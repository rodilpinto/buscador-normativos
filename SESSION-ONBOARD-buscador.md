---
title: Buscador de Base Normativa — state snapshot
maintained_by: sessões do Claude Code; humanos podem editar
last_updated: 2026-09-23
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

## 2. Estado na última pausa (2026-09-23, frente 2 fechada — T10)

🟢 **Frente 1 da v1.x fechada** (T3 merge → T1 golden-master → T2 runner). O código de A vive em
`levantamento-normativos/` **neste repo**, com história preservada; **repo A privado e arquivado**.
Nenhuma linha de produção mudou **na frente 1** (a frente 2 muda — ver abaixo). Contagem atual de testes: `BASELINE` em `tools/run_all_tests.py`.

🟢 **Noite de 22/09 — app na nuvem funcional:** `https://buscador-normativos.streamlit.app/` (privado), IA gerando
palavras-chave (chave `nuati.secin`, modelo `gemini-3.5-flash-lite`). Ponto de retorno: tag **`v1.0.1`**. A nuvem
segue a branch **`deploy`** (congelada em `v1.0.1`); o trabalho segue em `master`. Detalhe em §4 e §8.

✅ **Frente 2 (honestidade das fontes) FECHADA em 23/09 (T10).** As fontes declaram por que não responderam
(`motivo`/`detalhe`/`parcial`); o TCU lê o esquema real do acórdão; a nota diz de onde veio; tela e planilha separam
indisponível, parcial e sem resultado. Executada por agentes (D-C16): T1–T9 → revisão final de 5 lentes → FIX-FONTES
(`7322cc0`) + FIX-SAÍDA (`51883f6`) → T10. Critérios §7 conferidos: runner **336 TUDO VERDE**, golden OK,
`dedup_esperado.json` = `d054d5b`, **V11 7/7**. Registro completo: `spec/frente2-honestidade-fontes/execucao/` (TODOS =
SSOT, INSIGHTS, `revisoes/`) e `implementacao/10-fechar-frente.md` (comandos e saídas). ⚠ Fechou com a 🔴 **D-C17 aberta**.
Os worktrees `../bn-*` guardam screenshots de evidência (não versionados); a limpeza deles é o último passo da fase 5
(`execucao/TODOS.md`).

**Cadeia:** `git log --oneline --reverse 1c063ea..HEAD` (frente 2 inteira; não é restatada aqui). Marcos: `da543be` T1 ·
`9e259ca` trilha B · `08d9d8c` trilha A · `d4cab80` T9 · `7322cc0`/`51883f6` consertos da revisão final. ⚠ O SHA mais
novo listado aqui está SEMPRE um passo atrás do commit que gravou este arquivo; a cadeia real termina em `git log --oneline -3`.

**Working tree (`master`):** limpo no checkpoint; `master` = `origin/master`. Remoto `levantamento` (repo A local) segue
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
3. **(Plano de 16/09 apenas — v2.0)** Precedência das emendas: C > B > A > corpo; cada seção do corpo
   derrubada carrega um marcador `⛔` apontando a emenda. **O plano da frente 2 não tem isso: está dobrado.**
4. **(Plano de 16/09 apenas)** A ordem das tasks não é a numeração (emenda A1). No plano da frente 2,
   **ordem = numeração**.
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

**Pontos de retorno neste repo (22/09, empurrados):** `v1.0` → `eb91277` (= `levantamento-v1-streamlit`) ·
**`v1.0.1`** → `e2cd56a`: estado **funcional** (IA na nuvem confirmada pelo Rodrigo), com LexML/TCU ainda quebrados.
`git checkout v1.0.1`. O app da nuvem segue a **branch `deploy`** (criada em 22/09 = `v1.0.1`), não tag: voltar o app =
`git push -f origin <tag>:deploy` (**só com ok do Rodrigo**).

## 5. Disciplina de trabalho

Um chunk = uma task do plano. Fechar cada chunk: rodar a suíte → golden-master → atualizar
duráveis → commitar **e pushar** (decisão D-C7). Retomar com `/onboard-buscador`.

## 6. Próximo movimento

▶ **Frente 5 (LM local)** — a próxima pela ordem D-C11 (1 → 2 → **5** → 3 → 4). A spec **não está escrita**. O primeiro
passo é o desenho (brainstorm → spec → plano), a partir dos insumos (a)–(g) da linha da frente 5 no `_TODO.md`. Entre eles:
backend por ambiente, endpoint OpenAI-compatível do Gemini, **`st.secrets` vencendo a variável vazia do runner**, chave lida
só no import e `ementa None` com LLM ligado. ⚠ As chaves de LLM estão definidas no ambiente desta máquina: app lançado à mão
usa `env -u GEMINI_API_KEY -u GOOGLE_API_KEY -u OPENAI_API_KEY` (`~/.claude/ENVIRONMENT.md`).
**Antes disso**, se ainda estiver aberto em `spec/frente2-honestidade-fontes/execucao/TODOS.md`, feche a fase 5 da frente 2:
`/checkpoint` e limpeza dos worktrees, pela receita que está lá.

🔴 **D-C17 aberta e declarada** (dedup fuzzy funde acórdãos distintos: 26 de 900 numa amostra real; perda silenciosa).
Opções `a` / `a'` / `b` / `c` em `_DECISOES-PENDENTES.md`. Qualquer escolha vira **task própria** no passo fuzzy de
`deduplicator.py`, com golden conferido e fixture real. A revisão final de spec pede que não passe do início da frente 5.
📝 Sugestão minha: perguntar ao Rodrigo na abertura da próxima sessão.

Decisões abertas que **não** travam: D-C9 (só volta na v2.0), D-C14 (deploy). (D-C10.1 fechada em 22/09: tags só nos
marcos.) ⛔ **Não avançar a branch `deploy`**: só num marco, com ok do Rodrigo (`git push origin master:deploy`). O fim da
frente 2 **não** é autorização. Ações do Rodrigo pendentes: B-01 a B-06 (`BLOCKED-ON-RODRIGO.md`). O B-04 (medir a lacuna
de cobertura) ganhou as medições da frente 2.

## 7. Ponteiros

| Doc | Papel |
|---|---|
| `docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md` | **spec da frente 2** (em execução) |
| `docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md` | **plano v4 da frente 2** — tudo dobrado no corpo; ordem = numeração; **fonte de verdade** |
| `spec/frente2-honestidade-fontes/` | **split do plano v4** (22/09, D-C16): `00-overview.md` (5 fases, dependências) + `tasks/01..10` (verbatim + critérios de aceite) + `reference/` — é o que o subagente lê |
| `docs/superpowers/specs/2026-09-16-consolidacao-buscador-design.md` | spec da consolidação (arquitetura; vale) |
| `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md` | plano da Fase 1 — T3/T1/T2/T9 **feitas**; T5/T6 viraram a frente 5; T4/T7/T8 = **v2.0** (emendas no topo, D-C9) |
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
| **Chave do LLM no app da nuvem** | Chave Gemini do projeto Google **`nuati.secin`**, gravada pelo Rodrigo em 22/09 nos *Secrets* do app `buscador-normativos` (share.streamlit.io) — **o valor nunca passa pelo chat nem pelo repo**. O v1.0 só lê o segredo **`GEMINI_API_KEY`** (`llm/gemini_client.py:58`, SDK `google-genai`, modelo **`gemini-3.5-flash-lite`** desde 22/09 — o `2.5-flash-lite` dá 404 para chave nova). ⚠ O segredo só é lido **no import do módulo**: depois de mudar Secrets, **Reboot app**. O app antigo `levantamento-normativos.streamlit.app` foi **apagado** pelo Rodrigo em 22/09. ⛔ **Não criar `levantamento-normativos/.streamlit/secrets.toml` nesta máquina até a frente 5:** `st.secrets` vence a variável vazia do runner e a suíte passaria a chamar o Gemini de verdade. Para LLM local, variável só no terminal do `streamlit run`. |
| Acervo de consulta | `~/Documents/projetos-nuati/referencias/` |
| **Espelho na Câmara** | `git.camara.gov.br` **não é alcançável desta máquina**; é do PC do trabalho. Fluxo decidido em 22/09: este GitHub (B) é a origem → no PC do trabalho `git pull` + `git push camara master`. ⚠ **A URL do projeto lá e o `git remote add camara <url>` não estão registrados** — só o Rodrigo sabe (B-06). O push para B a cada task **continua**; a Câmara é espelho, nunca única cópia. Segredos fora do git nos dois lados. |
| Hospedagem / deploy | ⚠ **CORRIGIDO 22/09 (noite):** existe **deploy no Streamlit Community Cloud** — `https://levantamento-normativos.streamlit.app/`, apontado pelo Rodrigo. Prova: GET → `303` para `share.streamlit.io/-/auth/app` (app **privado**, exige login). A verificação anterior ("nenhum") só olhou arquivos do repo, e deploy no Community Cloud **não deixa rastro no repo**. Esse app vinha do **repo A** (confirmado pelo Rodrigo). ✅ **22/09 (noite): redeploy a partir deste repo B** → **`https://buscador-normativos.streamlit.app/`**, privado (GET → `303` para login), branch **`master`** (única branch de B; `main file` = `levantamento-normativos/app.py`). Streamlit recebeu acesso a repo privado; B **segue privado** (decisão do Rodrigo, depois de ver o que ficaria exposto: IP interno, nomes, ledgers — nenhum segredo no histórico). ⚠ **Branch do deploy: `deploy`**, não `master` (22/09) — congelada em `v1.0.1`; **só avança num marco, com ok do Rodrigo**
(`git push origin master:deploy`). ✅ Rodrigo trocou o app para `deploy` em 22/09 e confirmou a IA gerando palavras-chave (precisou regravar o segredo + reboot). ❓ O app antigo (`levantamento-normativos.streamlit.app`) ainda responde `303` em 22/09 — apagar ou não é do Rodrigo (B-06 item 4). Único outro endereço de infra: o LM local `10.10.111.125:1234` (D-C5). Nenhuma org da Câmara visível no `gh` deste token (só `neuko-repo`). |

⚠ **Assimetria de branch:** A usa `main`, B usa `master`. No merge (T3) isso aparece como
`git fetch levantamento` + `levantamento/main`, enquanto o push daqui é `origin master`.

⚠ **`.claude/` é rastreado neste repo** (`.claude/commands/onboard-buscador.md`). Por isso **não**
entra no `.gitignore` unido da T3, embora estivesse no de A.

⚠ **Namespace `R1-*` tem dois significados:** no plano de 08/09 são as emendas de 2026-09-11; na
revisão de 16/09 os achados brutos foram numerados à parte. Diga sempre de qual documento.

⚠ **A mensagem da tag de rollback é imutável e cita `6.533 linhas`** — medição antiga, que omitia
`llm/__init__.py`. O valor correto é **6.561** (`git ls-files 'levantamento-normativos/*.py' | xargs wc -l` — ⚠ só o app; `'*.py'` cru soma `tools/`, medido em 22/09: 6.849).

**Fechar a D-C9** quando respondida (só importa na v2.0): mover para 🟢 em `_DECISOES-PENDENTES.md` com a
data, abrir seção em `decisions/DECISIONS-LOG.md`, fechar `B-02` no `BLOCKED-ON-RODRIGO.md`.

## 9. Como atualizar este arquivo

Ao mudar de estado: atualize §2/§6, bump `last_updated`, acrescente entrada no `log.md`, atualize
os ledgers. Mantenha ≤ 1 página.
