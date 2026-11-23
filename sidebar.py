# Shared sidebar: Stockswisdom link plus a dropdown of pages 

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
COMPANY_URL = "https://stockswisdom.com/"

# Display names that differ from the file stem
CUSTOM_TITLES = {
    "screener": "Stock Screener",
    "compare": "Performance Comparison",
    "probabilities": "Probability Analysis",
}


def _title_from_stem(stem: str) -> str:
    parts = stem.split("_")
    if parts and parts[0].isdigit():
        parts = parts[1:]
    title = " ".join(parts) or stem
    return CUSTOM_TITLES.get(title.lower(), title)


def discover_pages() -> list[tuple[str, Path]]:
    """Landing page first, then every script in the pages directory."""
    pages = [("Market Trend", ROOT / "app.py")]

    pages_dir = ROOT / "pages"
    if pages_dir.is_dir():
        for path in sorted(pages_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            pages.append((_title_from_stem(path.stem), path))

    return pages


def render_sidebar(current: str) -> None:
    pages = discover_pages()
    labels = [name for name, _ in pages]

    if current not in labels:
        current = labels[0]

    if "nav_page" not in st.session_state:
        st.session_state.nav_page = current

    with st.sidebar:
        st.markdown(
            f'<a href="{COMPANY_URL}" target="_blank" rel="noopener noreferrer" '
            'style="text-decoration:none;color:#143d32;">'
            '<span style="font-size:1.7rem;font-weight:650;letter-spacing:-0.03em;">'
            "Stockswisdom</span></a>",
            unsafe_allow_html=True,
        )

        selected = st.selectbox(
            "Pages",
            labels,
            index=labels.index(st.session_state.nav_page),
            key="nav_select",
        )

    if selected != st.session_state.nav_page:
        st.session_state.nav_page = selected
        target = dict(pages)[selected]
        st.switch_page(str(target.relative_to(ROOT)))