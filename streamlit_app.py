import logging
from typing import List, Optional

import streamlit as st

from aipg.assistant import Assistant
from aipg.configs.app_config import AppConfig
from aipg.configs.loader import load_config
from aipg.task import Task


# ---------------------------
# Page and global styling
# ---------------------------
st.set_page_config(
    page_title="AI Micro-Project Generator",
    page_icon="✨",
    # layout="wide",
)

CUSTOM_CSS = """
<style>
  :root {
    --primary: #6d28d9;
    --primary-700: #5b21b6;
    --bg: #0b1020;
    --card: #0f172a;
    --muted: #94a3b8;
    --text: #e2e8f0;
    --accent: #22d3ee;
  }

  .stApp {
    background: radial-gradient(1200px 500px at 20% -10%, rgba(109,40,217,0.18), transparent 60%),
                radial-gradient(1000px 400px at 80% 0%, rgba(34,211,238,0.10), transparent 60%),
                var(--bg);
    color: var(--text);
  }

  .aipg-title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, var(--text), var(--accent));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin-bottom: 0.25rem;
  }

  .aipg-subtitle {
    color: var(--muted);
    font-size: 0.98rem;
    margin-bottom: 1.5rem;
  }

  .aipg-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02));
    border: 1px solid rgba(148,163,184,0.12);
    border-radius: 14px;
    padding: 1.2rem;
    box-shadow: 0 6px 20px rgba(0,0,0,0.25);
  }

  .aipg-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 999px;
    border: 1px solid rgba(148,163,184,0.18);
    color: var(--muted);
    font-size: 0.85rem;
    background: rgba(17,24,39,0.35);
    backdrop-filter: blur(6px);
  }

  .aipg-pill b { color: var(--text); }

  .stTextArea textarea, .stTextInput input, .stNumberInput input {
    background: #0b132a !important;
    border: 1px solid rgba(148,163,184,0.18) !important;
    color: var(--text) !important;
  }

  .stButton>button {
    background: linear-gradient(90deg, var(--primary), var(--primary-700));
    color: white;
    border: 0;
    padding: 0.65rem 1rem;
    border-radius: 12px;
    font-weight: 700;
  }

  .stButton>button:hover { filter: brightness(1.06); }

  .aipg-section-title {
    font-weight: 700;
    margin: 0 0 0.6rem 0;
    color: var(--text);
  }

  .aipg-mono {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def get_config(presets: Optional[str], overrides: List[str]) -> AppConfig:
    try:
        return load_config(presets, None, overrides, AppConfig)
    except Exception as e:
        st.error(f"Failed to load config: {e}")
        raise


def render_header():
    left, right = st.columns([0.75, 0.25])
    with left:
        st.markdown("<div class='aipg-title'>AI Micro-Project Generator</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='aipg-subtitle'>Generate focused micro-tasks that address specific misconceptions using your preferred LLM provider.</div>",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            "<div class='aipg-pill aipg-mono'>Session: <b>{}</b></div>".format("auto"),
            unsafe_allow_html=True,
        )


def render_sidebar() -> dict:
    st.sidebar.markdown("### Configuration")

    customize = st.sidebar.toggle("Customize configuration", value=False)
    if not customize:
        st.sidebar.info("Using default config (from package presets and environment).")
        return {"overrides": [], "customize": False}

    with st.sidebar.expander("LLM", expanded=True):
        model_name = st.text_input("Model name", value="gemini/gemini-2.0-flash")
        base_url = st.text_input("Base URL (optional)", value="")
        api_key = st.text_input("API Key", type="password")
        temperature = st.number_input("Temperature", value=0.5, min_value=0.0, max_value=2.0, step=0.1)
        max_tokens = st.number_input("Max completion tokens", value=500, min_value=1, step=50)
        caching_enabled = st.toggle("Enable caching", value=True)

    with st.sidebar.expander("Langfuse (optional)", expanded=False):
        lf_host = st.text_input("Host", value="https://cloud.langfuse.com")
        lf_pk = st.text_input("Public Key", value="")
        lf_sk = st.text_input("Secret Key", value="", type="password")

    with st.sidebar.expander("Runtime", expanded=False):
        task_timeout = st.number_input("Task timeout (sec)", value=3600, min_value=10, step=10)
        time_limit = st.number_input("Total time limit (sec)", value=14400, min_value=60, step=60)

    overrides: List[str] = []
    overrides.append(f"llm.model_name='{model_name}'")
    if base_url:
        overrides.append(f"llm.base_url='{base_url}'")
    if api_key:
        overrides.append(f"llm.api_key='{api_key}'")
    overrides.append(f"llm.max_completion_tokens={int(max_tokens)}")
    overrides.append(f"llm.temperature={float(temperature)}")
    overrides.append(f"llm.caching.enabled={str(bool(caching_enabled))}")
    if lf_host:
        overrides.append(f"langfuse.host='{lf_host}'")
    if lf_pk:
        overrides.append(f"langfuse.public_key='{lf_pk}'")
    if lf_sk:
        overrides.append(f"langfuse.secret_key='{lf_sk}'")
    overrides.append(f"task_timeout={int(task_timeout)}")
    overrides.append(f"time_limit={int(time_limit)}")

    return {"overrides": overrides, "customize": True}


def main():
    logging.basicConfig(level=logging.INFO)
    render_header()

    # Input section
    st.markdown("### Describe the user's mistake or misconception")
    user_issue = st.text_area(
        "", height=180, placeholder="Describe the error or misconception students often have..."
    )

    sidebar_state = render_sidebar()

    generate = st.button("Generate Micro-Project ✨", use_container_width=True)

    if generate:
        if not user_issue.strip():
            st.warning("Please provide a description of the mistake/misconception.")
            st.stop()

        # Build config (use defaults if not customizing)
        overrides = sidebar_state.get("overrides", [])
        config = get_config(presets=None, overrides=overrides)  # type: ignore[arg-type]

        # Run assistant
        with st.spinner("Generating micro-project..."):
            assistant = Assistant(config)
            task = Task(issue_description=user_issue)
            task = assistant.generate_project(task)

        # Results
        st.markdown("---")

        # col1, col2 = st.columns([0.55, 0.45])
        # with col1:
        st.markdown("#### Task Description")
        st.markdown(task.task_description or "—")
        st.markdown("#### Goal")
        st.markdown(task.task_goal or "—")
        with st.expander("Expert Solution", expanded=False):
            st.markdown(task.expert_solution or "—")
        # with col2:
        #     with st.expander("Expert Solution", expanded=False):
        #         st.markdown(task.expert_solution or "—")

        # with st.expander("Raw object", expanded=False):
        #     st.json(
        #         {
        #             "task_description": task.task_description,
        #             "task_goal": task.task_goal,
        #             "expert_solution": task.expert_solution,
        #         }
        #     )


if __name__ == "__main__":
    main()


