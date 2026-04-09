"""
app.py — Jarvis AI: Main Streamlit Application

Architecture:
  - Chat mode    → Natural conversation (ChatGPT style)
  - Research mode → Web search + synthesis (Perplexity style)
  - Task mode    → Deep reasoning + planning (Claude + Manus style)
"""

import streamlit as st
from brain import (
    detect_intent,
    chat_response,
    reasoning_response,
    create_plan,
    execute_step,
    generate_final_answer
)
from actions import execute_tool
from memory import load_memory, save_memory, update_memory, format_memory


# ════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════
st.set_page_config(
    page_title="Jarvis AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ════════════════════════════════════════════
# STYLING
# ════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Space+Mono:wght@400;700&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Main background */
.stApp {
    background: #0a0a0f;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f0f1a;
    border-right: 1px solid #1e1e2e;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 4px 0 !important;
}

/* User message */
[data-testid="stChatMessage"][data-testid*="user"] {
    flex-direction: row-reverse;
}

/* Input box */
[data-testid="stChatInput"] {
    background: #12121f !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}

/* Status badges */
.status-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    font-family: 'Space Mono', monospace;
    margin-bottom: 8px;
}
.badge-chat     { background: #1e3a2f; color: #4ade80; border: 1px solid #166534; }
.badge-research { background: #1e2a4a; color: #60a5fa; border: 1px solid #1e40af; }
.badge-task     { background: #2a1e3a; color: #c084fc; border: 1px solid #7c3aed; }

/* Step indicator */
.step-indicator {
    font-size: 12px;
    color: #64748b;
    font-family: 'Space Mono', monospace;
    padding: 4px 0;
}

/* Memory card */
.memory-card {
    background: #12121f;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 8px;
}

/* Title */
.jarvis-title {
    font-family: 'Space Mono', monospace;
    font-size: 20px;
    font-weight: 700;
    color: #e2e8f0;
    letter-spacing: 2px;
}
.jarvis-sub {
    font-size: 12px;
    color: #4a5568;
    letter-spacing: 1px;
}

/* Scrollable chat */
.main .block-container {
    max-width: 860px;
    padding-bottom: 100px;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════
# SESSION STATE INIT
# ════════════════════════════════════════════
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role":    "assistant",
            "content": "Hello! I'm **Jarvis**, your AI assistant.\n\nI can:\n- 💬 Chat naturally about anything\n- 🔍 Search the web for current information\n- 🧠 Reason through complex tasks and write code\n- 📋 Plan and execute multi-step tasks\n\nWhat would you like to do?",
            "mode":    "chat"
        }
    ]

if "memory" not in st.session_state:
    st.session_state.memory = load_memory()

if "thinking" not in st.session_state:
    st.session_state.thinking = False


# ════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════
with st.sidebar:
    st.markdown('<p class="jarvis-title">⚡ JARVIS</p>', unsafe_allow_html=True)
    st.markdown('<p class="jarvis-sub">AI ASSISTANT v2.0</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Capabilities
    st.markdown("### 🧩 Capabilities")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<span class="status-badge badge-chat">💬 CHAT</span>',     unsafe_allow_html=True)
        st.markdown('<span class="status-badge badge-task">🧠 REASON</span>',   unsafe_allow_html=True)
    with col2:
        st.markdown('<span class="status-badge badge-research">🔍 SEARCH</span>', unsafe_allow_html=True)
        st.markdown('<span class="status-badge badge-task">📋 PLAN</span>',       unsafe_allow_html=True)

    st.markdown("---")

    # Memory display
    st.markdown("### 🧠 Memory")
    memory_display = format_memory(st.session_state.memory)
    st.markdown(
        f'<div class="memory-card">{memory_display}</div>',
        unsafe_allow_html=True
    )

    if st.session_state.memory:
        if st.button("🗑️ Clear Memory", use_container_width=True):
            st.session_state.memory = {}
            save_memory({})
            st.success("Memory cleared!")
            st.rerun()

    st.markdown("---")

    # Settings
    st.markdown("### ⚙️ Settings")
    force_research = st.toggle("🔍 Force Web Search", value=False,
                               help="Always search the web, even for simple questions")
    force_reasoning = st.toggle("🧠 Force Deep Reasoning", value=False,
                                help="Use deep reasoning mode for all responses")
    show_steps = st.toggle("📋 Show Agent Steps", value=True,
                           help="Show what the agent is doing in real time")

    st.markdown("---")

    # Clear chat
    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = [
            {
                "role":    "assistant",
                "content": "Chat cleared. How can I help you?",
                "mode":    "chat"
            }
        ]
        st.rerun()

    st.markdown(
        '<p style="color:#2d3748; font-size:11px; text-align:center; margin-top:20px;">'
        'Powered by Groq + LLaMA 3</p>',
        unsafe_allow_html=True
    )


# ════════════════════════════════════════════
# CHAT DISPLAY
# ════════════════════════════════════════════
badge_html = {
    "chat":     '<span class="status-badge badge-chat">💬 CHAT</span>',
    "research": '<span class="status-badge badge-research">🔍 RESEARCH</span>',
    "task":     '<span class="status-badge badge-task">🧠 TASK</span>',
}

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
        if msg["role"] == "assistant" and "mode" in msg:
            mode = msg.get("mode", "chat")
            st.markdown(badge_html.get(mode, ""), unsafe_allow_html=True)
        st.markdown(msg["content"])


# ════════════════════════════════════════════
# AGENT: RESEARCH / TASK RUNNER
# ════════════════════════════════════════════
def run_agent(user_input: str, status_container) -> str:
    """
    Manus AI-style agent:
    Plan → Execute steps → Gather research → Synthesize answer
    """
    history = ""

    with status_container:
        # Step 1: Create plan
        if show_steps:
            st.markdown('<p class="step-indicator">📋 Planning steps...</p>', unsafe_allow_html=True)

        steps = create_plan(user_input)

        if show_steps:
            st.markdown(
                f'<p class="step-indicator">📋 Plan: {len(steps)} step(s) identified</p>',
                unsafe_allow_html=True
            )

        # Step 2: Execute each step
        for i, step in enumerate(steps, 1):
            if show_steps:
                st.markdown(
                    f'<p class="step-indicator">⚡ Step {i}/{len(steps)}: {step[:60]}...</p>',
                    unsafe_allow_html=True
                )

            result    = execute_step(step, st.session_state.memory, history)
            tool      = result.get("tool", "none")
            tool_input = result.get("input", "")
            final     = result.get("final")

            # If agent decided to answer directly
            if final and tool == "none":
                history += f"\n\nStep {i} result: {final}"
                continue

            # Use a tool
            if tool and tool != "none" and tool_input:
                if show_steps:
                    st.markdown(
                        f'<p class="step-indicator">🔧 Using tool: {tool} → {tool_input[:50]}</p>',
                        unsafe_allow_html=True
                    )

                output   = execute_tool(tool, tool_input)
                history += f"\n\nStep {i} ({tool}): {output[:1500]}"  # Limit per step

        if show_steps:
            st.markdown(
                '<p class="step-indicator">✅ Synthesizing answer...</p>',
                unsafe_allow_html=True
            )

    # Step 3: Generate final answer from all research
    return generate_final_answer(
        user_input,
        history,
        st.session_state.memory,
        st.session_state.messages
    )


# ════════════════════════════════════════════
# INPUT HANDLING
# ════════════════════════════════════════════
user_input = st.chat_input("Ask Jarvis anything...")

if user_input and user_input.strip():
    # Show user message immediately
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Update memory from user message
    st.session_state.memory = update_memory(st.session_state.memory, user_input)
    save_memory(st.session_state.memory)

    # Detect intent (unless overridden by toggles)
    if force_research:
        intent = "research"
    elif force_reasoning:
        intent = "task"
    else:
        intent = detect_intent(user_input)

    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        # Show mode badge
        st.markdown(badge_html.get(intent, badge_html["chat"]), unsafe_allow_html=True)

        # Container for agent steps (only for research/task)
        status_area = st.empty()

        with st.spinner("Thinking..."):
            if intent == "chat":
                response = chat_response(
                    user_input,
                    st.session_state.memory,
                    st.session_state.messages
                )
            elif intent == "task":
                response = reasoning_response(
                    user_input,
                    st.session_state.memory,
                    st.session_state.messages
                )
            else:  # research
                response = run_agent(user_input, status_area)

        # Clear the step indicators, show final response
        status_area.empty()
        st.markdown(response)

    # Save to history
    st.session_state.messages.append({
        "role":    "assistant",
        "content": response,
        "mode":    intent
    })

    st.rerun()
