import threading

from langchain.memory import ConversationBufferMemory

_memories = {}
_lock = threading.Lock()


def get_session_memory(user_id):
    with _lock:
        if user_id not in _memories:
            _memories[user_id] = ConversationBufferMemory(
                memory_key="chat_history",
                human_prefix="User",
                ai_prefix="Assistant",
                return_messages=False,
            )
        return _memories[user_id]


def clear_session_memory(user_id):
    with _lock:
        _memories.pop(user_id, None)
