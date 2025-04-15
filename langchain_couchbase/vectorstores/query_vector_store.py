from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Tuple, Type

from couchbase.cluster import Cluster
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from langchain_couchbase.vectorstores.base_vector_store import BaseCouchbaseVectorStore


class DistanceStrategy(Enum):
    """
    Distance strategy for the similarity search.
    """

    DOT = "dot"
    L2 = "l2"
    EUCLIDEAN = "euclidean"
    COSINE = "cosine"
    L2_SQUARED = "l2_squared"
    EUCLIDEAN_SQUARED = "euclidean_squared"


class IndexType(Enum):
    """
    Type of the Query index to create.
    """

    COMPOSITE = "composite"
    BHIVE = "bhive"


class CouchbaseQueryVectorStore(BaseCouchbaseVectorStore):
    """__Couchbase__ vector store integration using Query and Index service.

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
            from langchain_couchbase.vectorstores import DistanceStrategy

            auth = PasswordAuthenticator(DB_USERNAME, DB_PASSWORD)
            options = ClusterOptions(auth)
            cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)

            # Wait until the cluster is ready for use.
            cluster.wait_until_ready(timedelta(seconds=5))

            BUCKET_NAME = "langchain_bucket"
            SCOPE_NAME = "_default"
            COLLECTION_NAME = "_default"

            embeddings = OpenAIEmbeddings()

            vector_store = CouchbaseQueryVectorStore(
                cluster=cluster,
                bucket_name=BUCKET_NAME,
                scope_name=SCOPE_NAME,
                collection_name=COLLECTION_NAME,
                embedding=embeddings,
                distance_metric=DistanceStrategy.DOT,
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

            results = vector_store.similarity_search(query="thud",k=1, where_str="metadata.bar = 'baz'")
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

            * [SIM=-0.832155] foo [{'baz': 'bar'}]

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

            * [SIM=-0.832155] foo [{'baz': 'bar'}]

    Use as Retriever:
        .. code-block:: python

            retriever = vector_store.as_retriever(
                search_kwargs={"k": 1, "fetch_k": 2, "lambda_mult": 0.5},
            )
            retriever.invoke("thud")

        .. code-block:: python

            [Document(id='2', metadata={'bar': 'baz'}, page_content='thud')]
    """  # noqa: E501

    def __init__(
        self,
        cluster: Cluster,
        bucket_name: str,
        scope_name: str,
        collection_name: str,
        embedding: Embeddings,
        distance_metric: DistanceStrategy,
        *,
        text_key: Optional[str] = BaseCouchbaseVectorStore._default_text_key,
        embedding_key: Optional[str] = BaseCouchbaseVectorStore._default_embedding_key,
    ):
        super().__init__(
            cluster=cluster,
            bucket_name=bucket_name,
            scope_name=scope_name,
            collection_name=collection_name,
            embedding=embedding,
            text_key=text_key,
            embedding_key=embedding_key,
        )
        self._distance_metric = distance_metric

        # Create a primary index on the collection if it does not exist
        try:
            self._scope.query(
                f"CREATE PRIMARY INDEX IF NOT EXISTS ON {self._collection_name}"
            ).execute()
        except Exception as e:
            raise ValueError(f"Primary index creation failed with error: {e}")

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        where_str: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Return documents most similar to the query.

        Args:
            query (str): Query to look up for similar documents
            k (int): Number of Documents to return.
                Defaults to 4.
            where_str (Optional[str]): Optional where clause to filter the documents.
                Defaults to None.
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                If nothing is specified, defaults to all the fields stored in the index.

        Returns:
            List of Documents most similar to the query.
        """
        query_embedding = self.embeddings.embed_query(query)
        docs_with_scores = self.similarity_search_with_score_by_vector(
            query_embedding, k, where_str, **kwargs
        )
        return [doc for doc, _ in docs_with_scores]

    def similarity_search_with_score_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        where_str: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return docs most similar to embedding vector with their distances. Lower
        distances are more similar.

        Args:
            embedding (List[float]): Embedding vector to look up documents similar to.
            k (int): Number of Documents to return.
                Defaults to 4.
            where_str (Optional[str]): Optional where clause to filter the documents.
                Defaults to None.
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                If nothing is specified, defaults to all the fields stored in the index.

        Returns:
            List of (Document, distance) that are the most similar to the query vector.
            Lower distances are more similar.
        """

        fields = kwargs.get("fields", [f"{self._text_key}", f"{self._metadata_key}"])

        # Document text field needs to be returned from the search
        if self._text_key not in fields:
            fields.append(self._text_key)

        similarity_search_string = (
            f"ANN({self._embedding_key}, {embedding}, '{self._distance_metric.value}')"
        )

        if not where_str:
            search_query = (
                f"SELECT META().id, {','.join(fields)}, "
                f"{similarity_search_string} as distance "
                f"FROM {self._collection_name} "
                f"ORDER BY distance LIMIT {k}"
            )
        else:
            search_query = (
                f"SELECT META().id, {','.join(fields)}, "
                f"{similarity_search_string} as distance "
                f"FROM {self._collection_name} "
                f"WHERE {where_str} "
                f"ORDER BY distance LIMIT {k}"
            )

        try:
            search_iter = self._scope.query(search_query)

            docs_with_score = []

            # Parse the results
            for row in search_iter.rows():
                text = row.pop(self._text_key)
                id = row.pop("id", "")
                distance = row.pop("distance", 0)
                metadata = {}

                # Format the remaining fields as metadata
                if self._metadata_key in row:
                    metadata = row.pop(self._metadata_key)
                else:
                    metadata = row

                doc = Document(id=id, page_content=text, metadata=metadata)
                docs_with_score.append((doc, distance))

        except Exception as e:
            raise ValueError(f"Search failed with error: {e}")

        return docs_with_score

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        where_str: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return documents that are most similar to the query with their distances.
        Lower distances are more similar.

        Args:
            query (str): Query to look up for similar documents
            k (int): Number of Documents to return.
                Defaults to 4.
            where_str (Optional[str]): Optional where clause to filter the documents.
                Defaults to None.
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                If nothing is specified, defaults to text and metadata fields.

        Returns:
            List of (Document, distance) that are most similar to the query. Lower
            distances are more similar.
        """
        query_embedding = self.embeddings.embed_query(query)
        docs_with_score = self.similarity_search_with_score_by_vector(
            query_embedding, k, where_str, **kwargs
        )
        return docs_with_score

    def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        where_str: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Return documents that are most similar to the vector embedding.

        Args:
            embedding (List[float]): Embedding to look up documents similar to.
            k (int): Number of Documents to return.
                Defaults to 4.
            where_str (Optional[str]): Optional where clause to filter the documents.
                Defaults to None.
            fields (Optional[List[str]]): Optional list of fields to include in the
                metadata of results. Note that these need to be stored in the index.
                If nothing is specified, defaults to document text and metadata fields.

        Returns:
            List of Documents most similar to the query.
        """
        docs_with_score = self.similarity_search_with_score_by_vector(
            embedding, k, where_str, **kwargs
        )
        return [doc for doc, _ in docs_with_score]

    def create_index(
        self,
        index_type: IndexType,
        index_description: str,
        distance_metric: Optional[DistanceStrategy] = None,
        index_name: Optional[str] = None,
        vector_field: Optional[str] = None,
        vector_dimension: Optional[int] = None,
        fields: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        index_scan_nprobes: Optional[int] = None,
        index_trainlist: Optional[int] = None,
    ):
        """Create a new index for the Query vector store.

        Args:
            index_type (IndexType): Type of the index (BHIVE or COMPOSITE) to create.
            index_description (str): Description of the index like "IVF,SQ8".
            distance_metric (Optional[DistanceStrategy]): Distance metric to use for the
                index. Defaults to the distance metric in the constructor.
            index_name (str): Name of the index to create.
                Defaults to "langchain_{index_type}_query_index".
            vector_field (str): Name of the vector field to use for the index.
                Defaults to the embedding key in the constructor.
            vector_dimension (Optional[int]): Dimension of the vector field.
                If not provided, it will be determined from the embedding object.
            fields (List[str]): List of fields to include in the index.
                Defaults to the text field in the constructor.
            where_clause (Optional[str]): Optional where clause to filter the documents
                to index.
                Defaults to None.
            index_scan_nprobes (Optional[int]): Number of probes to use for the index.
                Defaults to None.
            index_trainlist (Optional[int]): Number of training samples to use for the
                index. Defaults to None.
        """
        if not isinstance(index_type, IndexType):
            raise ValueError(
                f"Invalid index type. Got {type(index_type)}. Expected {IndexType}"
            )

        similarity_metric = distance_metric or self._distance_metric

        if not index_description:
            raise ValueError(
                "Index description is required for creating Vector Query index."
            )

        # Get the vector field for the index
        vector_field = vector_field or self._embedding_key

        # Get the vector dimension for the index
        if not vector_dimension:
            try:
                vector_dimension = len(
                    self.embeddings.embed_query(
                        "check the size of the vector embeddings"
                    )
                )
            except Exception as e:
                raise ValueError(
                    "Vector dimension is required for creating Query index. "
                    f"Unable to determine the dimension from the embedding object. "
                    f"Error: {e}"
                )

        # Create the index parameters for the index creation query
        index_params = {}
        index_params["dimension"] = vector_dimension
        index_params["similarity"] = similarity_metric.value
        index_params["description"] = index_description
        if index_scan_nprobes:
            index_params["scan_nprobes"] = index_scan_nprobes
        if index_trainlist:
            index_params["train_list"] = index_trainlist

        # Add the text field to the fields if empty or if it is not present
        if not fields:
            fields = [self._text_key]
        else:
            if self._text_key not in fields:
                fields.append(self._text_key)

        # If where clause is provided, add it to the index creation query
        if where_clause:
            where_clause = f"WHERE {where_clause}"
        else:
            where_clause = ""

        if index_type == IndexType.BHIVE:
            if not index_name:
                index_name = "langchain_bhive_query_index"
            try:
                INDEX_CREATE_QUERY = (
                    f"CREATE VECTOR INDEX {index_name} ON {self._collection_name} "
                    f"({vector_field} VECTOR) INCLUDE ({', '.join(fields)}) "
                    f"{where_clause} USING GSI WITH {index_params}"
                )
                self._scope.query(INDEX_CREATE_QUERY).execute()
            except Exception as e:
                raise ValueError(f"Index creation failed with error: {e}")

        elif index_type == IndexType.COMPOSITE:
            if not index_name:
                index_name = "langchain_composite_query_index"

            try:
                INDEX_CREATE_QUERY = (
                    f"CREATE INDEX {index_name} ON {self._collection_name} "
                    f"({vector_field} VECTOR, {', '.join(fields)}) "
                    f"{where_clause} "
                    f"USING GSI WITH {index_params}"
                )
                self._scope.query(INDEX_CREATE_QUERY).execute()
            except Exception as e:
                raise ValueError(f"Index creation failed with error: {e}")

    @classmethod
    def _from_kwargs(
        cls: Type[CouchbaseQueryVectorStore],
        embedding: Embeddings,
        **kwargs: Any,
    ) -> CouchbaseQueryVectorStore:
        """Initialize the Couchbase Query vector store from keyword arguments for the
        vector store.

        Args:
            embedding: Embedding object to use to embed text.
            **kwargs: Keyword arguments to initialize the vector store with.
                Accepted arguments are:
                    - cluster
                    - bucket_name
                    - scope_name
                    - collection_name
                    - distance_metric
                    - text_key
                    - embedding_key

        """
        cluster = kwargs.get("cluster", None)
        bucket_name = kwargs.get("bucket_name", None)
        scope_name = kwargs.get("scope_name", None)
        collection_name = kwargs.get("collection_name", None)
        text_key = kwargs.get("text_key", cls._default_text_key)
        distance_metric = kwargs.get("distance_metric", None)
        embedding_key = kwargs.get("embedding_key", cls._default_embedding_key)

        return cls(
            embedding=embedding,
            cluster=cluster,
            bucket_name=bucket_name,
            scope_name=scope_name,
            collection_name=collection_name,
            distance_metric=distance_metric,
            text_key=text_key,
            embedding_key=embedding_key,
        )

    @classmethod
    def from_texts(
        cls: Type[CouchbaseQueryVectorStore],
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> CouchbaseQueryVectorStore:
        """Construct a Couchbase Query vector store from a list of texts.

        Example:
            .. code-block:: python

            from langchain_couchbase import CouchbaseQueryVectorStore
            from langchain_couchbase.vectorstores import DistanceStrategy
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

            vectorstore = CouchbaseQueryVectorStore.from_texts(
                texts,
                embedding=embeddings,
                cluster=cluster,
                bucket_name="",
                scope_name="",
                collection_name="",
                distance_metric=DistanceStrategy.COSINE,
            )

        Args:
            texts (List[str]): list of texts to add to the vector store.
            embedding (Embeddings): embedding function to use.
            metadatas (optional[List[Dict]): list of metadatas to add to documents.
            **kwargs: Keyword arguments used to initialize the vector store with and/or
                passed to `add_texts` method. Check the constructor and/or `add_texts`
                for the list of accepted arguments.

        Returns:
            A Couchbase Query vector store.

        """
        vector_store = cls._from_kwargs(embedding, **kwargs)
        batch_size = kwargs.get("batch_size", vector_store.DEFAULT_BATCH_SIZE)
        ids = kwargs.get("ids", None)
        vector_store.add_texts(
            texts, metadatas=metadatas, ids=ids, batch_size=batch_size
        )

        return vector_store
