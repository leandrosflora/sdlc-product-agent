import json
from types import SimpleNamespace

from sdlc_product_agent.github_issue import process_issue


def event():
    return {
        "issue": {
            "number": 42,
            "title": "Add idempotent payment endpoint",
            "body": "Retrying the same request must not duplicate a payment.",
            "html_url": "https://github.com/acme/payments/issues/42",
        },
        "repository": {"full_name": "acme/payments"},
    }


def allow(_):
    return SimpleNamespace(allowed=True)


def deny(_):
    return SimpleNamespace(allowed=False)


def test_issue_becomes_structured_criteria_comment_and_evidence(tmp_path):
    summary, comment = process_issue(
        event(), definitions_dir="agents", state_dir=tmp_path, authorize=allow,
    )
    assert summary["change_id"] == "CHG-0042"
    assert summary["project_id"] == "acme/payments"
    assert len(summary["acceptance_criteria"]) >= 3
    assert summary["evidence_refs"]
    assert summary["event_refs"]
    assert "<!-- agentic-sdlc-product-agent -->" in comment
    assert "- [ ]" in comment
    assert (tmp_path / "checkpoints" / "CHG-0042" / "product.json").is_file()


def test_policy_denial_stops_before_model(tmp_path):
    import pytest
    with pytest.raises(PermissionError):
        process_issue(event(), definitions_dir="agents", state_dir=tmp_path, authorize=deny)


def test_invalid_issue_is_rejected(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        process_issue({"issue": {}, "repository": {}}, definitions_dir="agents", state_dir=tmp_path, authorize=allow)
