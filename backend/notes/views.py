from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ai.services import remove_note
from .models import Note
from .serializers import NoteSerializer
from .services import delete_note, sync_note_vectors


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        note = serializer.save(user=self.request.user)
        sync_note_vectors(note)

    def perform_update(self, serializer):
        note = serializer.save()
        remove_note(note.id)
        sync_note_vectors(note)

    def perform_destroy(self, instance):
        delete_note(instance)
