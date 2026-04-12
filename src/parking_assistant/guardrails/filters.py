import re

from langchain_core.messages import AIMessage

PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b\d{9}\b"),
    re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
]

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?above\s+instructions", re.IGNORECASE),
    re.compile(r"(show|reveal|print|display)\s+(me\s+)?(the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?prior", re.IGNORECASE),
    re.compile(r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions", re.IGNORECASE),
]

BLOCKED_RESPONSE = "I can only help with parking-related questions and reservations."


def check_input(text: str) -> tuple[bool, str]:
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            return False, BLOCKED_RESPONSE
    return True, text


def check_output(text: str) -> str:
    result = text
    for pattern in PII_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


def guardrails_input_node(state: dict) -> dict:
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_message = messages[-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)

    is_safe, response = check_input(user_text)
    if not is_safe:
        return {"messages": [AIMessage(content=response)], "blocked": True}

    return {"blocked": False}


def guardrails_output_node(state: dict) -> dict:
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_message = messages[-1]
    if hasattr(last_message, "content"):
        sanitized = check_output(last_message.content)
        if sanitized != last_message.content:
            return {"messages": [AIMessage(content=sanitized)]}

    return {}
