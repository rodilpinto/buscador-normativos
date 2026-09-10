---
title: Buscador de Base Normativa - mapa de execução (split)
feature: buscador
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md
reference: spec/buscador/reference/global-constraints.md
last_updated: 2026-09-10
---

# Mapa de execução: 16 tasks, 5 ondas

> O **plano** segue fonte de verdade do *conteúdo* de cada task. Este arquivo é fonte de
> verdade do *ordenamento*. O status por task vive no `_TODO.md`, não aqui.
> Os arquivos em `tasks/` são cópia verbatim do plano, para o agente de build não ler 2641 linhas.

## O que cada task entrega

| # | Arquivo | Entrega |
|---|---|---|
| 1 | `tasks/01-foundation.md` | esqueleto do repo, `Config`, `carregar_config` |
| 2 | `tasks/02-sqlite-db.md` | schema SQLite (`buscas`, `resultados`, `arquivos`, `resultado_arquivo`) |
| 3 | `tasks/03-models-normalize.md` | `Resultado`, `normalizar_url/titulo`, `chave_dedup` |
| 4 | `tasks/04-source-protocol.md` | protocolo `Fonte`, `FonteFake`, `CATALOGO` |
| 5 | `tasks/05-planalto-adapter.md` | `FontePlanalto` (`buscar` + `extrair`) |
| 6 | `tasks/06-legin-tcu-adapters.md` | `FonteLegin`, `FonteTCU` |
| 7 | `tasks/07-open-web-source.md` | `FonteWebAberta` (provedor por injeção) |
| 8 | `tasks/08-keywords.md` | protocolo `LLM`, `NullLLM`, `expandir` |
| 9 | `tasks/09-archive-index.md` | índice sha256 do acervo, selo já-tenho (M1) |
| 10 | `tasks/10-premarking.md` | pré-marcação com justificativa (M3 + M4) |
| 11 | `tasks/11-search-orchestrator.md` | `executar_busca`, resiliente a fonte quebrada |
| 12 | `tasks/12-download-organize.md` | download, dedup sha256, pasta por tema, `caminho_longo` |
| 13 | `tasks/13-registry-spreadsheet.md` | planilha-registro (11 colunas + 6 de rastreabilidade) |
| 14 | `tasks/14-triage-page.md` | página de triagem e ações de grupo (M2) |
| 15 | `tasks/15-web-flow.md` | fluxo web: nova busca, aplicar download |
| 16 | `tasks/16-cli-sources-readme.md` | CLI, registro das fontes reais, README |

## Grafo de dependências

```
T1 config
 └─► T3 modelos/normalizar          (T3 não consome nada, mas precisa do pacote da T1)
      │
      ├──────────────┬──────────────┬──────────────┐
      ▼              ▼              ▼              ▼
  A: T2 db      B: T4 Fonte     C: T8 llm     D: T9 acervo
      │              │           palavras         │
      ▼              ├─► T5 Planalto              ▼
     T13 planilha    ├─► T6 Legin+TCU         T10 premarcação
                     └─► T7 web aberta
      └──────────────┴──────────────┴──────────────┘
                          ▼
              T11 orquestrador  ∥  T12 download
                          ▼
                  T14 triagem ─► T15 fluxo web     (mesmo app.py: serializado)
                          ▼
                      T16 CLI + README
```

## Ondas e trilhas

| Onda | Trilhas | Tasks | Paralelismo |
|---|---|---|---|
| 1 | Gate | T1 → T3 | nenhum (sequencial) |
| 2 | A dados · B fontes · C llm · D triagem-core | A: T2→T13 · B: T4→[T5 ∥ T6 ∥ T7] · C: T8 · D: T9→T10 | 4 trilhas |
| 3 | E núcleo | T11 ∥ T12 | 2 tasks |
| 4 | F web | T14 → T15 | nenhum (colisão em `app.py`) |
| 5 | G fechamento | T16 | nenhum |

**Por que T3 está no gate e não na trilha B:** `Resultado` e `normalizar_titulo` são consumidos
por T4, T9 e T10, ou seja, por três das quatro trilhas da onda 2. Deixar T3 dentro de uma
trilha faria as outras esperarem por ela de qualquer forma.

## Checagem mecânica de colisão de arquivos

Listas de arquivos tocados, por trilha da onda 2 (a única com paralelismo largo):

| Trilha | Arquivos |
|---|---|
| A | `buscador/db.py`, `buscador/planilha.py`, `tests/test_db.py`, `tests/test_planilha.py` |
| B | `buscador/fontes/{base,planalto,legin_camara,tcu,web_aberta}.py`, `tests/fixtures/{planalto,legin,tcu}_busca.html`, `tests/test_fontes_base.py`, `tests/test_fonte_{planalto,legin,tcu,web_aberta}.py` |
| C | `buscador/llm.py`, `buscador/palavras_chave.py`, `tests/test_palavras_chave.py` |
| D | `buscador/acervo.py`, `buscador/premarcacao.py`, `tests/test_acervo.py`, `tests/test_premarcacao.py` |

**Interseção: vazia.** As quatro trilhas podem rodar ao mesmo tempo.

Onda 3: T11 = `buscador/busca.py` + teste; T12 = `buscador/download.py` + teste. Interseção vazia.

**Duas colisões encontradas, ambas já serializadas:**

1. `buscador/web/app.py` - T14 cria, T15 modifica. Ficam na mesma trilha (F), nesta ordem.
   Nunca podem rodar em paralelo, apesar de tocarem rotas diferentes.
2. `README.md` - T1 e T16 listam as duas como **Create** (ver ambiguidade 1 abaixo).
   Ondas 1 e 5, então não há risco concorrente, mas T16 vai sobrescrever o arquivo da T1.

## Ambiguidades do plano (registradas, NÃO resolvidas)

Achadas na extração. Nenhuma foi preenchida com invenção; vão para o agente de build como pergunta.

1. **`README.md` criado duas vezes.** T1 lista `README.md` em "Create" e T16 também, em vez de
   "Modify". O plano não diz se a T16 sobrescreve ou complementa. 📝 Sugestão minha, não
   validada: T1 cria um README mínimo de 5 linhas e T16 o reescreve inteiro; mas quem decide
   é o humano ou o conteúdo literal das tasks.
2. **T14 e T15 no mesmo `app.py`** sem instrução de reconciliação de rotas, apenas a ordem
   sequencial. A serialização da onda 4 cobre isso.
3. **T6 cobre duas fontes** (Legin e TCU) e dois arquivos de teste numa task única. É como o
   plano escreveu; não dividi.
4. Cada arquivo de task termina no separador `---` herdado do plano. Cosmético.

## Travas externas (decisões, não código)

- **D-B2** (rotas e seletores CSS supostos): não trava escrever T5/T6, trava **confiar** nelas.
  Enquanto não houver página real salva, `extrair()` está verificado e `buscar()` não.
- **D-B1** (provedor da web aberta): não trava T7, que recebe a função por injeção. Trava rodar
  contra a web real.

Ver `_DECISOES-PENDENTES.md`.
