"""Pytest-based tests for the Enhanced Session Continuity System.

These tests validate the lifecycle of a session including creation,
activity logging, resumption, termination, and resumption after termination.

The original test script relied on prints and manual summaries. This version
uses ``assert`` statements so pytest can directly determine pass/fail states.

The tests require the ``knowledge_server`` module. If it is unavailable, all
tests in this file will be skipped.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

import pytest
import pytest_asyncio

# Ensure the MCP Knowledge Server is importable
sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "services", "mcp-knowledge-server", "src")
)

try:  # pragma: no cover - import failure handled via pytest skip
    from knowledge_server import (
        resume_session,
        end_session,
        log_conversation_message,
        log_claude_action,
    )
    KNOWLEDGE_SERVER_AVAILABLE = True
except Exception:  # ModuleNotFoundError is the common case
    resume_session = end_session = log_conversation_message = log_claude_action = None  # type: ignore
    KNOWLEDGE_SERVER_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not KNOWLEDGE_SERVER_AVAILABLE, reason="knowledge_server module not available"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="module")
async def initial_session_result() -> Dict[str, Any]:
    """Start a fresh session and return the complete result."""

    return await resume_session(
        project="test-project", quick_summary=True, auto_initialize=True
    )


@pytest.fixture(scope="module")
def session_id(initial_session_result: Dict[str, Any]) -> str:
    """Extract the session identifier from the initial session result."""

    return initial_session_result.get("new_session", {}).get("session_id")


@pytest_asyncio.fixture(scope="module")
async def session_activity(session_id: str) -> Dict[str, Any]:
    """Log a conversation message and several actions for the session."""

    msg_result = await log_conversation_message(
        session_id=session_id,
        message_type="user_message",
        content="Test message for session continuity testing",
        context={"test_mode": True},
    )

    test_actions = [
        ("file_edit", "Edited test file for continuity testing", ["test_file.py"], True),
        ("command", "Ran test command", [], True),
        ("config_change", "Modified test configuration", ["config.json"], False),
        ("session_test", "Session continuity test action", [], True),
    ]

    action_results: List[Dict[str, Any]] = []
    for action_type, description, files, success in test_actions:
        action_result = await log_claude_action(
            session_id=session_id,
            action_type=action_type,
            description=description,
            files_affected=files,
            success=success,
        )
        action_results.append(action_result)

    return {"message": msg_result, "actions": action_results}


@pytest_asyncio.fixture(scope="module")
async def terminated_session(session_id: str, session_activity: Dict[str, Any]) -> Dict[str, Any]:
    """Terminate the session after activity has been logged."""

    return await end_session(
        session_id=session_id,
        reason="test_completion",
        completion_timeout=10,
        prepare_resume=True,
        export_context=True,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fresh_session_start(initial_session_result: Dict[str, Any], session_id: str) -> None:
    """Verify a new session is created when none exists."""

    assert initial_session_result.get("status") == "fresh_start"
    assert session_id is not None


@pytest.mark.asyncio
async def test_session_with_activity(session_activity: Dict[str, Any]) -> None:
    """Ensure messages and actions are logged correctly."""

    msg = session_activity["message"]
    actions = session_activity["actions"]

    assert msg.get("status") == "logged"
    assert all(action.get("status") == "logged" for action in actions)
    assert len(actions) == 4


@pytest.mark.asyncio
async def test_session_resumption(session_id: str, session_activity: Dict[str, Any]) -> None:
    """Resume the session and validate returned context and guidance."""

    result = await resume_session(
        project="test-project", quick_summary=False, auto_initialize=True
    )

    assert result.get("status") == "session_resumed"
    previous_session = result.get("previous_session", {})
    assert previous_session.get("session_id") == session_id

    guidance = result.get("continuation_guidance", {})
    assert guidance.get("next_steps")
    assert guidance.get("recommendations")


@pytest.mark.asyncio
async def test_session_termination(terminated_session: Dict[str, Any]) -> None:
    """Confirm sessions terminate cleanly and persist data."""

    assert terminated_session.get("status") == "session_ended"

    persistence = terminated_session.get("data_persistence", {})
    assert persistence.get("context_exported") is True
    assert persistence.get("resume_prepared") is True
    assert persistence.get("database_updated") is True

    summary = terminated_session.get("session_summary", {})
    assert "total_actions" in summary


@pytest.mark.asyncio
async def test_resume_after_termination(session_id: str, terminated_session: Dict[str, Any]) -> None:
    """Ensure the system can resume from the last terminated session."""

    result = await resume_session(
        project="test-project", quick_summary=True, auto_initialize=True
    )

    assert result.get("status") == "session_resumed"
    previous_session = result.get("previous_session", {})
    assert previous_session.get("session_id") == session_id

