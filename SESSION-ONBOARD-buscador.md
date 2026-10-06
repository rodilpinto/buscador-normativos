---
title: Buscador de Base Normativa — state snapshot
maintained_by: sessões do Claude Code; humanos podem editar
last_updated: 2026-10-06
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

## 2. Estado na última pausa (2026-10-06, servidor do Nuati no ar; as três fontes de busca falham lá)

🔴 **O app roda no servidor do Nuati, mas lá a busca não traz nada hoje** (busca do Rodrigo em 05/10: "nenhuma fonte entregou
resultado"). Três causas distintas, medidas em 05-06/10 (detalhe: `log.md` 06/10 e B-06): **LexML** responde 404 em todo lugar
(endereço da API mudou; B-05); **TCU** dá 500/timeout em todo lugar (instável do lado deles); **web aberta** (`ddgs`) é barrada
**só no servidor**: o srv-nuati02 só deixa sair para destinos de uma whitelist (fato informado pelo Rodrigo em 06/10). O LLM local
funciona lá (palavras-chave, relevância e categorização, 01/10). 🔴 **D-C32** (o que fazer com a web aberta no servidor) está
aberta. Próximo trabalho: debug na `homologacao`, LexML primeiro (§6).

✅ **Dois ambientes (D-C22), migrados em 01/10:** **`main`** = produção = **`v1.1.1`** (`57f6b08`: `v1.1.0` = `829e71e` levou o framework, D-C30; `v1.1.1` o `servidor_nuati`, D-C31),
branch padrão no GitHub, app `https://buscador-normativos.streamlit.app/`; **`homologacao`** = trabalho do dia a dia, app
`https://buscador-normativos-homologacao.streamlit.app/` (todo push redeploya). **Servidor do Nuati** (desde 01/10, D-C31):
`main` roda como tarefa `BuscadorNormativos`, porta 8404, clonada do espelho `camara` (Gitea); a cada promoção, push da `main`
para `origin` **e** `camara` (da sessão principal) e o Rodrigo roda `servidor_nuati\atualizar.ps1` lá. `master`, `deploy`, `frente2/*` não existem mais.
✅ **Framework adotado** (`rodilpinto/nuati-framework` @ `56d7eb0`, aprovado como `v0.1.0` pelo Rodrigo em 01/10), em `homologacao` e `main`: `llm_cadeia` 1.1.0, `branding` 1.0.0,
`tempo_economizado` 1.0.0, pastas dentro de `levantamento-normativos/`; e `servidor_nuati` 1.0.0 (@ `36e888a`) na **raiz** do repo,
com o `servidor_nuati.conf`. São **cópias**: não se editam; a origem é o framework e o registro de cópias é o README §4 de lá.
Defeito ou falta → pedido ao framework (`_TODO.md`, "Pedidos ao nuati-framework" e "Depois do passe do servidor").
Runner TUDO VERDE (contagem: `BASELINE` em `tools/run_all_tests.py`; `LLM_SOMENTE=nenhum` garante "sem LLM"). Os testes do
`servidor_nuati` ficam fora do runner: `python -m pytest servidor_nuati -q`, da raiz. Registro: `log.md` 01/10 a 06/10.
**Esta sessão (01/10 a 06/10):** `git log --oneline e22822e..HEAD`. ⚠ O SHA mais novo citado aqui está sempre um ou mais commits
atrás dos que gravaram este arquivo: a cadeia real termina em `git log --oneline -3`.

### Estado anterior (2026-09-29, dia da reunião — cadeia de LLM entregue, versão ao vivo congelada)

🟡 **Frente 5 (LM local) em andamento — núcleo entregue em 23–28/09, fora da ordem de tasks, a pedido urgente do Rodrigo.**
A pasta **`levantamento-normativos/llm_cadeia/`** é o módulo de LLM de **todas** as soluções do Nuati (D-C18: copiar e
colar; ~~a ORIGEM é aqui~~ **superado em 01/10: a origem é o `nuati-framework`; aqui fica uma cópia**). O README dela é o ponto de entrada (uso, segredos, adoção, versão, changelog). Verificado ao vivo:
os 5 provedores externos com chave real (texto, notas, categorias, JSON) e, do PC do trabalho, o Gemma local. O que falta da
frente 5: `_TODO.md`, linha da frente 5 (veredito por insumo).
🧊 **Congelamento (D-C21):** o app ao vivo segue a `deploy` = `v1.0.1`; o **app de teste** segue `master`. Levar a versão
nova ao vivo é decisão do Rodrigo **depois da reunião** (B-09). ✅ **29/09:** a reunião passou; o caminho decidido está na §6 (D-C22/D-C23/D-C24). Adotaram o módulo: scopediagram e checklist v2, cada um
numa branch própria (sessões no PC do trabalho). Registro: `log.md`, entradas de 23/09 a 29/09.

### Estado anterior (2026-09-23, frente 2 fechada — T10)

🟢 **Frente 1 da v1.x fechada** (T3 merge → T1 golden-master → T2 runner). O código de A vive em
`levantamento-normativos/` **neste repo**, com história preservada; **repo A privado e arquivado**.
Nenhuma linha de produção mudou **na frente 1** (a frente 2 muda — ver abaixo). Contagem atual de testes: `BASELINE` em `tools/run_all_tests.py`.

🟢 **Noite de 22/09 — app na nuvem funcional:** `https://buscador-normativos.streamlit.app/` (~~privado~~ **público** — conferido em 29/09), IA gerando
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
`git checkout v1.0.1`. **Desde 01/10 a produção segue `main`** (= `v1.0.1`); voltar atrás = commit de reversão em `main`
(`git revert`), nunca push forçado (README do framework §3). Marcos da migração: tags `pre-framework-2026-10-01-deploy`
(`e2cd56a`) e `pre-framework-2026-10-01-master` (`e22822e`). ⚠ A mensagem da tag `v1.0.1` diz "branch master" — escrita antes
de a nuvem passar para `deploy`; tag não se edita, a correção está na D-C14.

## 5. Disciplina de trabalho

Um chunk = uma task do plano. Fechar cada chunk: rodar a suíte → golden-master → atualizar
duráveis → commitar **e pushar** (decisão D-C7). Retomar com `/onboard-buscador`.

## 6. Próximo movimento

▶ **Trabalhar em `homologacao`** (push → o app de homologação atualiza). Promover para `main` só com ok do Rodrigo e tag
(README do framework §3, "Depois da migração"). Última promoção: `v1.1.1` (01/10).
▶ **Pauta da próxima sessão (combinada com o Rodrigo em 06/10): debug das fontes na `homologacao`**, nesta ordem:
(1) **LexML**: achar o endereço atual da API (o SRU `www.lexml.gov.br/busca/SRU` dá 404 de qualquer lugar) e ajustar o
`searchers/lexml_searcher.py`, com teste sem rede; é `gov.br`, então tende a passar pela whitelist do servidor;
(2) **TCU**: conferir se o 500 persiste e se há outro endpoint; (3) **web aberta no servidor**: depende da 🔴 **D-C32**.
Cada conserto: teste → runner + golden → push na `homologacao` → conferir no app de homologação → promover (ok do Rodrigo, tag)
→ push para `origin` e `camara` → o Rodrigo roda `atualizar.ps1` no servidor.
▶ Antes ou junto: recopiar o `servidor_nuati` 1.0.1 do framework (`_TODO.md`, "Depois do passe do servidor").
▶ Depois: o insumo (f) da frente 5 (`ementa None` em `gemini_client.py`), menor, com teste óbvio.
▶ **Com o Rodrigo:** D-C32, B-11 (apagar o app `-teste`), B-12 (Secrets completos na homologação, opcional), B-08 (chave Groq)
e a 🔴 **D-C17**, que venceu o prazo.

🔴 **D-C17 aberta e declarada** (dedup fuzzy funde acórdãos distintos: 26 de 900 numa amostra real; perda silenciosa).
Opções `a` / `a'` / `b` / `c` em `_DECISOES-PENDENTES.md`. Qualquer escolha vira **task própria** no passo fuzzy de
`deduplicator.py`, com golden conferido e fixture real. A revisão final de spec pedia que não passasse do início da frente 5 — ⚠ **prazo vencido em 28/09** (ver o banner na D-C17).
📝 Sugestão minha: perguntar ao Rodrigo na abertura da próxima sessão.

Decisões abertas que **não** travam: D-C9 (só volta na v2.0), D-C14 (deploy). (D-C10.1 fechada em 22/09: tags só nos
marcos.) ⛔ **Não avançar a `main`**: só com ok do Rodrigo e tag (antes de 01/10 isto valia para a `deploy`). Ações do Rodrigo pendentes: `BLOCKED-ON-RODRIGO.md` (B-01 em diante). O B-04 (medir a lacuna
de cobertura) ganhou as medições da frente 2.

## 7. Ponteiros

A tabela **"Onde as coisas estão"** do `CLAUDE.md` do repo é a lista de documentos (specs, planos, split da
frente 2, ledgers, superados). A tabela antiga desta seção foi arquivada no `log.md` (23/09, review da T10).

## 8. Fatos que não estão escritos em nenhum outro lugar

| | |
|---|---|
| **Repo B** (este) | `github.com/rodilpinto/buscador-normativos`, privado. Branch padrão **`main`** (produção); trabalho em **`homologacao`** (D-C22, desde 01/10) |
| **Repo A** (fundido) | `github.com/rodilpinto/levantamento-normativos` — **privado e ARQUIVADO em 22/09** (T9). Só leitura. A tag `levantamento-v1-streamlit` existe lá e aqui (`git ls-remote --tags origin`). |
| Caminho de A | `~/Documents/projeto-nuati-normativos-levantamento/` — ⚠ o código fica em `levantamento-normativos/` **dentro** dele, não na raiz |
| Cliente de LLM | `llm/gemini_client.py` (prompts e parsing do buscador) → transporte em **`llm_cadeia/`** (cópia do `nuati-framework`, 1.1.0 na `homologacao`; ⛔ não editar) |
| Rodar o app | `python -m streamlit run app.py`, a partir da pasta do código |
| **Chave do LLM no app da nuvem** | Valores **nunca** passam pelo chat nem pelo repo. **Produção (`main`, v1.0.1):** só `GEMINI_API_KEY` (conta nuati.secin), modelo fixo `gemini-3.5-flash-lite`. **Homologação:** nomes do `llm_cadeia` (README da pasta; bloco padrão = `segredos.exemplo.toml` do framework); em 01/10 a cadeia de lá começa no `gemini` (B-12). Os dois leem também `GOOGLE_API_KEY`/`GOOGLE_CSE_ID` (opcionais). ⚠ Segredo lido **no import**: mudou Secrets → **Reboot app**. ⛔ **Não criar `levantamento-normativos/.streamlit/secrets.toml`** (`st.secrets` vence o ambiente). Neste PC o `~/.streamlit/secrets.toml` global tem as chaves de teste: o `st.secrets` o lê mesmo fora do `streamlit run`. |
| Acervo de consulta | `~/Documents/projetos-nuati/referencias/` |
| **Espelho na Câmara** | Desde 01/10 (D-C31): remoto **`camara`** = `https://git.camara.gov.br/Nuati-SECIN/buscador-normativos.git` (criado vazio pelo Rodrigo; recebeu `main`, `homologacao` e as tags). Só alcançável do **PC do trabalho** (rede da Câmara). O GitHub (`origin`) continua a origem; a cada promoção, push de `main`, `homologacao` e da tag para os dois. ⚠ Push para o `camara` **da sessão principal**, não de subagente (de subagente dá "Authentication failed"); a falha de autenticação também aparece às vezes na sessão principal e passa ao repetir (06/10: `git fetch --all` falhou no `camara`; o push de 01/10 passou). Conferir com `git ls-remote camara`. Segredos fora do git nos dois lados. O servidor do Nuati clona daqui (B-06). |
| **Cópias dos recursos do framework** | Registro único: README do `rodilpinto/nuati-framework`, §4 (o que cada app tem, versão medida, situação). Este repo não é mais origem de nada. |
| Hospedagem / deploy | Streamlit Community Cloud, apps **públicos** (D-C26), `main file` = `levantamento-normativos/app.py`. **Produção:** `https://buscador-normativos.streamlit.app/` ← `main`. **Homologação:** `https://buscador-normativos-homologacao.streamlit.app/` ← `homologacao`. Recriados pelo Rodrigo em 01/10 (o Streamlit não troca a branch de um app: apagar e recriar). App antigo `-teste` sem papel (B-11). Deploy em PaaS não deixa rastro no repo (`LESSONS.md` 22/09). Servidor do Nuati (espelho de `main`): B-06. |

⚠ **`.claude/` é rastreado neste repo** (`.claude/commands/onboard-buscador.md`). Por isso **não**
entra no `.gitignore` unido da T3, embora estivesse no de A.

## 9. Como atualizar este arquivo

Ao mudar de estado: atualize §2/§6, bump `last_updated`, acrescente entrada no `log.md`, atualize
os ledgers. Mantenha ≤ 1 página.
