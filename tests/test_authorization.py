import json
import subprocess

import pytest

from sdlc_product_agent import authorization


def test_check_authorization_raises_when_opa_missing(monkeypatch):
    monkeypatch.setattr(authorization.shutil, "which", lambda _name: None)
    with pytest.raises(authorization.PolicyUnavailableError, match="opa"):
        authorization.check_authorization({"action": "project.read"})


def test_resolve_policy_path_raises_when_file_missing(monkeypatch, tmp_path):
    monkeypatch.setenv(authorization.POLICY_ENV_VAR, str(tmp_path / "does-not-exist.rego"))
    with pytest.raises(authorization.PolicyUnavailableError, match="Policy file not found"):
        authorization._resolve_policy_path()


def test_resolve_policy_path_honors_env_var(monkeypatch, tmp_path):
    policy_file = tmp_path / "agent_authorization.rego"
    policy_file.write_text("package agentic_sdlc.authorization\n\ndefault allow := false\n")
    monkeypatch.setenv(authorization.POLICY_ENV_VAR, str(policy_file))
    assert authorization._resolve_policy_path() == policy_file


def test_check_authorization_parses_opa_eval_output(monkeypatch, tmp_path):
    policy_file = tmp_path / "agent_authorization.rego"
    policy_file.write_text("package agentic_sdlc.authorization\n\ndefault allow := false\n")
    monkeypatch.setenv(authorization.POLICY_ENV_VAR, str(policy_file))
    monkeypatch.setattr(authorization.shutil, "which", lambda _name: "/usr/bin/opa")

    fake_stdout = json.dumps({"result": [{"expressions": [{"value": True}]}]})

    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=fake_stdout, stderr="")

    monkeypatch.setattr(authorization.subprocess, "run", fake_run)

    result = authorization.check_authorization({"action": "project.read"})
    assert result.allowed is True
    assert result.action == "project.read"
