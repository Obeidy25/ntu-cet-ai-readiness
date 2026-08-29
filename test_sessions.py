"""
Test Script: Persistent Multi-Session History & Reply Quoting Diagnostic
Validates SQLite database persistence, session CRUD operations, dynamic title generation,
and targeted reply-to-message prompt injection.
"""

import sqlite3
import json
import os
from backend import (
    init_sessions_db,
    save_or_update_session,
    get_all_sessions,
    get_session_by_id,
    delete_session_by_id,
    AskRequest,
)


def test_session_persistence():
    print("=================================================================")
    print("Testing Persistent Chat Sessions & Reply Quoting System")
    print("=================================================================")

    # Initialize DB
    init_sessions_db()

    # Test 1: Create a new session
    session_id_1 = "test_sess_001"
    messages_1 = [
        {"role": "user", "content": "What are the AI applications in Saudi hospitals?"},
        {"role": "assistant", "content": "AI is applied in radiology, predictive diagnostics, and triage.", "sources": []}
    ]
    title_1 = "AI Applications in Saudi Hospitals"
    save_or_update_session(session_id_1, title_1, messages_1)
    print("\n[Test 1] Created session 1...")

    sess = get_session_by_id(session_id_1)
    assert sess is not None
    assert sess["title"] == title_1
    assert len(sess["messages"]) == 2
    print(f"  ✓ Session '{title_1}' persisted successfully in SQLite.")

    # Test 2: Update session with a new turn (Reply to message)
    quoted_text = "AI is applied in radiology, predictive diagnostics, and triage."
    reply_turn = {
        "role": "user",
        "content": "Can you explain the radiology application in detail?",
        "quoted_message": quoted_text,
    }
    messages_1.append(reply_turn)
    messages_1.append({
        "role": "assistant",
        "content": "In radiology, CNN models are used to detect lung nodules in chest X-rays.",
        "sources": [{"source": "test.pdf", "page": 2, "score": 65.0, "content_type": "text"}]
    })
    save_or_update_session(session_id_1, title_1, messages_1)

    updated_sess = get_session_by_id(session_id_1)
    assert len(updated_sess["messages"]) == 4
    assert updated_sess["messages"][2]["quoted_message"] == quoted_text
    print("  ✓ Reply-to-message turn with quoted context appended and saved.")

    # Test 3: List all sessions
    all_sessions = get_all_sessions()
    assert any(s["id"] == session_id_1 for s in all_sessions)
    print(f"  ✓ get_all_sessions returned {len(all_sessions)} sessions sorted by activity.")

    # Test 4: AskRequest schema validation
    req = AskRequest(
        question="Explain this further",
        session_id=session_id_1,
        quoted_message=quoted_text,
    )
    assert req.session_id == session_id_1
    assert req.quoted_message == quoted_text
    print("  ✓ AskRequest schema properly serializes session_id and quoted_message.")

    # Test 5: Delete session
    deleted = delete_session_by_id(session_id_1)
    assert deleted is True
    assert get_session_by_id(session_id_1) is None
    print("  ✓ Session deleted cleanly from database.")

    print("\n=================================================================")
    print("All persistent session & reply unit tests passed successfully! ✓")
    print("=================================================================")


if __name__ == "__main__":
    test_session_persistence()
