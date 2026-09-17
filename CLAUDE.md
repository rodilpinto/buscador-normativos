# Buscador de Base Normativa

App web local que **constrói** o acervo de critério de uma ação de controle: tema →
palavras-chave → busca (fontes catalogadas + web aberta) → **triagem humana em poucas
decisões** → download → organização por tema → planilha-registro.

Nasceu do projeto "Auditoria Interna apoiada por IA" (Secin/Nuati), área `ai-com-ia` do repo
`~/Documents/projetos-nuati/`.

## Retomando o trabalho

- Rode **`/onboard-buscador`**. Estado: `SESSION-ONBOARD-buscador.md`.
- Feche cada chunk com `/checkpoint`.

## Onde as coisas estão

| Doc | Papel |
|---|---|
| `SESSION-ONBOARD-buscador.md` | estado, ponto de entrada |
| `docs/superpowers/specs/2026-09-16-consolidacao-buscador-design.md` | **spec vigente** |
| `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md` | **plano vigente** — ⛔ emendas no topo prevalecem sobre o corpo |
| `_TODO.md` · `_DECISOES-PENDENTES.md` · `log.md` | status · decisões · timeline |
| `LESSONS.md` · `BLOCKED-ON-RODRIGO.md` · `decisions/` | lições · pendências humanas · rodadas de decisão |
| ⛔ `docs/.../2026-09-08-*` · `spec/buscador/tasks/` | **superados** — histórico apenas |

## Arquitetura (consolidação de 2026-09-16)

- **Base: Streamlit**, não FastAPI. A decisão B2 de 08/09 foi **revertida** — ela escolheu FastAPI
  sem saber que o app `levantamento-normativos` já existia, com suíte verde e busca por API.
- **LLM por backend injetável:** OpenAI-compatível para o servidor local da Câmara, Gemini como
  alternativa, backend nulo como padrão inerte. Configuração por variável de ambiente.
- **O agrupamento semântico é ADITIVO:** nunca remove, oculta ou filtra item da visão do usuário.

## Convenções

- **Texto normativo NUNCA é parafraseado.** Título e ementa são copiados literalmente da
  fonte; texto derivado de LLM vai para campo separado (`ementa_llm`).
- **Procedência é obrigatória** em todo resultado: `catalogada` ou `web-aberta`.
- **O sistema roda inteiro sem LLM.** Nenhum caminho de código pode exigir chave de API.
- **Rastreabilidade é a essência**, não conveniência: fonte, URL, sha256, data da coleta,
  decisão humana e o motivo da pré-marcação ficam gravados — inclusive quando o humano
  divergiu da sugestão.
- **Separar fato de sugestão:** marcar `📝` o que for proposta não validada.
- Python 3.13, UTF-8 explícito em todo `open()`, rodar via **Bash** (não PowerShell).
- Acima de **260 caracteres** o Python falha em silêncio no Windows.
