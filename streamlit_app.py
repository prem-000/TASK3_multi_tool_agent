
import streamlit as st

from agent.executor import (
    build_agent,
    run_agent,
    extract_final_answer,
    extract_trace,
    REQUIRED_TOOLS,
)
from agent.prompts import DEMO_QUERY
from config.settings import get_settings
from evaluation.evaluator import evaluate_agent_run

st.set_page_config(
    page_title="Multi-Tool Autonomous AI Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Multi-Tool Autonomous AI Agent")
st.caption(
    "Gemini + LangChain | Web Search | Calculator | Local File Reader"
)


@st.cache_resource
def load_agent():
    settings = get_settings()
    return build_agent(settings), settings.model


try:
    agent, model_name = load_agent()
except Exception as exc:
    st.error(f"Agent initialization failed: {type(exc).__name__}: {exc}")
    st.info(
        "Check that GEMINI_API_KEY is available in Colab Secrets and "
        "has been exposed as GOOGLE_API_KEY before starting Streamlit."
    )
    st.stop()

st.caption(f"Model: `{model_name}`")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "latest_evaluation" not in st.session_state:
    st.session_state.latest_evaluation = None

with st.sidebar:
    st.subheader("Tools")
    st.markdown(
        "- 🌐 **Web Search:** DuckDuckGo\n"
        "- 🧮 **Calculator:** safe arithmetic\n"
        "- 📄 **File Reader:** text files in `data/`"
    )

    st.divider()
    st.subheader("Local file")

    uploaded_file = st.file_uploader(
        "Add a text file to the project's data folder",
        type=["txt", "md", "csv", "json", "log"],
    )

    if uploaded_file is not None:
        from config.settings import PROJECT_ROOT

        data_dir = (PROJECT_ROOT / "data").resolve()
        data_dir.mkdir(parents=True, exist_ok=True)

        safe_name = uploaded_file.name.replace("/", "_").replace("\\", "_")
        blocked = {
            ".env", "secrets.toml", "credentials.json",
            "passwords.txt", "api_key.txt",
        }

        if safe_name.lower() in blocked or any(
            word in safe_name.lower()
            for word in ("password", "secret", "api_key", "token")
        ):
            st.error("That filename is not allowed.")
        elif len(uploaded_file.getvalue()) > 1_000_000:
            st.error("Please upload a file smaller than 1 MB.")
        else:
            target = (data_dir / safe_name).resolve()
            if target.parent != data_dir:
                st.error("Invalid file path.")
            else:
                target.write_bytes(uploaded_file.getvalue())
                st.success(f"Saved {safe_name} inside data/.")

    st.divider()

    if st.button("Run compound demo", use_container_width=True):
        st.session_state.pending_query = "/demo"
        st.rerun()

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.latest_evaluation = None
        st.session_state.pop("pending_query", None)
        st.rerun()


# Show conversation history.
for item in st.session_state.chat_history:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

        if item["role"] == "assistant" and item.get("trace"):
            with st.expander("View tool actions and observations"):
                for step in item["trace"]:
                    if step["type"] == "ACTION":
                        st.markdown(f"**ACTION — {step['tool']}**")
                        st.json(step["arguments"])
                    else:
                        st.markdown(f"**OBSERVATION — {step['tool']}**")
                        st.code(step["content"][:4000])

        if item["role"] == "assistant" and item.get("evaluation"):
            with st.expander("Execution evaluation"):
                st.json(item["evaluation"])


pending = st.session_state.pop("pending_query", None)
typed_query = st.chat_input("Give the agent a multi-step task...")
query = pending or typed_query

if query:
    is_demo = query.strip().lower() == "/demo"
    actual_query = DEMO_QUERY if is_demo else query

    st.session_state.chat_history.append({
        "role": "user",
        "content": actual_query if is_demo else query,
    })

    with st.chat_message("user"):
        st.markdown(actual_query if is_demo else query)

    # Send only clean user/assistant conversation turns to the agent.
    messages = [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.chat_history
        if item["role"] in {"user", "assistant"}
    ]

    with st.chat_message("assistant"):
        try:
            with st.spinner("Agent is selecting and running tools..."):
                result = run_agent(agent, messages)

            output_messages = result["messages"]
            answer = extract_final_answer(output_messages)
            trace = extract_trace(output_messages)

            st.markdown(answer)

            with st.expander("Tool actions and observations", expanded=True):
                if not trace:
                    st.write("No tools were invoked for this request.")

                for step in trace:
                    if step["type"] == "ACTION":
                        st.markdown(f"**ACTION — {step['tool']}**")
                        st.json(step["arguments"])
                    else:
                        st.markdown(f"**OBSERVATION — {step['tool']}**")
                        st.code(step["content"][:4000])

            evaluation = evaluate_agent_run(
                output_messages,
                REQUIRED_TOOLS if is_demo else set(),
            )

            with st.expander("Execution evaluation"):
                st.json(evaluation)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer,
                "trace": trace,
                "evaluation": evaluation,
            })

            st.session_state.latest_evaluation = evaluation

        except Exception as exc:
            error_text = (
                f"Agent failed: {type(exc).__name__}: {exc}"
            )
            st.error(error_text)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_text,
                "trace": [],
                "evaluation": None,
            })