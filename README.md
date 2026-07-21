# SDLC Product Agent

Primeiro agente funcional da [Agentic SDLC Reference Architecture](https://github.com/leandrosflora/agentic-sdlc-reference-architecture), executado pelo [Agentic SDLC Runtime](https://github.com/leandrosflora/agentic-sdlc-runtime).

## Fluxo implementado

~~~text
GitHub Issue
→ autorização OPA requirements.update
→ Context Builder
→ Product Agent
→ critérios de aceite estruturados
→ comentário idempotente no Issue
→ event + evidence bundle
~~~

## Comportamento

Ao abrir ou editar um Issue, o workflow Product Agent:

1. valida título, corpo, número e repositório;
2. cria um change_id determinístico;
3. consulta a policy canônica pelo OPA;
4. trata o conteúdo do Issue como contexto não confiável;
5. usa o Model Gateway configurado ou o modelo fake;
6. exige acceptance_criteria como lista não vazia;
7. publica checklist no Issue;
8. persiste contexto, saída, evento e checkpoint;
9. publica o evidence bundle como artifact por 90 dias.

O comentário contém um marker e é atualizado em novas execuções, evitando duplicação.

## Model Gateway

Sem secrets, o workflow usa o Fake Model Gateway determinístico. Para usar um endpoint OpenAI-compatible, configure no repositório:

- MODEL_BASE_URL
- MODEL_API_KEY
- MODEL_NAME

As credenciais não entram no prompt nem nas evidências.

## Execução manual

O workflow também aceita workflow_dispatch com o número de um Issue existente.

Localmente:

~~~bash
pip install -e ".[dev]"
python -m sdlc_product_agent.github_issue \
  --event event.json \
  --summary product-agent-summary.json \
  --comment product-agent-comment.md
~~~

É necessário ter OPA no PATH e definir SDLC_POLICY_PATH para a policy canônica.

A dependência `agentic-sdlc-runtime` é instalada da tag versionada no GitHub. Para
desenvolver contra o checkout irmão local em vez da tag:

~~~bash
pip install -e ../agentic-sdlc-runtime
~~~

## Autorização

- project.read: próprio project_id;
- requirements.update: Product Agent, mesmo project_id e risco R0/R1;
- sem escrita em código, arquitetura ou produção.

## Evidências

~~~text
.runtime/
├── checkpoints/<change_id>/product.json
├── evidence/<change_id>/<run_id>/
└── events/<change_id>/
~~~

## Referências

- [Runtime compartilhado](https://github.com/leandrosflora/agentic-sdlc-runtime)
- [Governança](https://github.com/leandrosflora/agentic-sdlc-reference-architecture/blob/main/docs/governance.md)
- [Policy OPA](https://github.com/leandrosflora/agentic-sdlc-reference-architecture/blob/main/policies/agent_authorization.rego)
