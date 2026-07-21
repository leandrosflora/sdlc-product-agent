# sdlc-product-agent

Agente `product` do [agentic-sdlc-reference-architecture](https://github.com/leandrosflora/agentic-sdlc-reference-architecture) — implementação operacional do papel `agent_role == "product"` definido em `policies/agent_authorization.rego`.

## Responsabilidade

Define e mantém requisitos e critérios de aceitação verificáveis; dono do **Definition gate** (requisito, critérios verificáveis, owner, dados, risco e `change_id`).

## Autorização (OPA)

- `project.read`: permitido, restrito ao próprio `project_id`.
- Alteração de requisitos: prevista na matriz de capacidades do governance; ainda não codificada como regra própria em `agent_authorization.rego` (hoje só `project.read` é avaliado para este papel).
- Sem permissão para escrever código de aplicação, alterar arquitetura/contratos ou acionar deploy.

## Status

Scaffold inicial (Python/.pyproj). Lógica do agente ainda não implementada.

## Referências

- Governança e gates: [docs/governance.md](https://github.com/leandrosflora/agentic-sdlc-reference-architecture/blob/main/docs/governance.md)
- Política: [policies/agent_authorization.rego](https://github.com/leandrosflora/agentic-sdlc-reference-architecture/blob/main/policies/agent_authorization.rego)
