"""Couchbase vector stores."""

from __future__ import annotations

import uuid
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
)

import couchbase.search as search
from couchbase.cluster import Cluster
from couchbase.exceptions import DocumentExistsException, DocumentNotFoundException
from couchbase.options import SearchOptions
from couchbase.vector_search import VectorQuery, VectorSearch
from langchain_core._api.deprecation import deprecated
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore


@deprecated(
    alternative_import="langchain_couchbase.vectorstores.CouchbaseSearchVectorStore",
    since="0.3.0",
    removal="1.0.0",
)
class CouchbaseVectorStore(VectorStore):
    """__Couchbase__ vector store integration.

    .. deprecated:: 0.1.0
        This class is deprecated and will be removed in version 1.0.0.
        Use :class:`CouchbaseSearchVectorStore` instead.

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
            from langchain_couchbase import CouchbaseVectorStore

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

            vector_store = CouchbaseVectorStore(
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

            * [SIM=0.500778] foo [{'baz': 'bar'}]

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

            * [SIM=0.500762] foo [{'baz': 'bar'}]

    Use as Retriever:
        .. code-block:: python

            retriever = vector_store.as_retriever(
                search_kwargs={"k": 1, "fetch_k": 2, "lambda_mult": 0.5},
            )
            retriever.invoke("thud")

        .. code-block:: python

            [Document(id='2', metadata={'bar': 'baz'}, page_content='thud')]

    """  # noqa: E501

    # Default batch size
    DEFAULT_BATCH_SIZE = 100
    _metadata_key = "metadata"
    _default_text_key = "text"
    _default_embedding_key = "embedding"

    def _check_bucket_exists(self) -> bool:
        """Check if the bucket exists in the linked Couchbase cluster"""
        bucket_manager = self._cluster.buckets()
        try:
            bucket_manager.get_bucket(self._bucket_name)
            return True
        except Exception:
            return False

    def _check_scope_and_collection_exists(self) -> bool:
        """Check if the scope and collection exists in the linked Couchbase bucket
        Raises a ValueError if either is not found"""
        scope_collection_map: Dict[str, Any] = {}

        # Get a list of all scopes in the bucket
        for scope in self._bucket.collections().get_all_scopes():
            scope_collection_map[scope.name] = []

            # Get a list of all the collections in the scope
            for collection in scope.collections:
                scope_collection_map[scope.name].append(collection.name)

        # Check if the scope exists
        if self._scope_name not in scope_collection_map.keys():
            raise ValueError(
                f"Scope {self._scope_name} not found in Couchbase "
                f"bucket {self._bucket_name}"
            )

        # Check if the collection exists in the scope
        if self._collection_name not in scope_collection_map[self._scope_name]:
            raise ValueError(
                f"Collection {self._collection_name} not found in scope "
                f"{self._scope_name} in Couchbase bucket {self._bucket_name}"
            )

        return True

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

    def __init__(
        self,
        cluster: Cluster,
        bucket_name: str,
        scope_name: str,
        collection_name: str,
        embedding: Embeddings,
        index_name: str,
        *,
        text_key: Optional[str] = _default_text_key,
        embedding_key: Optional[str] = _default_embedding_key,
        scoped_index: bool = True,
    ) -> None:
        """
        Initialize the Couchbase Vector Store.

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
        if not isinstance(cluster, Cluster):
            raise ValueError(
                f"cluster should be an instance of couchbase.Cluster, "
                f"got {type(cluster)}"
            )

        self._cluster = cluster

        if not embedding:
            raise ValueError("Embeddings instance must be provided.")

        if not bucket_name:
            raise ValueError("bucket_name must be provided.")

        if not scope_name:
            raise ValueError("scope_name must be provided.")

        if not collection_name:
            raise ValueError("collection_name must be provided.")

        if not index_name:
            raise ValueError("index_name must be provided.")

        self._bucket_name = bucket_name
        self._scope_name = scope_name
        self._collection_name = collection_name
        self._embedding_function = embedding
        self._text_key = text_key
        self._embedding_key = embedding_key
        self._index_name = index_name
        self._scoped_index = scoped_index

        # Check if the bucket exists
        if not self._check_bucket_exists():
            raise ValueError(
                f"Bucket {self._bucket_name} does not exist. "
                " Please create the bucket before searching."
            )

        try:
            self._bucket = self._cluster.bucket(self._bucket_name)
            self._scope = self._bucket.scope(self._scope_name)
            self._collection = self._scope.collection(self._collection_name)
        except Exception as e:
            raise ValueError(
                "Error connecting to couchbase. "
                "Please check the connection and credentials."
            ) from e

        # Check if the scope and collection exists. Throws ValueError if they don't
        try:
            self._check_scope_and_collection_exists()
        except Exception as e:
            raise e

        # Check if the index exists. Throws ValueError if it doesn't
        try:
            self._check_index_exists()
        except Exception as e:
            raise e

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Run texts through the embeddings and persist in vectorstore.

        If the document IDs are passed, the existing documents (if any) will be
        overwritten with the new ones.

        Args:
            texts (Iterable[str]): Iterable of strings to add to the vectorstore.
            metadatas (Optional[List[Dict]]): Optional list of metadatas associated
                with the texts.
            ids (Optional[List[str]]): Optional list of ids associated with the texts.
                IDs have to be unique strings across the collection.
                If it is not specified uuids are generated and used as ids.
            batch_size (Optional[int]): Optional batch size for bulk insertions.
                Default is 100.

        Returns:
            List[str]:List of ids from adding the texts into the vectorstore.
        """

        if not batch_size:
            batch_size = self.DEFAULT_BATCH_SIZE
        doc_ids: List[str] = []

        if ids is None:
            ids = [uuid.uuid4().hex for _ in texts]

        if metadatas is None:
            metadatas = [{} for _ in texts]

        # Check if TTL is provided
        ttl = kwargs.get("ttl", None)

        # Insert in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_metadatas = metadatas[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]
            batch_embedded_texts = self._embedding_function.embed_documents(batch_texts)

            batch_docs = {
                id: {
                    self._text_key: text,
                    self._metadata_key: metadata,
                    self._embedding_key: vector,
                }
                for id, text, metadata, vector in zip(
                    batch_ids, batch_texts, batch_metadatas, batch_embedded_texts
                )
            }

            try:
                # Insert with TTL if provided
                if ttl:
                    result = self._collection.upsert_multi(batch_docs, expiry=ttl)
                else:
                    result = self._collection.upsert_multi(batch_docs)
                if result.all_ok:
                    doc_ids.extend(batch_docs.keys())
                else:
                    raise ValueError("Failed to insert documents.", result.exceptions)
            except DocumentExistsException as e:
                raise ValueError(f"Document already exists: {e}")

        return doc_ids

    def delete(self, ids: Optional[List[str]] = None, **kwargs: Any) -> Optional[bool]:
        """Delete documents from the vector store by ids.

        Args:
            ids (List[str]): List of IDs of the documents to delete.
            batch_size (Optional[int]): Optional batch size for bulk deletions.

        Returns:
            bool: True if all the documents were deleted successfully, False otherwise.

        """

        if ids is None:
            raise ValueError("No document ids provided to delete.")

        batch_size = kwargs.get("batch_size", self.DEFAULT_BATCH_SIZE)
        deletion_status = True

        # Delete in batches
        for i in range(0, len(ids), batch_size):
            batch = ids[i : i + batch_size]
            try:
                result = self._collection.remove_multi(batch)
            except DocumentNotFoundException as e:
                deletion_status = False
                raise ValueError(f"Document not found: {e}")

            deletion_status &= result.all_ok

        return deletion_status

    @property
    def embeddings(self) -> Embeddings:
        """Return the query embedding object."""
        return self._embedding_function

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
        **kwargs: Any,
    ) -> List[Document]:
        """Return documents most similar to embedding vector with their scores.

        Args:
            query (str): Query to look up for similar documents
            k (int): Number of Documents to return.
                Defaults to 4.
            search_options (Optional[Dict[str, Any]]): Optional search options that are
                passed to Couchbase search.
                Defaults to empty dictionary
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                If nothing is specified, defaults to all the fields stored in the index.

        Returns:
            List of Documents most similar to the query.
        """
        query_embedding = self.embeddings.embed_query(query)
        docs_with_scores = self.similarity_search_with_score_by_vector(
            query_embedding, k, search_options, **kwargs
        )
        return [doc for doc, _ in docs_with_scores]

    def similarity_search_with_score_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        search_options: Optional[Dict[str, Any]] = {},
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return docs most similar to embedding vector with their scores.

        Args:
            embedding (List[float]): Embedding vector to look up documents similar to.
            k (int): Number of Documents to return.
                Defaults to 4.
            search_options (Optional[Dict[str, Any]]): Optional search options that are
                passed to Couchbase search.
                Defaults to empty dictionary.
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                If nothing is specified, defaults to all the fields stored in the index.

        Returns:
            List of (Document, score) that are the most similar to the query vector.
        """

        fields = kwargs.get("fields", ["*"])

        # Document text field needs to be returned from the search
        if fields != ["*"] and self._text_key not in fields:
            fields.append(self._text_key)

        search_req = search.SearchRequest.create(
            VectorSearch.from_vector_query(
                VectorQuery(
                    self._embedding_key,
                    embedding,
                    k,
                )
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
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return documents that are most similar to the query with their scores.

        Args:
            query (str): Query to look up for similar documents
            k (int): Number of Documents to return.
                Defaults to 4.
            search_options (Optional[Dict[str, Any]]): Optional search options that are
                passed to Couchbase search.
                Defaults to empty dictionary.
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                If nothing is specified, defaults to text and metadata fields.

        Returns:
            List of (Document, score) that are most similar to the query.
        """
        query_embedding = self.embeddings.embed_query(query)
        docs_with_score = self.similarity_search_with_score_by_vector(
            query_embedding, k, search_options, **kwargs
        )
        return docs_with_score

    def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        search_options: Optional[Dict[str, Any]] = {},
        **kwargs: Any,
    ) -> List[Document]:
        """Return documents that are most similar to the vector embedding.

        Args:
            embedding (List[float]): Embedding to look up documents similar to.
            k (int): Number of Documents to return.
                Defaults to 4.
            search_options (Optional[Dict[str, Any]]): Optional search options that are
                passed to Couchbase search.
                Defaults to empty dictionary.
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                If nothing is specified, defaults to document text and metadata fields.

        Returns:
            List of Documents most similar to the query.
        """
        docs_with_score = self.similarity_search_with_score_by_vector(
            embedding, k, search_options, **kwargs
        )
        return [doc for doc, _ in docs_with_score]

    @classmethod
    def _from_kwargs(
        cls: Type[CouchbaseVectorStore],
        embedding: Embeddings,
        **kwargs: Any,
    ) -> CouchbaseVectorStore:
        """Initialize the Couchbase vector store from keyword arguments for the
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
        cls: Type[CouchbaseVectorStore],
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> CouchbaseVectorStore:
        """Construct a Couchbase vector store from a list of texts.

        Example:
            .. code-block:: python

                from langchain_couchbase import CouchbaseVectorStore
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

                vectorstore = CouchbaseVectorStore.from_texts(
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
            **kwargs: Keyword arguments used to initialize the vector store with and/or
                passed to `add_texts` method. Check the constructor and/or `add_texts`
                for the list of accepted arguments.

        Returns:
            A Couchbase vector store.

        """
        vector_store = cls._from_kwargs(embedding, **kwargs)
        batch_size = kwargs.get("batch_size", vector_store.DEFAULT_BATCH_SIZE)
        ids = kwargs.get("ids", None)
        vector_store.add_texts(
            texts, metadatas=metadatas, ids=ids, batch_size=batch_size
        )

        return vector_store
