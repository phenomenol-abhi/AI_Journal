from .chunking import chunk_text
from .clients import get_embed_client
from .vector_store import get_vector_store


def ingest_note(user_id, note_id, content, created_at):
    chunks = chunk_text(content)
    if not chunks:
        return
    vectors = get_embed_client().embed(chunks)
    store = get_vector_store()
    store.ensure_collection()
    store.upsert_chunks(user_id, note_id, chunks, vectors, created_at)


def remove_note(note_id):
    get_vector_store().delete_note(note_id)


def retrieve_context(user_id, question, limit=4):
    vector = get_embed_client().embed([question])[0]
    return get_vector_store().search(user_id, vector, limit=limit)
