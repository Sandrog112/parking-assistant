import uuid

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from parking_assistant.graph.workflow import build_graph

st.set_page_config(page_title="Parking Assistant", page_icon="🅿️", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }
    .main-header {
        text-align: center;
        padding: 1rem 0 0.5rem;
    }
    .main-header h1 {
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
    }
    .main-header p {
        color: #8892b0;
        font-size: 1.05rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-pending { background: #fbbf2433; color: #fbbf24; border: 1px solid #fbbf2455; }
    .badge-approved { background: #22c55e33; color: #22c55e; border: 1px solid #22c55e55; }
    .badge-rejected { background: #ef444433; color: #ef4444; border: 1px solid #ef444455; }
    .info-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
    }
    .sidebar .stButton > button {
        width: 100%;
        border-radius: 8px;
    }
    div[data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

if "thread_id" not in st.session_state:
    st.session_state.thread_id = uuid.uuid4().hex
if "messages" not in st.session_state:
    st.session_state.messages = []
if "graph" not in st.session_state:
    from langgraph.checkpoint.memory import MemorySaver
    st.session_state.graph = build_graph().compile(checkpointer=MemorySaver())
if "awaiting_approval" not in st.session_state:
    st.session_state.awaiting_approval = False
if "pending_reservation" not in st.session_state:
    st.session_state.pending_reservation = None


def get_config():
    return {"configurable": {"thread_id": st.session_state.thread_id}}


def reset_chat():
    st.session_state.thread_id = uuid.uuid4().hex
    st.session_state.messages = []
    st.session_state.awaiting_approval = False
    st.session_state.pending_reservation = None
    from langgraph.checkpoint.memory import MemorySaver
    st.session_state.graph = build_graph().compile(checkpointer=MemorySaver())


with st.sidebar:
    st.markdown("## 🅿️ Parking Assistant")
    st.divider()

    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("**Ask me about:**")
    st.markdown("- 💰 Parking rates & pricing")
    st.markdown("- 🕐 Hours of operation")
    st.markdown("- 📍 Location & directions")
    st.markdown("- ⚡ EV charging spots")
    st.markdown("- 📋 Make a reservation")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("**Reservation flow:**")
    st.markdown("1. Tell me you want to reserve")
    st.markdown("2. Provide name, surname, car #, times")
    st.markdown("3. Admin reviews & approves")
    st.markdown("4. Confirmation sent!")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🔄 New Conversation", use_container_width=True):
        reset_chat()
        st.rerun()

    st.divider()
    st.caption(f"Session: `{st.session_state.thread_id[:8]}...`")

st.markdown("""
<div class="main-header">
    <h1>🅿️ Parking Assistant</h1>
    <p>Your intelligent parking concierge — ask questions or make a reservation</p>
</div>
""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🅿️"):
        st.markdown(msg["content"])

if st.session_state.awaiting_approval and st.session_state.pending_reservation:
    res = st.session_state.pending_reservation
    st.divider()
    st.markdown("### 🔔 Reservation Awaiting Admin Approval")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Name", f"{res.get('name', '')} {res.get('surname', '')}")
    with col2:
        st.metric("Car Number", res.get("car_number", ""))
    with col3:
        st.metric("Period", f"{res.get('start_time', '')} → {res.get('end_time', '')}")

    st.markdown('<span class="status-badge badge-pending">⏳ PENDING</span>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✅ Approve", use_container_width=True, type="primary"):
            with st.spinner("Processing approval..."):
                result = st.session_state.graph.invoke(
                    Command(resume={"approved": True, "reason": "Approved by admin"}),
                    config=get_config(),
                )
                messages = result.get("messages", [])
                if messages:
                    reply = messages[-1].content
                    st.session_state.messages.append({"role": "assistant", "content": reply})
            st.session_state.awaiting_approval = False
            st.session_state.pending_reservation = None
            st.rerun()

    with col_b:
        if st.button("❌ Reject", use_container_width=True):
            with st.spinner("Processing rejection..."):
                result = st.session_state.graph.invoke(
                    Command(resume={"approved": False, "reason": "Rejected by admin"}),
                    config=get_config(),
                )
                messages = result.get("messages", [])
                if messages:
                    reply = messages[-1].content
                    st.session_state.messages.append({"role": "assistant", "content": reply})
            st.session_state.awaiting_approval = False
            st.session_state.pending_reservation = None
            st.rerun()

elif prompt := st.chat_input("Ask about parking or make a reservation..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🅿️"):
        with st.spinner("Thinking..."):
            result = st.session_state.graph.invoke(
                {"messages": [HumanMessage(content=prompt)]},
                config=get_config(),
            )

            state = st.session_state.graph.get_state(get_config())

            if state.next and "admin_approval" in state.next:
                pending = state.values.get("pending_reservation", {})
                st.session_state.awaiting_approval = True
                st.session_state.pending_reservation = pending

                messages = result.get("messages", [])
                if messages:
                    reply = messages[-1].content
                else:
                    reply = "Your reservation request has been created. Awaiting admin approval..."
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.markdown(reply)
                st.rerun()
            else:
                messages = result.get("messages", [])
                reply = messages[-1].content if messages else "I'm here to help with parking questions!"
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.markdown(reply)
