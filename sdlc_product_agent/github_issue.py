from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from agentic_sdlc_runtime.mcp import FakeMCPGateway
from agentic_sdlc_runtime.model_gateway import FakeModelGateway, OpenAICompatibleGateway
from agentic_sdlc_runtime.models import ContextSource, ModelResponse, RunRequest
from agentic_sdlc_runtime.runtime import AgentRuntime

from .authorization import check_authorization


def _issue(event: dict) -> dict:
    issue = event.get("issue") or {}
    repository = event.get("repository") or {}
    if not isinstance(issue.get("number"), int) or not issue.get("title"):
        raise ValueError("event must contain issue.number and issue.title")
    return {
        "number": issue["number"],
        "title": issue["title"].strip(),
        "body": (issue.get("body") or "").strip(),
        "url": issue.get("html_url", ""),
        "repository": repository.get("full_name", "unknown/repository"),
    }


def _fake_response(issue: dict) -> ModelResponse:
    title = issue["title"]
    criteria = [
        f"Given the current system, when '{title}' is delivered, then the requested behavior is demonstrable end to end.",
        "Automated tests cover the successful path and relevant validation failures.",
        "Existing documented behavior remains compatible or the breaking change is explicitly approved.",
        "Operational evidence identifies the change, execution result and acceptance status.",
    ]
    content = json.dumps({"acceptance_criteria": criteria, "assumptions": [], "risk": "R1"})
    return ModelResponse(content=content, input_tokens=0, output_tokens=len(content) // 4, model="fake-product-v1")


def _validate_output(payload: dict) -> dict:
    criteria = payload.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria or not all(isinstance(item, str) and item.strip() for item in criteria):
        raise ValueError("model output requires a non-empty acceptance_criteria string array")
    risk = payload.get("risk", "R1")
    if risk not in {"R0", "R1"}:
        raise ValueError("product agent may only classify autonomous output as R0 or R1")
    return {
        "acceptance_criteria": [item.strip() for item in criteria],
        "assumptions": [str(item).strip() for item in payload.get("assumptions", []) if str(item).strip()],
        "risk": risk,
    }


def process_issue(event: dict, *, definitions_dir: str | Path, state_dir: str | Path,
                  authorize: Callable[[dict], object] = check_authorization) -> tuple[dict, str]:
    issue = _issue(event)
    project_id = issue["repository"]
    change_id = f"CHG-{issue['number']:04d}"
    decision = authorize({
        "action": "requirements.update",
        "identity": {"agent_role": "product", "project_id": project_id},
        "resource": {"project_id": project_id},
        "change": {"risk": "R1"},
    })
    if not decision.allowed:
        raise PermissionError("requirements.update denied by policy")

    if os.environ.get("MODEL_API_KEY") and os.environ.get("MODEL_NAME"):
        gateway = OpenAICompatibleGateway()
    else:
        gateway = FakeModelGateway([_fake_response(issue)])

    runtime = AgentRuntime(
        definitions_dir=definitions_dir, state_dir=state_dir,
        model_gateway=gateway, mcp_gateway=FakeMCPGateway(),
    )
    result = runtime.run(RunRequest(
        agent_role="product", project_id=project_id, change_id=change_id,
        objective=f"Refine GitHub Issue #{issue['number']}: {issue['title']}",
        acceptance_criteria=["criteria are independently testable", "assumptions are explicit"],
        sources=[ContextSource(
            uri=issue["url"] or f"github://{project_id}/issues/{issue['number']}",
            content=json.dumps({"title": issue["title"], "body": issue["body"]}, ensure_ascii=False),
            classification="internal", trusted=False,
        )],
        input_data={"task": "refine_issue", "issue": issue},
    ))
    normalized = _validate_output(result.output["result"])
    summary = {
        "schema_version": "1.0", "change_id": change_id, "project_id": project_id,
        "issue_number": issue["number"], "issue_url": issue["url"],
        "agent": "product", "agent_run_id": result.run_id,
        **normalized, "evidence_refs": result.evidence_refs, "event_refs": result.event_refs,
    }
    checks = "\n".join(f"- [ ] {item}" for item in normalized["acceptance_criteria"])
    assumptions = "\n".join(f"- {item}" for item in normalized["assumptions"]) or "- Nenhuma; validar com o owner."
    comment = f"""<!-- agentic-sdlc-product-agent -->
## Product Agent · Critérios de aceite

**Change:** {change_id} · **Risco inicial:** {normalized['risk']}

{checks}

### Premissas

{assumptions}

<sub>Execução {result.run_id} · evidence bundle disponível no artifact do workflow.</sub>
"""
    return summary, comment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--definitions", default="agents")
    parser.add_argument("--state", default=".runtime")
    parser.add_argument("--summary", default="product-agent-summary.json")
    parser.add_argument("--comment", default="product-agent-comment.md")
    args = parser.parse_args()
    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    summary, comment = process_issue(event, definitions_dir=args.definitions, state_dir=args.state)
    Path(args.summary).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.comment).write_text(comment, encoding="utf-8")


if __name__ == "__main__":
    main()
