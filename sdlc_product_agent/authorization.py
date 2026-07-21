"""OPA-backed authorization check against the agentic-sdlc-reference-architecture policy.

This module shells out to the `opa` CLI so the canonical rego in
agentic-sdlc-reference-architecture/policies/agent_authorization.rego stays the
single source of truth for authorization -- nothing here re-implements policy
logic.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

POLICY_QUERY = "data.agentic_sdlc.authorization.allow"
POLICY_ENV_VAR = "SDLC_POLICY_PATH"
DEFAULT_POLICY_RELATIVE_PATH = (
    Path("..") / "agentic-sdlc-reference-architecture" / "policies" / "agent_authorization.rego"
)


class PolicyUnavailableError(RuntimeError):
    """Raised when the OPA policy cannot be evaluated (missing `opa` binary or policy file)."""


@dataclass(frozen=True)
class AuthorizationResult:
    allowed: bool
    action: str
    raw: dict


def _resolve_policy_path() -> Path:
    configured = os.environ.get(POLICY_ENV_VAR)
    path = Path(configured) if configured else (Path(__file__).resolve().parents[1] / DEFAULT_POLICY_RELATIVE_PATH)
    if not path.is_file():
        raise PolicyUnavailableError(
            f"Policy file not found at '{path}'. Set {POLICY_ENV_VAR} to the path of "
            "agentic-sdlc-reference-architecture/policies/agent_authorization.rego, or check "
            "out that repo as a sibling of this one."
        )
    return path


def check_authorization(input_doc: dict) -> AuthorizationResult:
    """Evaluate `input_doc` against the canonical OPA policy via the `opa` CLI."""
    opa_bin = shutil.which("opa")
    if not opa_bin:
        raise PolicyUnavailableError(
            "The 'opa' CLI was not found on PATH. Install it from "
            "https://www.openpolicyagent.org/docs/latest/#running-opa to evaluate authorization."
        )
    policy_path = _resolve_policy_path()

    fd, tmp_path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(input_doc, tmp)
        try:
            result = subprocess.run(
                [opa_bin, "eval", "--format", "json", "--data", str(policy_path), "--input", tmp_path, POLICY_QUERY],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise PolicyUnavailableError(f"`opa eval` failed: {exc.stderr or exc.stdout}") from exc
    finally:
        os.unlink(tmp_path)

    parsed = json.loads(result.stdout)
    try:
        allowed = bool(parsed["result"][0]["expressions"][0]["value"])
    except (KeyError, IndexError, TypeError) as exc:
        raise PolicyUnavailableError(f"Unexpected `opa eval` output: {result.stdout}") from exc
    return AuthorizationResult(allowed=allowed, action=input_doc.get("action", ""), raw=parsed)
