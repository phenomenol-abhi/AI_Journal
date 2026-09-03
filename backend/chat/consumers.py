import asyncio
import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from ai.clients import get_chat_client
from ai.services import retrieve_context
from .memory import get_session_memory
from .prompts import build_messages

logger = logging.getLogger("chat.rag")

_SENTINEL = object()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close(code=4401)
            return
        self.user = user
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            payload = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "detail": "Invalid JSON"})
            return
        question = (payload.get("question") or "").strip()
        if payload.get("type") == "reset":
            from .memory import clear_session_memory

            clear_session_memory(self.user.id)
            await self.send_json({"type": "reset", "detail": "Conversation memory cleared"})
            return
        if not question:
            return
        asyncio.create_task(self.answer(question))

    async def answer(self, question):
        memory = get_session_memory(self.user.id)
        try:
            hits = await asyncio.to_thread(retrieve_context, self.user.id, question)
        except Exception as exc:
            logger.error("Retrieval failed for user %s: %s", self.user.id, exc)
            await self.send_json({"type": "error", "detail": f"Retrieval failed: {exc}"})
            return

        logger.info(
            "RAG retrieval user=%s question=%r hits=%d",
            self.user.id,
            question,
            len(hits),
        )
        sources = []
        for index, hit in enumerate(hits, start=1):
            logger.info(
                "  [%d] note=%s score=%.4f created_at=%s preview=%r",
                index,
                hit["note_id"],
                hit["score"],
                hit["created_at"],
                hit["text"][:80],
            )
            sources.append(
                {
                    "index": index,
                    "note_id": hit["note_id"],
                    "created_at": hit["created_at"],
                    "score": round(hit["score"], 4),
                    "snippet": hit["text"][:220],
                }
            )
        await self.send_json({"type": "sources", "sources": sources})

        chat_history = memory.load_memory_variables({}).get("chat_history")
        messages = build_messages(question, hits, chat_history)

        try:
            client = await asyncio.to_thread(get_chat_client)
            logger.info(
                "Generation starting provider=%s model=%s (history turns=%d)",
                client.name,
                client.chat_model,
                chat_history.count("Assistant:") if chat_history else 0,
            )
            stream = await asyncio.to_thread(client.chat, messages, True)
            parts = []
            while True:
                chunk = await asyncio.to_thread(next, stream, _SENTINEL)
                if chunk is _SENTINEL:
                    break
                content = getattr(chunk.choices[0].delta, "content", None)
                if content:
                    parts.append(content)
                    await self.send_json({"type": "token", "text": content})
            await asyncio.to_thread(
                memory.save_context, {"input": question}, {"output": "".join(parts)}
            )
        except Exception as exc:
            logger.error("Generation failed: %s", exc)
            await self.send_json({"type": "error", "detail": f"Generation failed: {exc}"})
            return

        await self.send_json({"type": "done"})

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))
