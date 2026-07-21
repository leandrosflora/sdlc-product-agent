from unittest.mock import patch

import pytest

from sdlc_product_agent.agent import ACTIONS, ROLE, UnknownActionError, execute
from sdlc_product_agent.authorization import AuthorizationResult


def test_role_is_set():
    assert ROLE == "product"


def test_project_read_is_always_a_known_action():
    assert "project.read" in ACTIONS


def test_execute_unknown_action_raises():
    with pytest.raises(UnknownActionError):
        execute("not.a.real.action", {})


def test_execute_denied_short_circuits_before_stub_handler():
    with patch(f"sdlc_product_agent.agent.check_authorization") as mock_check:
        mock_check.return_value = AuthorizationResult(allowed=False, action="project.read", raw={})
        result = execute("project.read", {"identity": {"agent_role": ROLE}})
    assert result.authorized is False
    assert result.implemented is False


def test_execute_allowed_runs_stub_handler():
    with patch(f"sdlc_product_agent.agent.check_authorization") as mock_check:
        mock_check.return_value = AuthorizationResult(allowed=True, action="project.read", raw={})
        result = execute("project.read", {"identity": {"agent_role": ROLE}})
    assert result.authorized is True
    assert result.implemented is False
    assert result.action == "project.read"
