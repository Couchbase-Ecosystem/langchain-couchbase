"""
LangChain Couchbase Caches

Functions "_hash", "_loads_generations" and "_dumps_generations"
are copied from the LangChain community module:

    "libs/community/langchain_community/cache.py"
"""

import hashlib
import json
import logging
from datetime import timedelta
from typing import Any, Dict, Optional, Union

from couchbase.cluster import Cluster
from couchbase.search import MatchQuery
from langchain_core.caches import RETURN_VAL_TYPE, BaseCache
from langchain_core.embeddings import Embeddings
from langchain_core.load.dump import dumps
from langchain_core.load.load import loads
from langchain_core.outputs import Generation

from langchain_couchbase._collection import open_collection
from langchain_couchbase.vectorstores import CouchbaseSearchVectorStore

logger = logging.getLogger(__file__)


def _hash(_input: str) -> str:
    """Use a deterministic hashing approach."""
    return hashlib.md5(_input.encode()).hexdigest()


def _dumps_generations(generations: RETURN_VAL_TYPE) -> str:
    """
    Serialization for generic RETURN_VAL_TYPE, i.e. sequence of `Generation`

    Args:
        generations (RETURN_VAL_TYPE): A list of language model generations.

    Returns:
        str: a single string representing a list of generations.

    This function (+ its counterpart `_loads_generations`) rely on
    the dumps/loads pair with Reviver, so are able to deal
    with all subclasses of Generation.

    Each item in the list can be `dumps`ed to a string,
    then we make the whole list of strings into a json-dumped.
    """
    return json.dumps([dumps(_item) for _item in generations])


def _loads_generations(generations_str: str) -> Union[RETURN_VAL_TYPE, None]:
    """
    Deserialization of a string into a generic RETURN_VAL_TYPE
    (i.e. a sequence of `Generation`).

    See `_dumps_generations`, the inverse of this function.

    Args:
        generations_str (str): A string representing a list of generations.

    Compatible with the legacy cache-blob format
    Does not raise exceptions for malformed entries, just logs a warning
    and returns none: the caller should be prepared for such a cache miss.

    Returns:
        RETURN_VAL_TYPE: A list of generations.
    """
    try:
        generations = [loads(_item_str) for _item_str in json.loads(generations_str)]
        return generations
    except (json.JSONDecodeError, TypeError):
        # deferring the (soft) handling to after the legacy-format attempt
        pass

    try:
        gen_dicts = json.loads(generations_str)
        # not relying on `_load_generations_from_json` (which could disappear):
        generations = [Generation(**generation_dict) for generation_dict in gen_dicts]
        logger.warning(
            f"Legacy 'Generation' cached blob encountered: '{generations_str}'"
        )
        return generations
    except (json.JSONDecodeError, TypeError):
        logger.warning(
            f"Malformed/unparsable cached blob encountered: '{generations_str}'"
        )
        return None


def _validate_ttl(ttl: Optional[timedelta]) -> None:
    """Validate the time to live"""
    if not isinstance(ttl, timedelta):
        raise ValueError(f"ttl should be of type timedelta but was {type(ttl)}.")
    if ttl <= timedelta(seconds=0):
        raise ValueError(
            f"ttl must be greater than 0 but was {ttl.total_seconds()} seconds."
        )


class CouchbaseCache(BaseCache):
    """Couchbase LLM Cache
    LLM Cache that uses Couchbase as the backend
    """

    PROMPT = "prompt"
    LLM = "llm"
    RETURN_VAL = "return_val"

    def __init__(
        self,
        cluster: Cluster,
        bucket_name: str,
        scope_name: str,
        collection_name: str,
        ttl: Optional[timedelta] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        """Initialize the Couchbase LLM Cache
        Args:
            cluster (Cluster): couchbase cluster object with active connection.
            bucket_name (str): name of the bucket to store documents in.
            scope_name (str): name of the scope in bucket to store documents in.
            collection_name (str): name of the collection in the scope to store
                documents in.
            ttl (Optional[timedelta]): TTL or time for the document to live in the cache
                After this time, the document will get deleted from the cache.
        """
        self._cluster = cluster

        self._bucket_name = bucket_name
        self._scope_name = scope_name
        self._collection_name = collection_name

        self._ttl = None

        handles = open_collection(cluster, bucket_name, scope_name, collection_name)
        self._bucket = handles.bucket
        self._scope = handles.scope
        self._collection = handles.collection

        # Check if the time to live is provided and valid
        if ttl is not None:
            _validate_ttl(ttl)
            self._ttl = ttl

    def lookup(self, prompt: str, llm_string: str) -> Optional[RETURN_VAL_TYPE]:
        """Look up from cache based on prompt and llm_string."""
        try:
            doc = self._collection.get(
                self._generate_key(prompt, llm_string)
            ).content_as[dict]
            return _loads_generations(doc[self.RETURN_VAL])
        except Exception:
            return None

    def _generate_key(self, prompt: str, llm_string: str) -> str:
        """Generate the key based on prompt and llm_string."""
        return _hash(prompt + llm_string)

    def update(self, prompt: str, llm_string: str, return_val: RETURN_VAL_TYPE) -> None:
        """Update cache based on prompt and llm_string."""
        doc = {
            self.PROMPT: prompt,
            self.LLM: llm_string,
            self.RETURN_VAL: _dumps_generations(return_val),
        }
        document_key = self._generate_key(prompt, llm_string)
        try:
            if self._ttl:
                self._collection.upsert(
                    key=document_key,
                    value=doc,
                    expiry=self._ttl,
                )
            else:
                self._collection.upsert(key=document_key, value=doc)
        except Exception:
            logger.error("Error updating cache")

    def clear(self, **kwargs: Any) -> None:
        """Clear the cache.
        This will delete all documents in the collection. This requires an index on the
        collection.
        """
        try:
            query = f"DELETE FROM `{self._collection_name}`"
            self._scope.query(query).execute()
        except Exception:
            logger.error("Error clearing cache. Please check if you have an index.")


class CouchbaseSemanticCache(BaseCache, CouchbaseSearchVectorStore):
    """Couchbase Semantic Cache
    Cache backed by a Couchbase Server with Vector Store support
    """

    LLM = "llm_string"
    RETURN_VAL = "return_val"

    def __init__(
        self,
        cluster: Cluster,
        embedding: Embeddings,
        bucket_name: str,
        scope_name: str,
        collection_name: str,
        index_name: str,
        score_threshold: Optional[float] = None,
        ttl: Optional[timedelta] = None,
    ) -> None:
        """Initialize the Couchbase LLM Cache
        Args:
            cluster (Cluster): couchbase cluster object with active connection.
            embedding (Embeddings): embedding model to use.
            bucket_name (str): name of the bucket to store documents in.
            scope_name (str): name of the scope in bucket to store documents in.
            collection_name (str): name of the collection in the scope to store
                documents in.
            index_name (str): name of the Search index to use.
            score_threshold (float): score threshold to use for filtering results.
            ttl (Optional[timedelta]): TTL or time for the document to live in the cache
                After this time, the document will get deleted from the cache.
        """
        self._ttl = None
        self.score_threshold = score_threshold

        if ttl is not None:
            _validate_ttl(ttl)
            self._ttl = ttl

        # Initialize the vector store; it opens and validates the collection
        super().__init__(
            cluster=cluster,
            bucket_name=bucket_name,
            scope_name=scope_name,
            collection_name=collection_name,
            embedding=embedding,
            index_name=index_name,
        )

    def lookup(self, prompt: str, llm_string: str) -> Optional[RETURN_VAL_TYPE]:
        """Look up from cache based on the semantic similarity of the prompt"""
        pre_filter = MatchQuery(llm_string, field=f"metadata.{self.LLM}")
        search_results = self.similarity_search_with_score(
            prompt, k=1, pre_filter=pre_filter
        )
        if search_results:
            selected_doc, score = search_results[0]
        else:
            return None

        # Check if the score is above the threshold if a threshold is provided
        if self.score_threshold:
            if score < self.score_threshold:
                return None

        return _loads_generations(selected_doc.metadata[self.RETURN_VAL])

    def update(self, prompt: str, llm_string: str, return_val: RETURN_VAL_TYPE) -> None:
        """Update cache based on the prompt and llm_string"""
        try:
            self.add_texts(
                texts=[prompt],
                metadatas=[
                    {
                        self.LLM: llm_string,
                        self.RETURN_VAL: _dumps_generations(return_val),
                    }
                ],
                ttl=self._ttl,
            )
        except Exception:
            logger.error("Error updating cache")

    def clear(self, **kwargs: Any) -> None:
        """Clear the cache.
        This will delete all documents in the collection.
        This requires an index on the collection.
        """
        try:
            query = f"DELETE FROM `{self._collection_name}`"
            self._scope.query(query).execute()
        except Exception:
            logger.error("Error clearing cache. Please check if you have an index.")
