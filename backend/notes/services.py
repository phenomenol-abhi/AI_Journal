from ai.services import ingest_note, remove_note

from .models import Note


def sync_note_vectors(note):
    ingest_note(
        user_id=note.user_id,
        note_id=note.id,
        content=note.content,
        created_at=note.created_at.isoformat(),
    )


def delete_note_vectors(note_id):
    remove_note(note_id)


def delete_note(note):
    delete_note_vectors(note.id)
    note.delete()


def get_user_note(user, note_id):
    return Note.objects.get(id=note_id, user=user)
