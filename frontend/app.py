"""Streamlit frontend for the AI Coding Tutor — fixed-composer two-column layout.

Layout overview
---------------
Wide-mode page
├── Sidebar  (previous conversations)
└── Main content
    ├── col_chat [75%]
    │   ├── st.container(height=CHAT_H)   ← scrollable conversation history + live stream
    │   └── st.chat_input()               ← always visible at the bottom of the column
    └── col_docs [25%]
        ├── File uploader + Upload button  ← always accessible at the top
        ├── st.container(height=DOCS_H)   ← scrollable attached-document list
        └── Clear Chat button              ← always accessible at the bottom

The conversation container has a fixed pixel height so it never grows the
page.  Messages scroll inside it.  st.chat_input() stays outside the
container and therefore below it at a constant position.

Streaming sequencing
--------------------
st.chat_input() is called BELOW the conversation container.  Its return
value is therefore unavailable inside the container block.  To stream
inside the container we use a one-run session-state queue:

  Run A: user submits → store question in session_state → st.rerun()
  Run B: container reads pending question → streams inside → appends answer → st.rerun()
  Run C: clean display with updated history inside the container
"""

from uuid import uuid4

import streamlit as st

from frontend.api.backend_client import (
    delete_session,
    load_conversation_summaries,
    load_session_messages,
    stream_question,
    upload_file,
    load_session_documents,
    delete_document,
)
from frontend.ui.render_service import render_chat
from frontend.ui.sidebar_service import render_sidebar

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

# Fixed pixel height for the scrollable conversation container.
# Adjust to taste — 540 px fits roughly 4–5 message pairs on a 1080p screen.
_CHAT_HEIGHT: int = 540

# Document list — grows naturally up to this row count, then becomes scrollable.
# Each row is ~40 px tall; cap at ~40 vh worth of content (≈380 px on 1080p).
_DOCS_MAX_ROWS: int = 9
_DOCS_MAX_PX: int = 380

# Allowed upload extensions.
_ALLOWED_TYPES = [
    "py", "js", "ts", "java", "cpp", "c", "cs", "go",
    "rs", "php", "rb", "swift", "kt", "txt", "md",
]

# Session-state key used to pass a question from st.chat_input() into the
# scrollable container on the next run.
_PENDING_KEY = "pending_question"


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------


def initialise_session() -> None:
    """Initialise Streamlit session state on first run (or after rerun)."""
    st.session_state.setdefault("session_id", str(uuid4()))
    st.session_state.setdefault("documents", [])
    st.session_state.setdefault("messages", None)
    st.session_state.setdefault("uploader_key", 0)

    if st.session_state.messages is None:
        try:
            st.session_state.messages = load_session_messages(
                st.session_state.session_id
            )
        except RuntimeError:
            st.session_state.messages = []

    if not st.session_state.documents:
        try:
            st.session_state.documents = load_session_documents(
                st.session_state.session_id
            )
        except RuntimeError:
            st.session_state.documents = []


def start_new_chat() -> None:
    """Reset state for a brand-new conversation."""
    st.session_state.session_id = str(uuid4())
    st.session_state.documents = []
    st.session_state.messages = []
    st.session_state.uploader_key += 1
    # Clear any pending question that belongs to the old session.
    st.session_state.pop(_PENDING_KEY, None)


def open_conversation(session_id: str) -> None:
    """Load an existing conversation from Supabase."""
    st.session_state.session_id = session_id
    st.session_state.pop(_PENDING_KEY, None)

    try:
        st.session_state.messages = load_session_messages(session_id)
    except RuntimeError:
        st.session_state.messages = []

    try:
        st.session_state.documents = load_session_documents(session_id)
    except RuntimeError:
        st.session_state.documents = []

    st.session_state.uploader_key += 1


# ---------------------------------------------------------------------------
# Left column — scrollable conversation + fixed composer
# ---------------------------------------------------------------------------


def _render_conversation_container() -> None:
    """Render the fixed-height scrollable conversation area.

    This container holds:
    1. The full conversation history (render_chat).
    2. The live streaming bubble when a question is pending.

    Streaming is triggered by reading ``_PENDING_KEY`` from session state
    rather than directly from st.chat_input(), because chat_input is called
    AFTER this container in the script (so it sits below the container in
    the DOM).  The pending-key pattern bridges the two runs cleanly:

        Run A  →  user submits via chat_input
               →  question stored in session_state[_PENDING_KEY]
               →  st.rerun()

        Run B  →  this function finds the pending question
               →  streams user + assistant bubbles inside the container
               →  appends the completed answer to session_state.messages
               →  st.rerun()

        Run C  →  no pending question; render_chat shows full history
    """
    with st.container(height=_CHAT_HEIGHT, border=False):
        # 1. Render the settled conversation history.
        render_chat(st.session_state.messages)

        # 2. If a question was submitted in the previous run, stream here.
        pending: str | None = st.session_state.get(_PENDING_KEY)
        if not pending:
            return

        # Consume the pending key immediately so a refresh or error won't
        # replay it.
        del st.session_state[_PENDING_KEY]

        try:
            with st.chat_message("user"):
                st.markdown(pending)

            with st.chat_message("assistant"):
                full_answer = st.write_stream(
                    stream_question(
                        session_id=st.session_state.session_id,
                        question=pending,
                    )
                )

            if full_answer:
                st.session_state.messages.append(
                    {"question": pending, "answer": str(full_answer)}
                )

        except ValueError as error:
            st.error(str(error))
            return
        except RuntimeError as error:
            st.error(str(error))
            return

        # Rerun so the completed exchange moves into render_chat and the
        # streaming bubble disappears cleanly.
        st.rerun()


def _render_composer() -> None:
    """Render the chat input below the conversation container.

    Because this widget sits outside the fixed-height container, it never
    gets pushed down as the conversation grows — the container absorbs all
    the height growth internally.

    On submission we store the question in session state and rerun so the
    next run can stream inside the conversation container.
    """
    question = st.chat_input("Ask a question about the uploaded files")
    if question:
        st.session_state[_PENDING_KEY] = question
        st.rerun()


# ---------------------------------------------------------------------------
# Right column — upload + document list + clear
# ---------------------------------------------------------------------------


def _render_document_panel() -> None:
    """Render the document management panel in the right column.

    Structure (top → bottom):
    - CSS flex-column injection so Clear Chat is always pinned to the bottom.
    - Upload header + file uploader widget  (always at the top, no scroll).
    - Upload confirmation button            (appears only when files are staged).
    - Attached document list:
        • Fewer than _DOCS_MAX_ROWS files → natural height, no wasted space.
        • _DOCS_MAX_ROWS or more files    → fixed-height scrollable container.
    - Invisible flex spacer               (pushes Clear Chat to the bottom).
    - Clear Chat button                   (always pinned at the bottom).

    The document list height is therefore content-driven first and only
    becomes scrollable once the content would exceed _DOCS_MAX_PX pixels.
    This matches the behaviour of Cursor / Claude Desktop file panels.
    """

    # ---- CSS: make the right column a flex column so Clear Chat stays
    #      pinned at the bottom regardless of how many files are attached.
    #      The spacer <div class="_doc-spacer"> below grows via flex:1.
    #      :has() is supported in all Streamlit-compatible browsers
    #      (Chrome 105+, Firefox 121+, Safari 15.4+).
    st.markdown(
        """
        <style>
        /* Right column (2nd column) → flex column, full height */
        section[data-testid="stMain"]
            .stHorizontalBlock
            > [data-testid="stColumn"]:last-child
            > [data-testid="stVerticalBlock"] {
            display: flex;
            flex-direction: column;
            height: 100%;
            min-height: 0;
        }
        /* The stElementContainer wrapping our spacer div grows to fill
           whatever space is left between the doc list and Clear Chat. */
        section[data-testid="stMain"]
            .stHorizontalBlock
            > [data-testid="stColumn"]:last-child
            > [data-testid="stVerticalBlock"]
            > [data-testid="stElementContainer"]:has(._doc-spacer) {
            flex: 1;
            min-height: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 📎 Attach Files")

    # ---- File uploader (always accessible at the top) ----------------
    uploaded_files = st.file_uploader(
        "Upload files",
        type=_ALLOWED_TYPES,
        label_visibility="collapsed",
        key=f"file_uploader_{st.session_state.uploader_key}",
        accept_multiple_files=True,
    )

    if uploaded_files:
        if st.button("⬆️ Upload", use_container_width=True):
            for uf in uploaded_files:
                try:
                    result = upload_file(
                        session_id=st.session_state.session_id,
                        uploaded_file=uf,
                    )
                    st.session_state.documents.append({
                        "document_id": result.get("document_id", ""),
                        "filename": uf.name,
                    })
                    st.success(f"✅ {uf.name}")
                except RuntimeError as error:
                    st.error(f"❌ {uf.name}: {error}")

            st.session_state.uploader_key += 1
            st.rerun()

    # ---- Attached document list (content-driven height) --------------
    docs = st.session_state.documents
    if docs:
        st.markdown("**Attached**")

        def _doc_rows() -> None:
            """Render one row per attached document."""
            for doc in docs:
                col_name, col_del = st.columns([0.82, 0.18])
                with col_name:
                    name = doc["filename"]
                    label = name if len(name) <= 20 else name[:17] + "…"
                    st.caption(label, help=name)
                with col_del:
                    if st.button(
                        "🗑",
                        key=f"del_{doc['document_id']}",
                        help=f"Remove {doc['filename']}",
                        use_container_width=True,
                    ):
                        try:
                            delete_document(doc["document_id"])
                            st.session_state.documents = [
                                d for d in st.session_state.documents
                                if d["document_id"] != doc["document_id"]
                            ]
                            st.rerun()
                        except RuntimeError as error:
                            st.error(str(error))

        if len(docs) >= _DOCS_MAX_ROWS:
            # Many files — use a fixed-height scrollable container so the
            # panel doesn't push the Clear Chat button off-screen.
            with st.container(height=_DOCS_MAX_PX, border=False):
                _doc_rows()
        else:
            # Few files — render at natural height; no reserved empty space.
            _doc_rows()

    # ---- Flex spacer: grows to fill space between list and button ----
    # The CSS rule above makes the stElementContainer wrapping this div
    # flex:1, so it absorbs all unused vertical space in the right column.
    st.markdown('<div class="_doc-spacer"></div>', unsafe_allow_html=True)

    # ---- Clear Chat (pinned at the bottom by the flex spacer above) --
    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True, type="secondary"):
        try:
            delete_session(st.session_state.session_id)
            st.session_state.messages = []
            st.session_state.pop(_PENDING_KEY, None)
            st.rerun()
        except RuntimeError as error:
            st.error(str(error))


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """Application entrypoint."""

    # set_page_config must be the very first Streamlit call.
    st.set_page_config(
        page_title="AI Coding Tutor",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialise_session()

    try:
        conversations = load_conversation_summaries()
    except RuntimeError:
        conversations = []

    render_sidebar(
        conversations=conversations,
        current_session_id=st.session_state.session_id,
        on_new_chat=start_new_chat,
        on_open_conversation=open_conversation,
    )

    col_chat, col_docs = st.columns([3, 1])

    with col_chat:
        # Fixed-height scrollable conversation area.
        # This is what prevents the page from growing — height is constant.
        _render_conversation_container()

        # Composer sits BELOW the container at a stable vertical position.
        _render_composer()

    with col_docs:
        _render_document_panel()


if __name__ == "__main__":
    main()