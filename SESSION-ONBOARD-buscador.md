---
title: Buscador de Base Normativa — state snapshot
maintained_by: sessões do Claude Code; humanos podem editar
last_updated: 2026-09-22
related: [_TODO.md, _DECISOES-PENDENTES.md, log.md, LESSONS.md, BLOCKED-ON-RODRIGO.md, decisions/DECISIONS-LOG.md, docs/superpowers/specs/2026-09-16-consolidacao-buscador-design.md, docs/superpowers/plans/2026-09-16-consolidacao-fase1.md]
---

# Buscador de Base Normativa — onboarding de sessão

Ponto de entrada único. ≤ 1 página. Histórico em `log.md`; backlog em `_TODO.md`; decisões em
`_DECISOES-PENDENTES.md`; lições em `LESSONS.md`.

## 1. O que é (30s)

App web local que **constrói** o acervo de critério de uma ação de controle: tema →
palavras-chave → busca → **triagem em poucas decisões** → download → organização → planilha.

⚠ **Não confundir com o `wiki-chat`** (`projetos-nuati/wiki-chat/`): aquele **consome** acervo
pronto; este **constrói**. Projetos distintos, declarado pelo Rodrigo em 08/09 e reconfirmado no
board de 16/09 (decisão D-C2).

## 2. Estado na última pausa (2026-09-22, fim do dia)

🟢 **Frente 1 da v1.x fechada** (T3 merge → T1 golden-master → T2 runner). O código de A vive em
`levantamento-normativos/` **neste repo**, com história preservada; **repo A privado e arquivado**.
Nenhuma linha de produção mudou. Contagem atual de testes: `BASELINE` em `tools/run_all_tests.py`.

🟡 **Frente 2 (honestidade das fontes): spec e plano v4 prontos, revisados em 3 rodadas adversariais,
zero código.** É a próxima. Tudo está dobrado no corpo do plano — **não há seção de emendas a consultar**.

**Cadeia desta sessão:** `dc99d73` → `4f36080` (T3) → `97e61cc` → `d054d5b` (T1) → `e18dd4b` (T2) →
`b489d00` (spec) → `b1a6d3c` (plano v1) → `1e24933` (v2) → `46cdb0e` (v3) → `02dc620`/`a457e84` (v4) →
`f55488c`/`407b5a1` (ledgers, repo A) → commit deste checkpoint.
⚠ **O SHA mais novo listado aqui está SEMPRE um passo atrás do commit que gravou este arquivo** — a cadeia
real termina em `git log --oneline -3`.

**Working tree:** limpo na pausa; `master` = `origin/master`. Remoto `levantamento` (repo A local) segue
configurado; A está arquivado no GitHub. A tag `levantamento-v1-streamlit` existe aqui **e** no remoto de B.

**Ferramentas:** `python tools/run_all_tests.py` (≈9 min — as suítes LIVE batem em fontes quebradas) e
`python tools/golden_master.py comparar`. O app v1.0: `python -m streamlit run app.py` em
`levantamento-normativos/`.

## 3. Achados críticos (não perder)

1. **O projeto NÃO é greenfield.** O app `levantamento-normativos` existe desde março/2026 em
   `~/Documents/projeto-nuati-normativos-levantamento/`: **205 testes verdes** medidos em 16/09 (13+53+98+41),
   busca por API (LexML SRU/CQL, TCU Dados Abertos, Google CSE/DuckDuckGo). A spec de 08/09 dizia
   o contrário — a varredura dela não cobriu essa pasta. Detalhe em `LESSONS.md`.
2. **A decisão B2 foi REVERTIDA:** a base é o **Streamlit já escrito**, não um FastAPI novo.
3. **Precedência das emendas: C > B > A > corpo.** O plano da Fase 1 tem 3 rodadas de revisão
   adversarial; cada seção do corpo derrubada carrega um marcador `⛔` apontando a emenda.
4. **A ordem das tasks não é a numeração:** T3 → T1 → T2 → T4 → T5 → T6 → T7 → T8 → T9 (emenda A1).
5. **O agrupamento semântico é ADITIVO** — nunca remove, oculta ou filtra item da visão do
   usuário (requisito vinculante do Rodrigo, D-C1). Tem teste próprio; não "simplificar".
6. **Cobertura é requisito, não preferência:** medir a lacuna das fontes catalogadas contra um
   tema real **antes** de fechar o MVP.
7. **LLM local inalcançável desta máquina** (`10.10.111.125:1234`, timeout). Detalhe e a regra do
   `timeout` em tupla: `~/.claude/ENVIRONMENT.md`.
8. **As duas fontes catalogadas estão quebradas hoje (medido 22/09):** LexML `/busca/SRU` atrás de desafio
   de JavaScript do Senado (200 `text/html`; fallbacks 404; sem conserto legítimo → B-05); TCU
   `atonormativo` em 500 e, pior, a API de acórdãos **não devolve `ementa`/`numero`/`ano`** — o código lia
   só isso, então todo acórdão colapsa num id e nunca casa. Só a web aberta (DuckDuckGo; `GOOGLE_CSE_ID`
   vazio) traz resultado. A frente 2 conserta o que dá; detalhe em `LESSONS.md` (22/09).
9. **Fixture real do TCU** em `levantamento-normativos/tests/fixtures/tcu_acordaos_real.json`; o HTML real do
   desafio do Senado em `lexml_desafio_senado.html`. Fixtures de API são captura, não redação.

## 4. Ponto de restauração (rollback)

Tag anotada no repo A, **mensagem literal**: *"Estado pre-consolidacao: app Streamlit completo e
revisado (mar/2026)."* — ou seja, o estado **ANTES** da consolidação.
✅ Empurrada para o remoto em 16/09 (`git ls-remote --tags origin` confirma).

```bash
cd ~/Documents/projeto-nuati-normativos-levantamento && git checkout levantamento-v1-streamlit
```

## 5. Disciplina de trabalho

Um chunk = uma task do plano. Fechar cada chunk: rodar a suíte → golden-master → atualizar
duráveis → commitar **e pushar** (decisão D-C7). Retomar com `/onboard-buscador`.

## 6. Próximo movimento

**Executar o plano v4 da frente 2, a partir da T1**, em sessão nova. Primeiro passo agêntico, sem
depender de ninguém: abrir `docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md`, ler
"Global Constraints" + "Estrutura de arquivos" + **só a Task 1**, e despachar um subagente para a T1
(`superpowers:subagent-driven-development`), com o gate por task: `python tools/run_all_tests.py` verde
**e** `python tools/golden_master.py comparar` OK **e** push. ⚠ A regra do plano "se o observado divergir,
parar" vale para a diferença entre o **bloco de testes** e o observado — contar `def test_` antes de
suspeitar do código.

Decisões abertas que **não** travam: D-C9 (só volta na v2.0), D-C14 (deploy) e B-06. Ações do Rodrigo
pendentes: B-01, B-03, B-04, B-05, B-06 (`BLOCKED-ON-RODRIGO.md`).

## 7. Ponteiros

| Doc | Papel |
|---|---|
| `docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md` | **spec da frente 2** (próxima) |
| `docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md` | **plano v4 da frente 2** — tudo dobrado no corpo; ordem = numeração |
| `docs/superpowers/specs/2026-09-16-consolidacao-buscador-design.md` | spec da consolidação (arquitetura; vale) |
| `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md` | plano da Fase 1 — T3/T1/T2 **feitas**; T5/T6 viraram a frente 5; T4/T7/T8/T9 = **v2.0** (emendas no topo, D-C9) |
| `_TODO.md` · `_DECISOES-PENDENTES.md` · `log.md` | status · decisões · timeline |
| `LESSONS.md` · `BLOCKED-ON-RODRIGO.md` | lições transversais · o que espera o humano |
| `decisions/DECISIONS-LOG.md` + o board `.html` | as rodadas de decisão, com os comentários |
| ⛔ `docs/.../2026-09-08-*` e `spec/buscador/tasks/` | **SUPERADOS**, histórico apenas |

## 8. Fatos que não estão escritos em nenhum outro lugar

| | |
|---|---|
| **Repo B** (este) | `github.com/rodilpinto/buscador-normativos`, privado, branch **`master`** |
| **Repo A** (fundido) | `github.com/rodilpinto/levantamento-normativos` — **privado e ARQUIVADO em 22/09** (T9). Só leitura. A tag `levantamento-v1-streamlit` existe lá e aqui (`git ls-remote --tags origin`). |
| Caminho de A | `~/Documents/projeto-nuati-normativos-levantamento/` — ⚠ o código fica em `levantamento-normativos/` **dentro** dele, não na raiz |
| Cliente de LLM | `llm/gemini_client.py` (dentro de `llm/`, não na raiz) |
| Rodar o app | `python -m streamlit run app.py`, a partir da pasta do código |
| Acervo de consulta | `~/Documents/projetos-nuati/referencias/` |
| **Espelho na Câmara** | `git.camara.gov.br` **não é alcançável desta máquina**; é do PC do trabalho. Fluxo decidido em 22/09: este GitHub (B) é a origem → no PC do trabalho `git pull` + `git push camara master`. O push para B a cada task **continua**; a Câmara é espelho, nunca única cópia. Segredos fora do git nos dois lados. |
| Hospedagem / deploy | **nenhum** (verificado em 22/09: sem Dockerfile/Procfile/streamlit.app; só roda local). Único endereço de infra conhecido: o LM local `10.10.111.125:1234` (D-C5). Nenhuma org da Câmara visível no `gh` deste token (só `neuko-repo`). |

⚠ **Assimetria de branch:** A usa `main`, B usa `master`. No merge (T3) isso aparece como
`git fetch levantamento` + `levantamento/main`, enquanto o push daqui é `origin master`.

⚠ **`.claude/` é rastreado neste repo** (`.claude/commands/onboard-buscador.md`). Por isso **não**
entra no `.gitignore` unido da T3, embora estivesse no de A.

⚠ **Namespace `R1-*` tem dois significados:** no plano de 08/09 são as emendas de 2026-09-11; na
revisão de 16/09 os achados brutos foram numerados à parte. Diga sempre de qual documento.

⚠ **A mensagem da tag de rollback é imutável e cita `6.533 linhas`** — medição antiga, que omitia
`llm/__init__.py`. O valor correto é **6.561** (`git ls-files '*.py' | xargs wc -l`).

**Fechar a D-C9** quando respondida (só importa na v2.0): mover para 🟢 em `_DECISOES-PENDENTES.md` com a
data, abrir seção em `decisions/DECISIONS-LOG.md`, fechar `B-02` no `BLOCKED-ON-RODRIGO.md`.

## 9. Como atualizar este arquivo

Ao mudar de estado: atualize §2/§6, bump `last_updated`, acrescente entrada no `log.md`, atualize
os ledgers. Mantenha ≤ 1 página.
