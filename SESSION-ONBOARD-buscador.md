---
title: Buscador de Base Normativa — state snapshot
maintained_by: sessões do Claude Code; humanos podem editar
last_updated: 2026-09-29
related: [levantamento-normativos/llm_cadeia/README.md, _TODO.md, _DECISOES-PENDENTES.md, log.md, LESSONS.md, BLOCKED-ON-RODRIGO.md, decisions/DECISIONS-LOG.md, docs/superpowers/specs/2026-09-16-consolidacao-buscador-design.md, docs/superpowers/plans/2026-09-16-consolidacao-fase1.md]
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

## 2. Estado na última pausa (2026-09-29, dia da reunião — cadeia de LLM entregue, versão ao vivo congelada)

🟡 **Frente 5 (LM local) em andamento — núcleo entregue em 23–28/09, fora da ordem de tasks, a pedido urgente do Rodrigo.**
A pasta **`levantamento-normativos/llm_cadeia/`** é o módulo de LLM de **todas** as soluções do Nuati (D-C18: copiar e
colar; a ORIGEM é aqui). O README dela é o ponto de entrada (uso, segredos, adoção, versão, changelog). Verificado ao vivo:
os 5 provedores externos com chave real (texto, notas, categorias, JSON) e, do PC do trabalho, o Gemma local. O que falta da
frente 5: `_TODO.md`, linha da frente 5 (veredito por insumo).
🧊 **Congelamento (D-C21):** o app ao vivo segue a `deploy` = `v1.0.1`; o **app de teste** segue `master`. Levar a versão
nova ao vivo é decisão do Rodrigo **depois da reunião** (B-09). Adotaram o módulo: scopediagram e checklist v2, cada um
numa branch própria (sessões no PC do trabalho). Registro: `log.md`, entradas de 23/09 a 29/09.

### Estado anterior (2026-09-23, frente 2 fechada — T10)

🟢 **Frente 1 da v1.x fechada** (T3 merge → T1 golden-master → T2 runner). O código de A vive em
`levantamento-normativos/` **neste repo**, com história preservada; **repo A privado e arquivado**.
Nenhuma linha de produção mudou **na frente 1** (a frente 2 muda — ver abaixo). Contagem atual de testes: `BASELINE` em `tools/run_all_tests.py`.

🟢 **Noite de 22/09 — app na nuvem funcional:** `https://buscador-normativos.streamlit.app/` (privado), IA gerando
palavras-chave (chave `nuati.secin`, modelo `gemini-3.5-flash-lite`). Ponto de retorno: tag **`v1.0.1`**. A nuvem
segue a branch **`deploy`** (congelada em `v1.0.1`); o trabalho segue em `master`. Detalhe em §4 e §8.

✅ **Frente 2 (honestidade das fontes) FECHADA em 23/09 (T10).** As fontes declaram por que não responderam
(`motivo`/`detalhe`/`parcial`); o TCU lê o esquema real do acórdão; a nota diz de onde veio; tela e planilha separam
indisponível, parcial e sem resultado. Executada por agentes (D-C16): T1–T9 → revisão final de 5 lentes → FIX-FONTES
(`7322cc0`) + FIX-SAÍDA (`51883f6`) → T10. Critérios §7 conferidos (runner, golden,
dedup, V11 — números e saídas em `implementacao/10-fechar-frente.md`). Registro completo: `spec/frente2-honestidade-fontes/execucao/` (TODOS =
SSOT, INSIGHTS, `revisoes/`) e `implementacao/10-fechar-frente.md` (comandos e saídas). ⚠ Fechou com a 🔴 **D-C17 aberta**.
Fase 5 fechada (`/checkpoint` de 23/09): worktrees removidos, a evidência (screenshots e `.xlsx`, não versionados) está em
`tests/evidencia/<worktree>/` deste repo — local, ignorada pelo git. Branches `frente2/trilha-*` no remoto: B-07.

**Cadeia:** `git log --oneline --reverse 1c063ea..HEAD` (frente 2 inteira; não é restatada aqui). Marcos: `da543be` T1 ·
`9e259ca` trilha B · `08d9d8c` trilha A · `d4cab80` T9 · `7322cc0`/`51883f6` consertos da revisão final. ⚠ O SHA mais
novo listado aqui está SEMPRE um passo atrás do commit que gravou este arquivo; a cadeia real termina em `git log --oneline -3`.

**Working tree (`master`), checkpoint de 29/09:** limpo depois do commit do checkpoint, **mas `master` à frente de `origin/master`** — o push espera o ok do Rodrigo (dia da reunião; ver §6). Conferir com `git status -sb`. Remoto `levantamento` (repo A local) segue
configurado; A está arquivado no GitHub. A tag `levantamento-v1-streamlit` existe aqui **e** no remoto de B.

**Ferramentas:** `python tools/run_all_tests.py` (≈5 min, medido 23/09: 4m49s — as suítes LIVE batem em fontes quebradas) e
`python tools/golden_master.py comparar`. O app v1.0: `python -m streamlit run app.py` em
`levantamento-normativos/`.

## 3. Achados críticos (não perder)

5. **O agrupamento semântico é ADITIVO** — nunca remove, oculta ou filtra item da visão do
   usuário (requisito vinculante do Rodrigo, D-C1). Tem teste próprio; não "simplificar".
6. **Cobertura é requisito, não preferência:** medir a lacuna das fontes catalogadas contra um
   tema real **antes** de fechar o MVP.
7. **LLM local inalcançável desta máquina** (`10.10.111.125:1234`, timeout); **alcançável do PC do trabalho** (Gemma
   verificado ao vivo em 28/09 pela sessão do scopediagram). Detalhe e a regra do `timeout` em tupla:
   `~/.claude/ENVIRONMENT.md`. Chaves de LLM para teste local: `~/.llm-chaves.toml` (fora do repo; receita no mesmo
   `ENVIRONMENT.md`) — **nunca imprimir o conteúdo**.
8. Histórico (não é greenfield; B2 revertida; emendas/ordem do plano de 16/09; fontes quebradas em 22/09; fixtures
   reais): arquivado no `log.md`, entrada de 23/09 (review da T10). Estado das fontes: a frente 2 consertou (23/09) o
   que dava; o que resta está em B-04/B-05 (`BLOCKED-ON-RODRIGO.md`).

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
`git push -f origin <tag>:deploy` (**só com ok do Rodrigo**). ⚠ A mensagem da tag `v1.0.1` diz "branch master" — escrita antes
de a nuvem passar para `deploy`; tag não se edita, a correção está na D-C14.

## 5. Disciplina de trabalho

Um chunk = uma task do plano. Fechar cada chunk: rodar a suíte → golden-master → atualizar
duráveis → commitar **e pushar** (decisão D-C7). Retomar com `/onboard-buscador`.

## 6. Próximo movimento

▶ **Primeiro, com o Rodrigo (depois da reunião de 29/09):** B-09 (levar `master` à `deploy`? visibilidade dos apps de
teste), B-08 (trocar a chave Groq) e a 🔴 **D-C17**, que venceu o prazo. **Até ele decidir, não empurrar `master`** — o app
de teste é o reserva da reunião e redeploya a cada push. **O congelamento acaba só com um ok explícito do Rodrigo**
(não com a passagem do dia); até lá, cada chunk é commitado e fica local.
▶ **Primeiro passo agêntico** (não depende do Rodrigo): terminar a frente 5 pelos insumos ainda abertos da linha dela no
`_TODO.md` — o (f) (`ementa None`, reproduzido em 29/09) é o menor e tem teste óbvio; depois (e), (c), (d), (g). Qualquer
mudança em `llm_cadeia/` sobe `__version__` + changelog (regra de sincronia no README). ⚠ As chaves de LLM estão definidas no ambiente desta máquina: app lançado à mão
usa `env -u GEMINI_API_KEY -u GOOGLE_API_KEY -u OPENAI_API_KEY` (`~/.claude/ENVIRONMENT.md`).

🔴 **D-C17 aberta e declarada** (dedup fuzzy funde acórdãos distintos: 26 de 900 numa amostra real; perda silenciosa).
Opções `a` / `a'` / `b` / `c` em `_DECISOES-PENDENTES.md`. Qualquer escolha vira **task própria** no passo fuzzy de
`deduplicator.py`, com golden conferido e fixture real. A revisão final de spec pedia que não passasse do início da frente 5 — ⚠ **prazo vencido em 28/09** (ver o banner na D-C17).
📝 Sugestão minha: perguntar ao Rodrigo na abertura da próxima sessão.

Decisões abertas que **não** travam: D-C9 (só volta na v2.0), D-C14 (deploy). (D-C10.1 fechada em 22/09: tags só nos
marcos.) ⛔ **Não avançar a branch `deploy`**: só num marco, com ok do Rodrigo (`git push origin master:deploy`). O fim da
frente 2 **não** é autorização. Ações do Rodrigo pendentes: `BLOCKED-ON-RODRIGO.md` (B-01 em diante). O B-04 (medir a lacuna
de cobertura) ganhou as medições da frente 2.

## 7. Ponteiros

A tabela **"Onde as coisas estão"** do `CLAUDE.md` do repo é a lista de documentos (specs, planos, split da
frente 2, ledgers, superados). A tabela antiga desta seção foi arquivada no `log.md` (23/09, review da T10).

## 8. Fatos que não estão escritos em nenhum outro lugar

| | |
|---|---|
| **Repo B** (este) | `github.com/rodilpinto/buscador-normativos`, privado, branch **`master`** |
| **Repo A** (fundido) | `github.com/rodilpinto/levantamento-normativos` — **privado e ARQUIVADO em 22/09** (T9). Só leitura. A tag `levantamento-v1-streamlit` existe lá e aqui (`git ls-remote --tags origin`). |
| Caminho de A | `~/Documents/projeto-nuati-normativos-levantamento/` — ⚠ o código fica em `levantamento-normativos/` **dentro** dele, não na raiz |
| Cliente de LLM | `llm/gemini_client.py` (prompts e parsing do buscador) → transporte em **`llm_cadeia/`** (módulo copiável; README = entrada) |
| Rodar o app | `python -m streamlit run app.py`, a partir da pasta do código |
| **Chave do LLM no app da nuvem** | Chave Gemini do projeto **`nuati.secin`** nos *Secrets* do app `buscador-normativos` (share.streamlit.io) — **o valor nunca passa pelo chat nem pelo repo**. A `deploy` (`v1.0.1`) lê só **`GEMINI_API_KEY`**, modelo **`gemini-3.5-flash-lite`**. Em `master` desde 23–25/09: **cadeia de LLM** — desde 28/09 a pasta copiável **`llm_cadeia/`** (README = ponto de entrada; origem para as outras soluções): chave digitada pelo usuário (só na sessão) > local (`LLM_BASE_URL`) > `GEMINI_API_KEY` > `GEMINI_API_KEY_2` > Groq > Cerebras > OpenRouter (todo serviço com segunda chave `_2`), com rodízio de modelos por provedor e esperas por tipo de erro; nomes dos segredos em `.streamlit/secrets.toml.example`. ⚠ O LM local `10.10.111.125` é intranet: a nuvem **não** o alcança. ⚠ Segredo lido **no import**: mudou Secrets → **Reboot app**. ⛔ **Não criar `levantamento-normativos/.streamlit/secrets.toml` nesta máquina até a frente 5** (`st.secrets` vence a variável vazia do runner). Histórico: `log.md` 23/09. |
| Acervo de consulta | `~/Documents/projetos-nuati/referencias/` |
| **Espelho na Câmara** | `git.camara.gov.br` **não é alcançável desta máquina**; é do PC do trabalho. Fluxo decidido em 22/09: este GitHub (B) é a origem → no PC do trabalho `git pull` + `git push camara master`. ⚠ **A URL do projeto lá e o `git remote add camara <url>` não estão registrados** — só o Rodrigo sabe (B-06). O push para B a cada task **continua**; a Câmara é espelho, nunca única cópia. Segredos fora do git nos dois lados. |
| **Cópias do `llm_cadeia`** (recopiar a cada versão nova) | **scopediagram** — no PC do trabalho; aqui: `~/Documents/projeto-nuati-diagrama-de-escopo/`; deve estar na **1.0.1** (`@ 7f1c069`, dita à sessão dele em 28/09 — não conferido aqui). **checklist v2** — repo público `rodilpinto/checklist-conformidade`, branch `feat/llm-cadeia` (o `master` de lá é o app ao vivo); cópia em `llm_cadeia/` na raiz do repo; **medido em 29/09: `__version__ = "1.0.0"` — uma atrás da origem, precisa recopiar a 1.0.1** (comando: `curl -s https://raw.githubusercontent.com/rodilpinto/checklist-conformidade/feat/llm-cadeia/llm_cadeia/__init__.py \| grep __version__`). Cópia nova: acrescentar linha aqui. |
| Hospedagem / deploy | **`https://buscador-normativos.streamlit.app/`** (Streamlit Community Cloud, privado; `main file` = `levantamento-normativos/app.py`), servido da branch **`deploy`**, congelada em `v1.0.1`. **App de teste** (28/09): `https://buscador-normativos-teste.streamlit.app/`, segue **`master`** (todo push em `master` redeploya), Python 3.14, Secrets = conteúdo de `~/.llm-chaves.toml` (local, fora do repo); criado pelo Rodrigo e confirmado funcionando (IA + chave do usuário). ⛔ **Só avança num marco, com ok do Rodrigo** (`git push origin master:deploy`). Deploy em PaaS não deixa rastro no repo (`LESSONS.md` 22/09). App antigo e fatos do servidor do Nuati: B-06. LM local: `10.10.111.125:1234` (D-C5). Histórico: `log.md` 23/09. |

⚠ **`.claude/` é rastreado neste repo** (`.claude/commands/onboard-buscador.md`). Por isso **não**
entra no `.gitignore` unido da T3, embora estivesse no de A.

## 9. Como atualizar este arquivo

Ao mudar de estado: atualize §2/§6, bump `last_updated`, acrescente entrada no `log.md`, atualize
os ledgers. Mantenha ≤ 1 página.
