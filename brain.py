"""
brain.py — Core intelligence module
Uses Groq API (free, fast) with llama3 for all reasoning tasks.
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
# ─────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Fast model for quick tasks, smart model for deep reasoning
FAST_MODEL  = "llama-3.1-8b-instant"   # Intent, planning, step decisions
SMART_MODEL = "llama-3.3-70b-versatile" # Chat, reasoning, final answers


# ─────────────────────────────────────────
# HELPER: LLM CALL
# ─────────────────────────────────────────
def llm_call(messages, model=SMART_MODEL, temperature=0.7, max_tokens=2048):
    """Universal LLM call using Groq API."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[LLM Error: {str(e)}]"


# ─────────────────────────────────────────
# HELPER: SAFE JSON PARSE
# ─────────────────────────────────────────
def safe_parse(text):
    """Safely extract JSON from LLM response."""
    try:
        text = text.strip()
        # Remove markdown code blocks
        text = text.replace("```json", "").replace("```", "").strip()
        # Find first { ... }
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except Exception:
        pass
    return None


# ─────────────────────────────────────────
# 1. INTENT DETECTION
# ─────────────────────────────────────────
def detect_intent(user_input: str) -> str:
    """
    Classify what the user wants:
    - chat     → casual talk, greetings, opinions, simple Q&A
    - research → needs live web data, news, current facts
    - task     → code, analysis, writing, complex reasoning
    """
    messages = [
        {
            "role": "system",
            "content": (
                "Classify the user message into ONE category.\n\n"
                "Categories:\n"
                "- chat: casual talk, greetings, simple questions answerable from knowledge\n"
                "- research: needs current web data, news, prices, recent events, live info\n"
                "- task: code writing, math, analysis, document creation, complex reasoning\n\n"
                "Return ONLY JSON:\n"
                '{"type": "chat" | "research" | "task"}'
            )
        },
        {"role": "user", "content": user_input}
    ]
    response = llm_call(messages, model=FAST_MODEL, temperature=0.1, max_tokens=60)
    data = safe_parse(response)
    if data and data.get("type") in ("chat", "research", "task"):
        return data["type"]
    return "chat"


# ─────────────────────────────────────────
# 2. CHAT RESPONSE (ChatGPT style)
# ─────────────────────────────────────────
def chat_response(user_input: str, memory: dict, conversation_history: list) -> str:
    """
    Natural, context-aware conversation — like ChatGPT.
    Uses conversation history for continuity.
    """
    memory_text = json.dumps(memory, indent=2) if memory else "Nothing stored yet."

    system_prompt = f"""You are Jarvis, a highly intelligent and friendly AI assistant.

What you know about the user:
{memory_text}

Guidelines:
- Respond naturally and conversationally
- Use the user's name if you know it
- Be clear, concise, and helpful
- For technical topics, be precise and give examples
- Show personality — be warm and engaging
- For code questions, always give working, complete code"""

    messages = [{"role": "system", "content": system_prompt}]

    # Add last 8 messages as context
    for msg in conversation_history[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_input})

    return llm_call(messages, model=SMART_MODEL, temperature=0.7, max_tokens=1500)


# ─────────────────────────────────────────
# 3. REASONING RESPONSE (Claude style)
# ─────────────────────────────────────────
def reasoning_response(user_input: str, memory: dict, conversation_history: list) -> str:
    """
    Deep reasoning for complex tasks — like Claude.
    Breaks down problems, thinks step by step.
    """
    system_prompt = """You are an expert AI with deep reasoning and problem-solving capabilities.

For complex questions:
1. Break the problem into clear parts
2. Reason through each part carefully
3. Provide a structured, well-explained answer

For code tasks:
- Provide complete, working, commented code
- Explain the approach before the code
- Mention edge cases and potential issues

For analysis:
- Be thorough and structured
- Use headers and bullet points for clarity
- Provide concrete examples

Always think before answering. Quality over speed."""

    messages = [{"role": "system", "content": system_prompt}]

    for msg in conversation_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_input})

    return llm_call(messages, model=SMART_MODEL, temperature=0.4, max_tokens=3000)


# ─────────────────────────────────────────
# 4. CREATE PLAN (Manus AI style)
# ─────────────────────────────────────────
def create_plan(user_input: str) -> list:
    """
    Break a complex task into 2-4 actionable steps.
    Like Manus AI's task planning.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are a task planner. Break the user's request into 2-4 clear steps.\n\n"
                "Available tools for steps:\n"
                "- search: search the web\n"
                "- read: read a specific webpage\n"
                "- youtube: search YouTube\n"
                "- none: answer from knowledge directly\n\n"
                "Return ONLY JSON:\n"
                '{"steps": ["step 1 description", "step 2 description"]}'
            )
        },
        {"role": "user", "content": f"Task: {user_input}"}
    ]
    response = llm_call(messages, model=FAST_MODEL, temperature=0.1, max_tokens=200)
    data = safe_parse(response)
    if data and isinstance(data.get("steps"), list):
        return data["steps"][:4]  # Max 4 steps
    return [user_input]


# ─────────────────────────────────────────
# 5. EXECUTE STEP (Agent decision)
# ─────────────────────────────────────────
def execute_step(step: str, memory: dict, history: str) -> dict:
    """
    For each step, decide:
    - Use a tool (search/read/youtube)
    - Or answer directly
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI agent. Decide how to execute the given step.\n\n"
                "Tools available:\n"
                "- search: Use to find current information, news, facts from the web\n"
                "- read: Use to read a specific URL (provide full URL as input)\n"
                "- youtube: Use to find videos on YouTube\n"
                "- none: Answer directly without any tool\n\n"
                "Return ONLY JSON:\n"
                "{\n"
                '  "tool": "search" | "read" | "youtube" | "none",\n'
                '  "input": "search query or URL",\n'
                '  "final": "direct answer if tool=none, else null"\n'
                "}"
            )
        },
        {
            "role": "user",
            "content": (
                f"Step: {step}\n"
                f"Context gathered so far:\n{history[-800:] if history else 'None'}"
            )
        }
    ]
    response = llm_call(messages, model=FAST_MODEL, temperature=0.1, max_tokens=200)
    data = safe_parse(response)
    if data:
        return data
    # Fallback: answer directly
    return {"tool": "none", "input": "", "final": step}


# ─────────────────────────────────────────
# 6. GENERATE FINAL ANSWER (Perplexity style)
# ─────────────────────────────────────────
def generate_final_answer(user_input: str, research: str, memory: dict, conversation_history: list) -> str:
    """
    Synthesize gathered research into a clear final answer.
    Like Perplexity — structured, informative, accurate.
    """
    memory_text = json.dumps(memory, indent=2) if memory else "None"

    system_prompt = f"""You are Jarvis, an intelligent research assistant like Perplexity AI.

User context: {memory_text}

Your job:
- Synthesize the research gathered into a clear, helpful answer
- Use markdown formatting (bold, bullets, headers where helpful)
- Be accurate — only state what the research supports
- Be comprehensive but not verbose
- If research is incomplete, say what you found and what's uncertain
- Cite source URLs naturally (e.g., "According to [source]...")"""

    messages = [{"role": "system", "content": system_prompt}]

    for msg in conversation_history[-4:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({
        "role": "user",
        "content": (
            f"Original question: {user_input}\n\n"
            f"Research gathered:\n{research}\n\n"
            "Please provide a comprehensive, well-structured answer."
        )
    })

    return llm_call(messages, model=SMART_MODEL, temperature=0.5, max_tokens=2000)
