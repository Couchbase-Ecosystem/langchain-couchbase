"""Base vector store for Couchbase."""

from __future__ import annotations

import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Optional,
    cast,
)

from couchbase.cluster import Cluster
from couchbase.exceptions import DocumentExistsException, DocumentNotFoundException
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from langchain_couchbase._collection import open_collection

if TYPE_CHECKING:
    from collections.abc import Iterable


class BaseCouchbaseVectorStore(VectorStore):
    """Base vector store for Couchbase.
    This class handles the data input and output for the vector store.
    This class is meant to be used as a base class for other vector stores.
    """

    # Default batch size
    DEFAULT_BATCH_SIZE = 100
    _metadata_key = "metadata"
    _default_text_key = "text"
    _default_embedding_key = "embedding"

    def __init__(
        self,
        cluster: Cluster,
        bucket_name: str,
        scope_name: str,
        collection_name: str,
        embedding: Embeddings,
        *,
        text_key: Optional[str] = _default_text_key,
        embedding_key: Optional[str] = _default_embedding_key,
    ) -> None:
        """
        Initialize the Couchbase Base Vector Store for data input and output.

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
        self._cluster = cluster

        if not embedding:
            raise ValueError("Embeddings instance must be provided.")

        if not bucket_name:
            raise ValueError("bucket_name must be provided.")

        if not scope_name:
            raise ValueError("scope_name must be provided.")

        if not collection_name:
            raise ValueError("collection_name must be provided.")

        self._bucket_name = bucket_name
        self._scope_name = scope_name
        self._collection_name = collection_name
        self._embedding_function = embedding
        self._text_key = cast(str, text_key)
        self._embedding_key = cast(str, embedding_key)

        handles = open_collection(cluster, bucket_name, scope_name, collection_name)
        self._bucket = handles.bucket
        self._scope = handles.scope
        self._collection = handles.collection

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

        texts = list(texts)

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
