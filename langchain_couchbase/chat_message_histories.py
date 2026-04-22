"""Couchbase Chat Message History"""

import logging
import time
import uuid
from datetime import timedelta
from typing import List, Optional, Sequence

from couchbase.cluster import Cluster
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict,
)

from langchain_couchbase.utils import (
    check_bucket_exists,
    check_scope_and_collection_exists,
    validate_ttl,
)

logger = logging.getLogger(__name__)

DEFAULT_SESSION_ID_KEY = "session_id"
DEFAULT_MESSAGE_KEY = "message"
DEFAULT_TS_KEY = "ts"
DEFAULT_INDEX_NAME = "LANGCHAIN_CHAT_HISTORY"
DEFAULT_BATCH_SIZE = 100


class CouchbaseChatMessageHistory(BaseChatMessageHistory):
    """Couchbase Chat Message History
    Chat message history that uses Couchbase as the storage
    """

    def __init__(
        self,
        *,
        cluster: Cluster,
        bucket_name: str,
        scope_name: str,
        collection_name: str,
        session_id: str,
        session_id_key: str = DEFAULT_SESSION_ID_KEY,
        message_key: str = DEFAULT_MESSAGE_KEY,
        create_index: bool = True,
        ttl: Optional[timedelta] = None,
    ) -> None:
        """Initialize the Couchbase Chat Message History
        Args:
            cluster (Cluster): couchbase cluster object with active connection.
            bucket_name (str): name of the bucket to store documents in.
            scope_name (str): name of the scope in bucket to store documents in.
            collection_name (str): name of the collection in the scope to store
                documents in.
            session_id (str): value for the session used to associate messages from
                a single chat session. It is stored as a field in the chat message.
            session_id_key (str): name of the field to use for the session id.
                Set to "session_id" by default.
            message_key (str): name of the field to use for the messages
                Set to "message" by default.
            create_index (bool): create an index if True. Set to True by default.
            ttl (timedelta): time to live for the documents in the collection.
                When set, the documents are automatically deleted after the ttl expires.
        """
        if not isinstance(cluster, Cluster):
            raise ValueError(
                f"cluster should be an instance of couchbase.Cluster, "
                f"got {type(cluster)}"
            )

        self._cluster = cluster

        self._bucket_name = bucket_name
        self._scope_name = scope_name
        self._collection_name = collection_name
        self._ttl = None

        # Check if the bucket exists
        if not check_bucket_exists(cluster, bucket_name):
            raise ValueError(
                f"Bucket {bucket_name} does not exist. "
                "Please create the bucket before searching."
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
        check_scope_and_collection_exists(
            self._bucket, scope_name, collection_name, bucket_name
        )

        self._session_id_key = session_id_key
        self._message_key = message_key
        self._create_index = create_index
        self._session_id = session_id
        self._ts_key = DEFAULT_TS_KEY

        if ttl is not None:
            validate_ttl(ttl)
            self._ttl = ttl

        # Create an index if it does not exist if requested
        if create_index:
            index_fields = (
                f"({self._session_id_key}, {self._ts_key}, {self._message_key})"
            )
            index_creation_query = (
                f"CREATE INDEX {DEFAULT_INDEX_NAME} IF NOT EXISTS ON "
                + f"{self._collection_name}{index_fields} "
            )

            try:
                self._scope.query(index_creation_query).execute()
            except Exception:
                logger.exception("Error creating index")

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the cache"""
        # Generate a UUID for the document key
        document_key = uuid.uuid4().hex
        # get utc timestamp for ordering the messages
        timestamp = time.time()
        message_content = message_to_dict(message)

        try:
            if self._ttl:
                self._collection.insert(
                    document_key,
                    value={
                        self._message_key: message_content,
                        self._session_id_key: self._session_id,
                        self._ts_key: timestamp,
                    },
                    expiry=self._ttl,
                )
            else:
                self._collection.insert(
                    document_key,
                    value={
                        self._message_key: message_content,
                        self._session_id_key: self._session_id,
                        self._ts_key: timestamp,
                    },
                )
        except Exception:
            logger.exception("Error adding message")

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """Add messages to the cache in a batched manner"""
        batch_size = DEFAULT_BATCH_SIZE
        messages_to_insert = []
        for message in messages:
            document_key = uuid.uuid4().hex
            timestamp = time.time()
            message_content = message_to_dict(message)
            messages_to_insert.append(
                {
                    document_key: {
                        self._message_key: message_content,
                        self._session_id_key: self._session_id,
                        self._ts_key: timestamp,
                    },
                }
            )

        # Add the messages to the cache in batches of batch_size
        try:
            for i in range(0, len(messages_to_insert), batch_size):
                batch = messages_to_insert[i : i + batch_size]
                # Convert list of dictionaries to a single dictionary to insert
                insert_batch = {list(d.keys())[0]: list(d.values())[0] for d in batch}
                if self._ttl:
                    self._collection.insert_multi(insert_batch, expiry=self._ttl)
                else:
                    self._collection.insert_multi(insert_batch)
        except Exception:
            logger.exception("Error adding messages")

    def clear(self) -> None:
        """Clear the cache"""
        # Delete all documents in the collection with the session_id
        clear_query = (
            f"DELETE FROM `{self._collection_name}` "
            f"WHERE {self._session_id_key}=$session_id"
        )
        try:
            self._scope.query(clear_query, session_id=self._session_id).execute()
        except Exception:
            logger.exception("Error clearing cache")

    @property
    def messages(self) -> List[BaseMessage]:
        """Get all messages in the cache associated with the session_id"""
        fetch_query = (
            f"SELECT {self._message_key} FROM `{self._collection_name}` "
            + f"where {self._session_id_key}=$session_id"
            + f" ORDER BY {self._ts_key} ASC"
        )
        message_items = []

        try:
            result = self._scope.query(fetch_query, session_id=self._session_id)
            for document in result:
                message_items.append(document[f"{self._message_key}"])
        except Exception:
            logger.exception("Error fetching messages")

        return messages_from_dict(message_items)

    @messages.setter
    def messages(self, messages: List[BaseMessage]) -> None:
        raise NotImplementedError(
            "Direct assignment to 'messages' is not allowed."
            " Use the 'add_messages' instead."
        )
