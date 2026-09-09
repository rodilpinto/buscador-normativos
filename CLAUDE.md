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
| `docs/superpowers/specs/2026-09-08-buscador-normativos-design.md` | spec: princípio, decisões B1-B5, riscos |
| `docs/superpowers/plans/2026-09-08-buscador-normativos.md` | plano: 16 tasks com TDD |
| `_TODO.md` · `_DECISOES-PENDENTES.md` · `log.md` | ledgers e timeline |

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
