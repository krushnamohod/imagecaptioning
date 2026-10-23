"""Streamlit interface for the AI image captioning FastAPI backend."""

from __future__ import annotations

import os
from datetime import datetime

import streamlit as st

from api_client import APIError, CaptionAPI


PLATFORMS = ["Instagram", "LinkedIn", "Facebook", "X (Twitter)"]
LANGUAGES = ["English", "Hindi", "Marathi"]
STYLES = [
    "Normal", "Formal", "Creative", "Humorous", "Marketing", "Travel",
    "Accessibility / Alt Text",
]
TEMPLATES = [
    "gradient_overlay",
    "instagram_creative",
    "linkedin_professional",
    "facebook_informative",
    "x_concise",
    "minimal_footer",
]

st.set_page_config(
    page_title="Caption Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root { --panel: rgba(19, 28, 49, .72); --line: rgba(148, 163, 198, .18); --accent: #a99aff; --muted: #a6b0c5; }
      .block-container { max-width: 1240px; padding-top: 1.6rem; padding-bottom: 2.5rem; }
      /* Dedicated line box avoids Streamlit's default paragraph metrics clipping these labels. */
      .eyebrow-label {
        display: block; box-sizing: border-box; width: fit-content; max-width: 100%;
        min-height: 1.55em; padding: .12em 0 .2em; margin: 0 0 .55rem;
        overflow: visible; color: var(--accent); font-size: .72rem; font-weight: 700;
        letter-spacing: .13em; line-height: 1.55; white-space: normal;
      }
      .eyebrow-label::after {
        content: ""; display: inline-block; width: 1.8rem; height: 2px; margin-left: .65rem;
        border-radius: 2px; vertical-align: middle;
        background: linear-gradient(90deg, #7969e8, #58a2dc, #7969e8); background-size: 200% 100%;
        animation: accent-drift 5s ease-in-out infinite alternate;
      }
      .project-subtitle { max-width: 46rem; color: var(--muted); margin: .15rem 0 1.5rem; line-height: 1.6; }
      div.st-key-page-heading h1 {
        margin: 0 0 .3rem; color: #f1f3fb; font-size: clamp(1.8rem, 3.2vw, 2.45rem);
        line-height: 1.22; letter-spacing: -.035em; overflow: visible;
      }
      div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--line); background: var(--panel);
        transition: border-color .2s ease, box-shadow .2s ease;
      }
      div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(151, 139, 245, .34); box-shadow: 0 8px 26px rgba(3, 8, 20, .16);
      }
      div[data-testid="stExpander"] { border-color: var(--line); transition: border-color .2s ease; }
      div[data-testid="stExpander"]:hover { border-color: rgba(151, 139, 245, .34); }
      .st-key-page-heading, .st-key-generation-results { animation: gentle-fade .32s ease-out both; }
      .stButton > button { transition: border-color .18s ease, background-color .18s ease, box-shadow .18s ease; }
      .stButton > button:hover { box-shadow: 0 4px 16px rgba(75, 87, 155, .18); }
      .muted { color: #9aa6bd; }
      @keyframes gentle-fade { from { opacity: 0; } to { opacity: 1; } }
      @keyframes accent-drift { from { background-position: 0% 50%; } to { background-position: 100% 50%; } }
      @media (max-width: 700px) {
        .block-container { padding: 1rem 1rem 2rem; }
        .eyebrow-label { font-size: .68rem; letter-spacing: .1em; }
      }
      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; transition-duration: .01ms !important; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def api() -> CaptionAPI:
    """Reuse a lightweight API client for this Streamlit session."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = CaptionAPI(os.getenv("BACKEND_API_URL"))
    return st.session_state.api_client


def initialize_state() -> None:
    defaults = {
        "generation": None,
        "captioned_png": None,
        "generation_error": None,
        "render_error": None,
        "pending_delete_id": None,
        "history_details": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def format_time(timestamp: str | None) -> str:
    if not timestamp:
        return "Time unavailable"
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return parsed.astimezone().strftime("%b %d, %Y · %I:%M %p %Z")
    except (TypeError, ValueError):
        return timestamp


def show_caption_results() -> None:
    result = st.session_state.generation
    if not result:
        return

    with st.container(key="generation-results"):
        st.subheader("Generation results")
        left, right = st.columns(2, gap="large")
        with left, st.container(border=True):
            st.markdown('<div class="eyebrow-label">BLIP | BASE CAPTION</div>', unsafe_allow_html=True)
            st.write(result["base_caption"])
        with right, st.container(border=True):
            st.markdown('<div class="eyebrow-label">GROQ | CUSTOM CAPTION</div>', unsafe_allow_html=True)
            st.write(result["generated_caption"])
            st.caption(
                f"{result.get('platform', 'Platform')} | {result.get('language', 'Language')} | "
                f"{result.get('style', 'Style')}"
            )

        if st.session_state.render_error:
            st.warning(
                "Both captions were generated and saved to history, but the captioned image "
                f"could not be rendered: {st.session_state.render_error}"
            )
        elif st.session_state.captioned_png:
            st.markdown("#### Captioned image")
            st.image(st.session_state.captioned_png, use_container_width=True)
            st.download_button(
                "Download captioned PNG",
                data=st.session_state.captioned_png,
                file_name="captioned-image.png",
                mime="image/png",
                type="primary",
            )

def generation_page() -> None:
    with st.container(key="page-heading"):
        st.markdown('<div class="eyebrow-label">AI-POWERED IMAGE CONTENT</div>', unsafe_allow_html=True)
        st.title("Caption Studio")
        st.markdown(
            '<div class="project-subtitle">Turn a photo into a thoughtful, platform-ready caption and a polished image.</div>',
            unsafe_allow_html=True,
        )

    upload_column, settings_column = st.columns([1.05, 0.95], gap="large")
    with upload_column, st.container(border=True):
        st.subheader("1 · Add an image")
        uploaded = st.file_uploader(
            "Upload a JPG, PNG, or WEBP image",
            type=["jpg", "jpeg", "png", "webp"],
            help="Images can be up to 10 MB.",
        )
        image_bytes = uploaded.getvalue() if uploaded is not None else None
        if uploaded is not None:
            if len(image_bytes) > 10 * 1024 * 1024:
                st.error("This image exceeds the 10 MB upload limit.")
                uploaded = None
                image_bytes = None
            else:
                st.image(image_bytes, caption=uploaded.name, use_container_width=True)
        if uploaded is None:
            st.info("Choose an image to preview it here before generation.")

    with settings_column, st.container(border=True):
        st.subheader("2 · Caption settings")
        platform = st.selectbox("Social platform", PLATFORMS, key="generate_platform")
        language = st.selectbox("Language", LANGUAGES, key="generate_language")
        style = st.selectbox("Writing style", STYLES, key="generate_style")
        template = st.selectbox("Visual template", TEMPLATES, key="generate_template")
        st.caption("The selected template is saved with this generation in history.")

    if st.button("✨  Generate Caption", type="primary", disabled=uploaded is None, use_container_width=True):
        st.session_state.generation = None
        st.session_state.captioned_png = None
        st.session_state.generation_error = None
        st.session_state.render_error = None
        try:
            with st.spinner("Generating captions with BLIP and Groq…"):
                generated = api().generate_captions(
                    image_bytes=image_bytes,
                    filename=uploaded.name,
                    platform=platform,
                    language=language,
                    style=style,
                    template=template,
                )
            # Store captions before rendering so a render error does not hide them.
            st.session_state.generation = generated
        except APIError as exc:
            st.session_state.generation_error = str(exc)
        else:
            try:
                with st.spinner("Rendering the captioned image…"):
                    st.session_state.captioned_png = api().render_captioned_image(
                        image_bytes=image_bytes,
                        filename=uploaded.name,
                        caption=generated["generated_caption"],
                        language=language,
                        template=template,
                    )
            except APIError as exc:
                st.session_state.render_error = str(exc)

    if st.session_state.generation_error:
        st.error(st.session_state.generation_error)
    show_caption_results()


def history_page() -> None:
    with st.container(key="page-heading"):
        st.markdown('<div class="eyebrow-label">YOUR PREVIOUS GENERATIONS</div>', unsafe_allow_html=True)
        st.title("Caption history")
        st.caption("History is shared by this application instance; it is not tied to a user account.")

    page_size = st.selectbox("Records per page", [10, 20, 50], index=1)
    if "history_offset" not in st.session_state:
        st.session_state.history_offset = 0
    offset = st.session_state.history_offset

    try:
        with st.spinner("Loading history…"):
            payload = api().list_history(limit=page_size, offset=offset)
    except APIError as exc:
        st.error(str(exc))
        if st.button("Try again"):
            st.rerun()
        return

    records = payload["records"]
    total = payload.get("total", len(records))
    if not records:
        st.info("No caption generations are in history yet. Generate a caption to see it here.")
    else:
        st.caption(f"Showing {offset + 1}–{offset + len(records)} of {total} records")
        for record in records:
            record_id = int(record["id"])
            header = f"{record.get('platform', 'Generation')}  ·  {format_time(record.get('created_at_utc'))}  ·  #{record_id}"
            with st.expander(header):
                st.markdown("**BLIP base caption**")
                st.write(record.get("base_caption", ""))
                st.markdown("**Groq-generated caption**")
                st.write(record.get("generated_caption", ""))
                st.caption(
                    f"Language: {record.get('language', '—')} · "
                    f"Style: {record.get('writing_style', '—')} · "
                    f"Template: {record.get('visual_template') or 'Not selected'}"
                )
                detail_column, delete_column = st.columns(2)
                with detail_column:
                    if st.button("Load record details", key=f"details_{record_id}"):
                        try:
                            st.session_state.history_details[record_id] = api().get_history_record(record_id)
                        except APIError as exc:
                            st.error(str(exc))
                    details = st.session_state.history_details.get(record_id)
                    if details:
                        st.json(details)
                with delete_column:
                    if st.session_state.pending_delete_id == record_id:
                        st.warning("Delete this history record?")
                        confirm, cancel = st.columns(2)
                        with confirm:
                            if st.button("Confirm delete", key=f"confirm_delete_{record_id}", type="primary"):
                                try:
                                    api().delete_history_record(record_id)
                                    st.session_state.pending_delete_id = None
                                    st.session_state.history_details.pop(record_id, None)
                                    st.success("Record deleted.")
                                    st.rerun()
                                except APIError as exc:
                                    st.error(str(exc))
                        with cancel:
                            if st.button("Cancel", key=f"cancel_delete_{record_id}"):
                                st.session_state.pending_delete_id = None
                                st.rerun()
                    elif st.button("Delete record", key=f"delete_{record_id}"):
                        st.session_state.pending_delete_id = record_id
                        st.rerun()

    previous_column, next_column = st.columns(2)
    with previous_column:
        if st.button("← Previous", disabled=offset <= 0):
            st.session_state.history_offset = max(0, offset - page_size)
            st.rerun()
    with next_column:
        if st.button("Next →", disabled=offset + len(records) >= total):
            st.session_state.history_offset = offset + page_size
            st.rerun()


def main() -> None:
    initialize_state()
    with st.sidebar:
        st.markdown("## ✨ Caption Studio")
        st.caption("Image captioning & content generation")
        page = st.radio("Workspace", ["Generate", "History"], label_visibility="collapsed")
        st.divider()
        st.caption("FastAPI backend")
        st.code(os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000"), language=None)

    if page == "Generate":
        generation_page()
    else:
        history_page()


if __name__ == "__main__":
    main()
