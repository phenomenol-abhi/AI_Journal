import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)


class VectorStoreError(Exception):
    pass


class VectorStore:
    def __init__(self):
        url = os.getenv("QDRANT_URL")
        if not url:
            raise VectorStoreError("QDRANT_URL is not configured")
        self.client = QdrantClient(
            url=url,
            api_key=os.getenv("QDRANT_API_KEY") or None,
            timeout=30,
        )
        self.collection = os.getenv("QDRANT_COLLECTION", "journal_notes")
        self.dimension = int(os.getenv("EMBEDDING_DIMENSION", "768"))

    def ensure_collection(self):
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
            )
        for field in ("user_id", "note_id"):
            self.client.create_payload_index(
                collection_name=self.collection,
                field_name=field,
                field_schema="keyword",
            )

    @staticmethod
    def _point_id(note_id, chunk_index):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"note:{note_id}:chunk:{chunk_index}"))

    def upsert_chunks(self, user_id, note_id, chunks, vectors, created_at):
        points = [
            PointStruct(
                id=self._point_id(note_id, index),
                vector=vector,
                payload={
                    "user_id": str(user_id),
                    "note_id": str(note_id),
                    "chunk_index": index,
                    "text": text,
                    "created_at": created_at,
                },
            )
            for index, (text, vector) in enumerate(zip(chunks, vectors))
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def delete_note(self, note_id):
        self.client.delete(
            collection_name=self.collection,
            points_selector=Filter(
                must=[FieldCondition(key="note_id", match=MatchValue(value=str(note_id)))]
            ),
        )

    def search(self, user_id, query_vector, limit=4):
        self.ensure_collection()
        result = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=limit,
            with_payload=True,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]
            ),
        )
        hits = []
        for point in result.points:
            payload = point.payload
            hits.append(
                {
                    "note_id": payload.get("note_id"),
                    "text": payload.get("text", ""),
                    "created_at": payload.get("created_at", ""),
                    "score": point.score,
                }
            )
        return hits


_store = None


def get_vector_store():
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
