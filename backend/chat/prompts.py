SYSTEM_PROMPT = (
    "You are a personal journal assistant. Answer the user's question using ONLY the "
    "journal excerpts provided in the context. If the excerpts do not contain the answer, "
    "say that nothing in the journal covers it. Never invent facts. When you use information "
    "from an excerpt, cite it inline with its index marker, for example [1] or [2]."
)


def build_context_block(hits):
    if not hits:
        return "The user's journal is empty or has no relevant entries."
    blocks = []
    for index, hit in enumerate(hits, start=1):
        blocks.append(f"[{index}] {hit['created_at']}\n{hit['text']}")
    return "\n\n".join(blocks)


def build_messages(question, hits, chat_history=None):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if chat_history:
        messages.append(
            {
                "role": "system",
                "content": f"Conversation so far:\n{chat_history}\n"
                "Use it for follow-up references like 'that place' or 'she'.",
            }
        )
    messages.append(
        {
            "role": "user",
            "content": f"Journal context:\n{build_context_block(hits)}\n\nQuestion: {question}",
        }
    )
    return messages
