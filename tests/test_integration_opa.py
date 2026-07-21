"""Real (non-mocked) authorization checks against the canonical OPA policy.

These only run when `opa` is on PATH and the sibling
agentic-sdlc-reference-architecture checkout is resolvable -- otherwise they are
skipped rather than failing CI environments that don't have that layout.
"""
from __future__ import annotations

import shutil

import pytest

from sdlc_product_agent import authorization

ROLE = "product"


def _integration_available() -> bool:
    if shutil.which("opa") is None:
        return False
    try:
        authorization._resolve_policy_path()
    except authorization.PolicyUnavailableError:
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _integration_available(), reason="opa CLI or sibling reference-architecture checkout not available"
)


def test_project_read_is_allowed_for_own_project():
    result = authorization.check_authorization(
        {
            "action": "project.read",
            "identity": {"agent_role": ROLE, "project_id": "example-project"},
            "resource": {"project_id": "example-project"},
        }
    )
    assert result.allowed is True


def test_project_read_is_denied_for_a_different_project():
    result = authorization.check_authorization(
        {
            "action": "project.read",
            "identity": {"agent_role": ROLE, "project_id": "example-project"},
            "resource": {"project_id": "other-project"},
        }
    )
    assert result.allowed is False
