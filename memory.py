"""
memory.py — Persistent user memory
Stores what the user tells us across conversations.
Uses both rule-based and LLM-based fact extraction.
"""

import json
import os
from groq import Groq

MEMORY_FILE = "memory.json"
client      = Groq(api_key=os.environ.get("GROQ_API_KEY"))
FAST_MODEL  = "llama-3.1-8b-instant"


# ─────────────────────────────────────────
# LOAD / SAVE
# ─────────────────────────────────────────
def load_memory() -> dict:
    """Load saved memory from disk."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            pass
    return {}


def save_memory(memory: dict) -> None:
    """Save memory to disk."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=4)
    except Exception as e:
        print(f"Memory save error: {e}")


# ─────────────────────────────────────────
# LLM FACT EXTRACTION
# ─────────────────────────────────────────
def extract_facts_llm(text: str) -> dict:
    """
    Use LLM to extract personal facts from user message.
    Returns a dict of key: value pairs to store.
    """
    try:
        response = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract personal facts the user is sharing about themselves.\n"
                        "Only extract clearly stated, specific facts.\n"
                        "Common keys: name, age, location, job, hobby, language, goals, likes, dislikes\n\n"
                        "Return ONLY a JSON dict (no markdown, no extra text).\n"
                        "If nothing personal to extract, return: {}\n\n"
                        "Examples:\n"
                        '  Input: "My name is Alex and I live in Mumbai"\n'
                        '  Output: {"name": "Alex", "location": "Mumbai"}\n\n'
                        '  Input: "What is 2+2?"\n'
                        '  Output: {}'
                    )
                },
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=150
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start != -1 and end > start:
            data = json.loads(raw[start:end])
            if isinstance(data, dict):
                # Filter out empty/invalid values
                return {k: v for k, v in data.items() if v and isinstance(v, str) and len(v) < 100}
    except Exception:
        pass
    return {}


# ─────────────────────────────────────────
# RULE-BASED EXTRACTION (fast, offline)
# ─────────────────────────────────────────
PATTERNS = {
    "my name is":    "name",
    "i am called":   "name",
    "call me":       "name",
    "i live in":     "location",
    "i'm from":      "location",
    "i am from":     "location",
    "i work as":     "job",
    "i am a ":       "job",
    "i'm a ":        "job",
    "i like":        "likes",
    "i love":        "loves",
    "i hate":        "dislikes",
    "i dislike":     "dislikes",
    "my hobby is":   "hobby",
    "i speak":       "language",
    "my age is":     "age",
    "i am ":         "age",  # "I am 25 years old"
}

def extract_facts_rules(text: str) -> dict:
    """Fast rule-based extraction for common patterns."""
    facts = {}
    text_lower = text.lower()

    for phrase, key in PATTERNS.items():
        if phrase in text_lower:
            # Get the text after the phrase
            value = text_lower.split(phrase, 1)[-1].strip()
            # Stop at sentence end or common punctuation
            for stopper in [".", ",", "!", "?", " and ", " but ", " because "]:
                if stopper in value:
                    value = value.split(stopper)[0].strip()
            # Only keep short, meaningful values
            if value and 1 < len(value) < 60:
                facts[key] = value.title() if key in ("name", "location") else value

    return facts


# ─────────────────────────────────────────
# UPDATE MEMORY
# ─────────────────────────────────────────
def update_memory(memory: dict, text: str) -> dict:
    """
    Extract facts from user message and update memory.
    Combines rule-based (fast) and LLM-based (smart) extraction.
    """
    # Rule-based first (instant)
    rule_facts = extract_facts_rules(text)
    memory.update(rule_facts)

    # LLM-based for more nuanced extraction
    llm_facts = extract_facts_llm(text)
    if llm_facts:
        memory.update(llm_facts)

    return memory


# ─────────────────────────────────────────
# MEMORY SUMMARY (for display)
# ─────────────────────────────────────────
def format_memory(memory: dict) -> str:
    """Format memory for display in the sidebar."""
    if not memory:
        return "Nothing stored yet.\nTell me your name, location, etc."

    lines = []
    icon_map = {
        "name":     "👤",
        "location": "📍",
        "job":      "💼",
        "age":      "🎂",
        "likes":    "❤️",
        "loves":    "💖",
        "dislikes": "👎",
        "hobby":    "🎯",
        "language": "🌐",
        "goals":    "🎯",
    }
    for key, value in memory.items():
        icon = icon_map.get(key.lower(), "📌")
        lines.append(f"{icon} **{key.capitalize()}**: {value}")

    return "\n\n".join(lines)
