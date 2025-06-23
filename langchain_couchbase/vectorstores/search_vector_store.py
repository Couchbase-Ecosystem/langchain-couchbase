from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Type

import couchbase.search as search
from couchbase.cluster import Cluster
from couchbase.options import SearchOptions
from couchbase.search import SearchQuery
from couchbase.vector_search import VectorQuery, VectorSearch
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from langchain_couchbase.vectorstores.base_vector_store import BaseCouchbaseVectorStore


class CouchbaseSearchVectorStore(BaseCouchbaseVectorStore):
    """__Couchbase__ vector store integration using Search/FTS service.

    Setup:
        Install ``langchain-couchbase`` and head over to the Couchbase [website](https://cloud.couchbase.com) and create a new connection, with a bucket, collection, and search index.

        .. code-block:: bash

            pip install -U langchain-couchbase

        .. code-block:: python

            import getpass

            COUCHBASE_CONNECTION_STRING = getpass.getpass("Enter the connection string for the Couchbase cluster: ")
            DB_USERNAME = getpass.getpass("Enter the username for the Couchbase cluster: ")
            DB_PASSWORD = getpass.getpass("Enter the password for the Couchbase cluster: ")

    Key init args — indexing params:
        embedding: Embeddings
            Embedding function to use.

    Key init args — client params:
        cluster: Cluster
            Couchbase cluster object with active connection.
        bucket_name: str
            Name of the bucket to store documents in.
        scope_name: str
            Name of the scope in the bucket to store documents in.
        collection_name: str
            Name of the collection in the scope to store documents in.
        index_name: str
            Name of the Search index to use.

    Instantiate:
        .. code-block:: python

            from datetime import timedelta
            from langchain_openai import OpenAIEmbeddings
            from couchbase.auth import PasswordAuthenticator
            from couchbase.cluster import Cluster
            from couchbase.options import ClusterOptions
            from langchain_couchbase import CouchbaseSearchVectorStore

            auth = PasswordAuthenticator(DB_USERNAME, DB_PASSWORD)
            options = ClusterOptions(auth)
            cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)

            # Wait until the cluster is ready for use.
            cluster.wait_until_ready(timedelta(seconds=5))

            BUCKET_NAME = "langchain_bucket"
            SCOPE_NAME = "_default"
            COLLECTION_NAME = "_default"
            SEARCH_INDEX_NAME = "langchain-test-index"

            embeddings = OpenAIEmbeddings()

            vector_store = CouchbaseSearchVectorStore(
                cluster=cluster,
                bucket_name=BUCKET_NAME,
                scope_name=SCOPE_NAME,
                collection_name=COLLECTION_NAME,
                embedding=embeddings,
                index_name=SEARCH_INDEX_NAME,
            )

    Add Documents:
        .. code-block:: python

            from langchain_core.documents import Document

            document_1 = Document(page_content="foo", metadata={"baz": "bar"})
            document_2 = Document(page_content="thud", metadata={"bar": "baz"})
            document_3 = Document(page_content="i will be deleted :(")

            documents = [document_1, document_2, document_3]
            ids = ["1", "2", "3"]
            vector_store.add_documents(documents=documents, ids=ids)

    Delete Documents:
        .. code-block:: python

            vector_store.delete(ids=["3"])

    Search:
        .. code-block:: python

            results = vector_store.similarity_search(query="thud",k=1)
            for doc in results:
                print(f"* {doc.page_content} [{doc.metadata}]")

        .. code-block:: python

            * thud [{'bar': 'baz'}]

    Search with filter:
        .. code-block:: python

            from couchbase.search import MatchQuery
            
            filter = MatchQuery("baz",field="metadata.bar")
            results = vector_store.similarity_search(query="thud",k=1,pre_filter=filter)
            for doc in results:
                print(f"* {doc.page_content} [{doc.metadata}]")

        .. code-block:: python
            
            * thud [{'bar': 'baz'}]

    Hybrid Search:
        .. code-block:: python

            results = vector_store.similarity_search(query="thud",k=1,search_options={"query": {"field":"metadata.bar", "match": "baz"}})
            for doc in results:
                print(f"* {doc.page_content} [{doc.metadata}]")

        .. code-block:: python

            * thud [{'bar': 'baz'}]

    Search with score:
        .. code-block:: python

            results = vector_store.similarity_search_with_score(query="qux",k=1)
            for doc, score in results:
                print(f"* [SIM={score:3f}] {doc.page_content} [{doc.metadata}]")

        .. code-block:: python

            * [SIM=0.500762] foo [{'baz': 'bar'}]

    Async:
        .. code-block:: python

            # add documents
            await vector_store.aadd_documents(documents=documents, ids=ids)

            # delete documents
            await vector_store.adelete(ids=["3"])

            # search
            results = vector_store.asimilarity_search(query="thud",k=1)

            # search with score
            results = await vector_store.asimilarity_search_with_score(query="qux",k=1)
            for doc,score in results:
                print(f"* [SIM={score:3f}] {doc.page_content} [{doc.metadata}]")

        .. code-block:: python

            * [SIM=0.500735] foo [{'baz': 'bar'}]

    Use as Retriever:
        .. code-block:: python

            retriever = vector_store.as_retriever(
                search_kwargs={"k": 1, "fetch_k": 2, "lambda_mult": 0.5},
            )
            retriever.invoke("thud")

        .. code-block:: python

            [Document(id='2', metadata={'bar': 'baz'}, page_content='thud')]
    """  # noqa: E501

    def _check_index_exists(self) -> bool:
        """Check if the Search index exists in the linked Couchbase cluster
        Raises a ValueError if the index does not exist"""
        if self._scoped_index:
            all_indexes = [
                index.name for index in self._scope.search_indexes().get_all_indexes()
            ]
            if self._index_name not in all_indexes:
                raise ValueError(
                    f"Index {self._index_name} does not exist. "
                    " Please create the index before searching."
                )
        else:
            all_indexes = [
                index.name for index in self._cluster.search_indexes().get_all_indexes()
            ]
            if self._index_name not in all_indexes:
                raise ValueError(
                    f"Index {self._index_name} does not exist. "
                    " Please create the index before searching."
                )

        return True
    
    def _check_pre_filter(self, pre_filter: SearchQuery) -> bool:
        """Check if the pre-filter is a valid SearchQuery object.
        Raises a ValueError if the pre-filter is not valid."""
        if isinstance(pre_filter, SearchQuery):
            return True
        raise ValueError(f"pre_filter must be a SearchQuery object, got"
                         f"{type(pre_filter)}")

    def __init__(
        self,
        cluster: Cluster,
        bucket_name: str,
        scope_name: str,
        collection_name: str,
        embedding: Embeddings,
        index_name: str,
        *,
        text_key: Optional[str] = BaseCouchbaseVectorStore._default_text_key,
        embedding_key: Optional[str] = BaseCouchbaseVectorStore._default_embedding_key,
        scoped_index: bool = True,
    ) -> None:
        """
        Initialize the Couchbase SearchVector Store.

        Args:

            cluster (Cluster): couchbase cluster object with active connection.
            bucket_name (str): name of bucket to store documents in.
            scope_name (str): name of scope in the bucket to store documents in.
            collection_name (str): name of collection in the scope to store documents in
            embedding (Embeddings): embedding function to use.
            index_name (str): name of the Search index to use.
            text_key (optional[str]): key in document to use as text.
                Set to text by default.
            embedding_key (optional[str]): key in document to use for the embeddings.
                Set to embedding by default.
            scoped_index (optional[bool]): specify whether the index is a scoped index.
                Set to True by default.
        """
        super().__init__(
            cluster=cluster,
            bucket_name=bucket_name,
            scope_name=scope_name,
            collection_name=collection_name,
            embedding=embedding,
            text_key=text_key,
            embedding_key=embedding_key,
        )

        if not index_name:
            raise ValueError("index_name must be provided.")

        self._index_name = index_name
        self._scoped_index = scoped_index

        # Check if the index exists. Throws ValueError if it doesn't
        try:
            self._check_index_exists()
        except Exception as e:
            raise e

    def _format_metadata(self, row_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to format the metadata from the Couchbase Search API.
        Args:
            row_fields (Dict[str, Any]): The fields to format.

        Returns:
            Dict[str, Any]: The formatted metadata.
        """
        metadata = {}
        for key, value in row_fields.items():
            # Couchbase Search returns the metadata key with a prefix
            # `metadata.` We remove it to get the original metadata key
            if key.startswith(self._metadata_key):
                new_key = key.split(self._metadata_key + ".")[-1]
                metadata[new_key] = value
            else:
                metadata[key] = value

        return metadata

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        search_options: Optional[Dict[str, Any]] = {},
        pre_filter: Optional[SearchQuery] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Return documents most similar to embedding vector with their scores.

        Args:
            query (str): Query to look up for similar documents
            k (int): Number of Documents to return.
                Defaults to 4.
            search_options (Optional[Dict[str, Any]]): Optional hybrid search options 
                that are passed to Couchbase search service. Used for combining vector 
                similarity with text-based search criteria. Examples:
                - {"query": {"field": "metadata.category", "match": "action"}}
                - {"query": {"field": "metadata.year", "min": 2020, "max": 2023}}
                Defaults to empty dictionary.
            pre_filter (Optional[SearchQuery]): Optional pre-filter to apply before 
                vector search execution. It reduces the search space. Examples:
                - NumericRangeQuery(field="year", min=2020, max=2023)
                - TermQuery("search_term",field="category")
                - ConjunctionQuery(query1, query2)
                Defaults to None.
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                If nothing is specified, defaults to all the fields stored in the index.

        Returns:
            List of Documents most similar to the query.
            
        Note:
            - Use search_options for hybrid search combining vector similarity with 
                other supported search queries
            - Use pre_filter for efficient pre-search filtering, especially with large 
                datasets
            - Both parameters can be used together for complex search scenarios

        """
        query_embedding = self.embeddings.embed_query(query)
        docs_with_scores = self.similarity_search_with_score_by_vector(
            query_embedding, k, search_options, pre_filter, **kwargs
        )
        return [doc for doc, _ in docs_with_scores]

    def similarity_search_with_score_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        search_options: Optional[Dict[str, Any]] = {},
        pre_filter: Optional[SearchQuery] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return docs most similar to embedding vector with their scores.

        Args:
            embedding (List[float]): Embedding vector to look up documents similar to.
            k (int): Number of Documents to return.
                Defaults to 4.
            search_options (Optional[Dict[str, Any]]): Optional hybrid search options 
                that are passed to Couchbase search service. Used for combining vector 
                similarity with text-based search criteria. Examples:
                - {"query": {"field": "metadata.category", "match": "action"}}
                - {"query": {"field": "metadata.year", "min": 2020, "max": 2023}}
                Defaults to empty dictionary.
            pre_filter (Optional[SearchQuery]): Optional pre-filter to apply before 
                vector search execution. It reduces the search space. Examples:
                - NumericRangeQuery(field="year", min=2020, max=2023)
                - TermQuery("search_term",field="category")
                - ConjunctionQuery(query1, query2)
                Defaults to None.
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                    If nothing is specified, defaults to all the fields stored in 
                    the index.
       

        Returns:
            List of (Document, score) that are the most similar to the query vector.
            
        Note:
            - Use search_options for hybrid search combining vector similarity with 
                other supported search queries
            - Use pre_filter for efficient pre-search filtering, especially with large 
                datasets
            - Both parameters can be used together for complex search scenarios
        """

        fields = kwargs.get("fields", ["*"])

        if pre_filter:
            try:
                self._check_pre_filter(pre_filter)
            except Exception as e:
                raise ValueError(f"Invalid pre-filter: {e}")

        # Document text field needs to be returned from the search
        if fields != ["*"] and self._text_key not in fields:
            fields.append(self._text_key)

        vector_query = VectorQuery(
            self._embedding_key,
            embedding,
            num_candidates=k,
            prefilter=pre_filter if pre_filter else None,
        )

        search_req = search.SearchRequest.create(
            VectorSearch.from_vector_query(
                vector_query
            )
        )

        try:
            if self._scoped_index:
                search_iter = self._scope.search(
                    self._index_name,
                    search_req,
                    SearchOptions(
                        limit=k,
                        fields=fields,
                        raw=search_options,
                    ),
                )

            else:
                search_iter = self._cluster.search(
                    self._index_name,
                    search_req,
                    SearchOptions(limit=k, fields=fields, raw=search_options),
                )

            docs_with_score = []

            # Parse the results
            for row in search_iter.rows():
                if row.fields:
                    text = row.fields.pop(self._text_key, "")
                    id = row.id

                    # Format the metadata from Couchbase
                    metadata = self._format_metadata(row.fields)

                    score = row.score
                    doc = Document(id=id, page_content=text, metadata=metadata)
                    docs_with_score.append((doc, score))
                else:
                    raise ValueError(
                        "Search results do not contain the fields from the document. "
                        "Please check if the Search index contains the required fields:"
                        f"{self._text_key}"
                    )
        except Exception as e:
            raise ValueError(f"Search failed with error: {e}")

        return docs_with_score

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        search_options: Optional[Dict[str, Any]] = {},
        pre_filter: Optional[SearchQuery] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return documents that are most similar to the query with their scores.

        Args:
            query (str): Query to look up for similar documents
            k (int): Number of Documents to return.
                Defaults to 4.
            search_options (Optional[Dict[str, Any]]): Optional hybrid search options 
                that are passed to Couchbase search service. Used for combining vector 
                similarity with text-based search criteria. Examples:
                - {"query": {"field": "metadata.category", "match": "action"}}
                - {"query": {"field": "metadata.year", "min": 2020, "max": 2023}}
                Defaults to empty dictionary.
            pre_filter (Optional[SearchQuery]): Optional pre-filter to apply before 
                vector search execution. It reduces the search space. Examples:
                - NumericRangeQuery(field="year", min=2020, max=2023)
                - TermQuery("search_term",field="category")
                - ConjunctionQuery(query1, query2)
                Defaults to None.
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                If nothing is specified, defaults to text and metadata fields.

        Returns:
            List of (Document, score) that are most similar to the query.
            
        Note:
            - Use search_options for hybrid search combining vector similarity with 
                other supported search queries
            - Use pre_filter for efficient pre-search filtering, especially with large 
                datasets
            - Both parameters can be used together for complex search scenarios
        """
        query_embedding = self.embeddings.embed_query(query)
        docs_with_score = self.similarity_search_with_score_by_vector(
            query_embedding, k, search_options, pre_filter, **kwargs
        )
        return docs_with_score

    def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        search_options: Optional[Dict[str, Any]] = {},
        pre_filter: Optional[SearchQuery] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Return documents that are most similar to the vector embedding.

        Args:
            embedding (List[float]): Embedding to look up documents similar to.
            k (int): Number of Documents to return.
                Defaults to 4.
            search_options (Optional[Dict[str, Any]]): Optional hybrid search options 
                that are passed to Couchbase search service. Used for combining vector 
                similarity with text-based search criteria. Examples:
                - {"query": {"field": "metadata.category", "match": "action"}}
                - {"query": {"field": "metadata.year", "min": 2020, "max": 2023}}
                Defaults to empty dictionary.
            pre_filter (Optional[SearchQuery]): Optional pre-filter to apply before 
                vector search execution. It reduces the search space. Examples:
                - NumericRangeQuery(field="year", min=2020, max=2023)
                - TermQuery("search_term",field="category")
                - ConjunctionQuery(query1, query2)
                Defaults to None.
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                If nothing is specified, defaults to document text and metadata fields.

        Returns:
            List of Documents most similar to the query.
            
        Note:
            - Use search_options for hybrid search combining vector similarity with 
                other supported search queries
            - Use pre_filter for efficient pre-search filtering, especially with large 
                datasets
            - Both parameters can be used together for complex search scenarios
        """
        docs_with_score = self.similarity_search_with_score_by_vector(
            embedding, k, search_options, pre_filter, **kwargs
        )
        return [doc for doc, _ in docs_with_score]

    @classmethod
    def _from_kwargs(
        cls: Type[CouchbaseSearchVectorStore],
        embedding: Embeddings,
        **kwargs: Any,
    ) -> CouchbaseSearchVectorStore:
        """Initialize the Couchbase Searchvector store from keyword arguments for the 
        vector store.

        Args:
            embedding: Embedding object to use to embed text.
            **kwargs: Keyword arguments to initialize the vector store with.
                Accepted arguments are:
                    - cluster
                    - bucket_name
                    - scope_name
                    - collection_name
                    - index_name
                    - text_key
                    - embedding_key
                    - scoped_index

        """
        cluster = kwargs.get("cluster", None)
        bucket_name = kwargs.get("bucket_name", None)
        scope_name = kwargs.get("scope_name", None)
        collection_name = kwargs.get("collection_name", None)
        index_name = kwargs.get("index_name", None)
        text_key = kwargs.get("text_key", cls._default_text_key)
        embedding_key = kwargs.get("embedding_key", cls._default_embedding_key)
        scoped_index = kwargs.get("scoped_index", True)

        return cls(
            embedding=embedding,
            cluster=cluster,
            bucket_name=bucket_name,
            scope_name=scope_name,
            collection_name=collection_name,
            index_name=index_name,
            text_key=text_key,
            embedding_key=embedding_key,
            scoped_index=scoped_index,
        )

    @classmethod
    def from_texts(
        cls: Type[CouchbaseSearchVectorStore],
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> CouchbaseSearchVectorStore:
        """Construct a Couchbase vector store from a list of texts.

        Example:
            .. code-block:: python

            from langchain_couchbase import CouchbaseSearchVectorStore
            from langchain_openai import OpenAIEmbeddings

            from couchbase.cluster import Cluster
            from couchbase.auth import PasswordAuthenticator
            from couchbase.options import ClusterOptions
            from datetime import timedelta

            auth = PasswordAuthenticator(username, password)
            options = ClusterOptions(auth)
            connect_string = "couchbases://localhost"
            cluster = Cluster(connect_string, options)

            # Wait until the cluster is ready for use.
            cluster.wait_until_ready(timedelta(seconds=5))

            embeddings = OpenAIEmbeddings()

            texts = ["hello", "world"]

            vectorstore = CouchbaseSearchVectorStore.from_texts(
                texts,
                embedding=embeddings,
                cluster=cluster,
                bucket_name="",
                scope_name="",
                collection_name="",
                index_name="vector-index",
            )

        Args:
            texts (List[str]): list of texts to add to the vector store.
            embedding (Embeddings): embedding function to use.
            metadatas (optional[List[Dict]): list of metadatas to add to documents.
            **kwargs: Keyword arguments used to initialize the vector store 
                with and/or passed to `add_texts` method. Check the constructor and/or
                `add_texts` for the list of accepted arguments.

        Returns:
            A Couchbase Searchvector store.

        """
        vector_store = cls._from_kwargs(embedding, **kwargs)
        batch_size = kwargs.get("batch_size", vector_store.DEFAULT_BATCH_SIZE)
        ids = kwargs.get("ids", None)
        vector_store.add_texts(
            texts, metadatas=metadatas, ids=ids, batch_size=batch_size
        )

        return vector_store
