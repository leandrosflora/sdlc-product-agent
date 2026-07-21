"""sdlc-product-agent: operational agent implementing agent_role == "product".

Skeleton stage: every action is authorization-checked against the canonical
OPA policy before it runs, but the actions themselves are stubs -- no LLM
call and no side effect yet. See README.md for the role's responsibility and
current policy scope.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from .authorization import AuthorizationResult, check_authorization

ROLE = "product"


@dataclass(frozen=True)
class ActionResult:
    action: str
    authorized: bool
    implemented: bool
    detail: str


class UnknownActionError(ValueError):
    """Raised when `execute` is called with an action outside ACTIONS."""


def _stub(action: str, description: str) -> Callable[[dict], ActionResult]:
    def handler(input_doc: dict) -> ActionResult:  # noqa: ARG001 - input reserved for future implementation
        return ActionResult(
            action=action,
            authorized=True,
            implemented=False,
            detail=f"'{action}' ({description}) is authorized but not yet implemented by the {ROLE} agent.",
        )

    return handler


# Action surface for this role, derived from the governance capability matrix
# (agentic-sdlc-reference-architecture/docs/governance.md). Not every action
# below is backed by a rule in agent_authorization.rego yet -- those will be
# denied by default-deny until the policy is extended. See README.md.
ACTIONS: Dict[str, Callable[[dict], ActionResult]] = {
    "project.read": _stub("project.read", "read the project's context and requirements"),
    "requirements.update": _stub("requirements.update", "update requirements and acceptance criteria (Definition gate)")
}


def authorize(input_doc: dict) -> AuthorizationResult:
    """Evaluate `input_doc` (with its own `action`) against the OPA policy."""
    return check_authorization(input_doc)


def execute(action: str, input_doc: dict) -> ActionResult:
    """Authorize `action` for `input_doc`, then run its stub handler if allowed."""
    if action not in ACTIONS:
        raise UnknownActionError(f"Unknown action '{action}' for {ROLE} agent. Known actions: {sorted(ACTIONS)}")
    auth = check_authorization({**input_doc, "action": action})
    if not auth.allowed:
        return ActionResult(action=action, authorized=False, implemented=False, detail="Denied by policy.")
    return ACTIONS[action](input_doc)
