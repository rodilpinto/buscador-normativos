---
title: "Bloqueios no humano — Buscador de Base Normativa"
maintained_by: sessões do Claude Code; só o Rodrigo resolve
last_updated: 2026-09-23
related: [_DECISOES-PENDENTES.md, _TODO.md, decisions/DECISIONS-LOG.md]
---

# Bloqueado no humano

> Índice acumulativo de ações que só o Rodrigo pode fazer (pedidos a terceiros, credenciais,
> acessos, decisões de gate). **Nunca é resetado**; item resolvido vira trilha DONE no fim.
> Entradas são índices finos — o pacote completo mora no doc da área.
>
> **Estados:** 🔴 aberto · 🟡 em andamento · ✅ resolvido (vai para a trilha DONE, **sem**
> renumerar os demais).
> **IDs:** `B-0N`, sequenciais, **nunca reaproveitados**. Entrada nova vai no fim das abertas,
> antes da trilha DONE. Todo item tem ID — inclusive os que ainda não viraram pedido formulado.

---

## 🔴 B-01 · Pedir ao Alexandro um modelo de embeddings no servidor local

- **Aberto em:** 2026-09-16 · **Origem:** decisão D-C1.2 (board da consolidação, grupo 2)
- **Bloqueia:** nada agora. É **melhoria**, não pré-requisito.

**O pedido, pronto para repassar:**

> O LM Studio em `http://10.10.111.125:1234/v1` serve hoje o `google/gemma-4`, que é modelo de
> **geração**. Para o buscador agrupar resultados por assunto, precisamos também de um modelo de
> **embeddings** carregado no mesmo servidor, exposto em `/v1/embeddings`.
> Serve qualquer um multilíngue de boa qualidade — por exemplo `multilingual-e5-large`,
> `bge-m3` ou similar. São modelos pequenos (~500MB–2GB) e rodam junto com o de geração.

**Por que não trava nada.** A decisão D-C1.2 escolheu `sentence-transformers` rodando **dentro do
app** justamente para não depender desta resposta. Quando o modelo existir no servidor, a troca é
de configuração: a interface de embeddings é a mesma, muda só quem gera o vetor.

**Estado:** aguardando o Rodrigo repassar.

---

## 🔴 B-02 · Escolher como consumir o plano da Fase 1 (dobrar · construir como está · dividir)

- **Aberto em:** 2026-09-16 · **Detalhe completo:** decisão **D-C9** em `_DECISOES-PENDENTES.md`
- **Atualizado em 2026-09-22:** são **três** opções agora — a `c` (dobrar + split por task) foi
  acrescentada a pedido do Rodrigo. A recomendação mudou de `a` para `c`, força fraca.
- **Bloqueia:** ⚠ **nada.** T3/T1/T2 já foram executadas (22/09) e o plano da frente 2 já nasce dobrado. Só volta a importar na v2.0.

Pergunta de uma linha, com as opções e a recomendação no ledger. Não exige pesquisa nem consulta
a terceiros — é preferência de forma.

---

## 🔴 B-03 · Autorizar o registro do repo na auto-memória do `projetos-nuati`

- **Aberto em:** 2026-09-16 · **Origem:** emenda B8 da rodada 2 adversarial
- **Bloqueia:** nada do código. Só o item de `_TODO.md` §P3.

O `~/Documents/projetos-nuati/MEMORY.md` **não existe** (verificado). O MEMORY.md real desse
projeto é a auto-memória em `~/.claude/projects/C--Users-Rodrigo-Documents-projetos-nuati/memory/`,
e a regra global `memory-write-policy` proíbe criar ou editar auto-memória sem autorização
explícita. **Pergunta ao Rodrigo:** autoriza acrescentar uma linha lá apontando para este repo?

---

## 🔴 B-04 · Medir a lacuna de cobertura das fontes catalogadas

- **Aberto em:** 2026-09-16 · **Origem:** comentário do Rodrigo no grupo 5 do board
- **Bloqueia:** o fechamento do MVP. **Não** bloqueia nenhuma task da Fase 1.

> "essa é uma ferramenta de pesquisar, então devemos conseguir pegar o máximo de coisas possível
> senão a ferramenta não será segura." — Rodrigo, 2026-09-16

> ⚠ **2026-09-22 — a lacuna já começou a ser medida, e é pior do que "adiar Planalto/LEGIN".**
> Numa execução real do app v1.0 nesta data, **as duas fontes catalogadas devolveram zero**:
> LexML está atrás de um desafio de WAF do Senado (HTTP 200 com HTML, não XML SRU; os 3 URLs de
> fallback do searcher não salvam — dois são 404) e o endpoint de atos normativos do TCU devolve
> HTTP 500. E a UI reportou **"0 erros"**. Detalhe completo e as medições: `LESSONS.md`, entrada
> de 2026-09-22. Isto **muda o pacote deste bloqueio**: não é só medir o que falta, é decidir o
> que fazer quando a fonte catalogada cai — hoje o usuário não fica sabendo.

> **2026-09-23 — frente 2 fechada (T10).** ✅ a UI e a planilha distinguem indisponível de sem resultado; acórdãos do TCU
> deixaram de ser invisíveis — mas os recentes chegam sem sumário (medido), a lacuna continua.
> **O que ficou medido na execução** (detalhe em `spec/frente2-honestidade-fontes/execucao/INSIGHTS.md` e `revisoes/`):
> - **Janela do TCU:** o app só vê os **~500 acórdãos mais recentes** (`MAX_PAGES` = 25 páginas) — ao vivo em 23/09, "os 500
>   acórdãos mais recentes, de 08/09/2026 a 22/09/2026" (≈ **2 semanas**; testador da FIX-FONTES, `revisoes/fix-fontes.md`; a mesma janela no V11 da T10).
>   A revisão final de UX, antes do conserto, viu ~1 semana. A janela agora aparece no detalhe (FIX-FONTES F-UX3); acórdão
>   mais antigo que isso **não é buscado** — é lacuna de cobertura, não de honestidade.
> - **Sem sumário:** **327 de 500 (65%)** dos acórdãos trazidos chegaram sem `sumario` — nesses, só o título casa a
>   palavra-chave (medido ao vivo na T4, 23/09, `implementacao/04-tcu-esquema-real.md`; o detalhe diz "N sem sumário").
> - **Atos normativos do TCU:** endpoint em HTTP 500 em todas as medições da execução (22–23/09) — o TCU aparece **Parcial**.
> - **LexML:** segue atrás do desafio de WAF do Senado (`bloqueio_waf`; B-05).
> - 🔴 **D-C17:** o dedup fuzzy funde acórdãos **distintos** (26 de 900 numa amostra real) — perda silenciosa que afeta
>   justamente esta medição. A frente 2 fechou com ela aberta (`_DECISOES-PENDENTES.md`).

Rodar uma busca sobre um **tema real** e avaliar o que as fontes catalogadas (LexML + TCU)
deixaram passar, comparado ao que a web aberta trouxe. Precisa de um tema real e do julgamento de
quem conhece o acervo — **não dá para automatizar a aferição**, por isso é bloqueio no humano e
não task. Cobertura insuficiente conta como **falha**, não como limitação conhecida.

---

## 🔴 B-05 · Pedir acesso oficial ao LexML / Senado Federal

- **Aberto em:** 2026-09-22 · **Origem:** decisão D-C13, depois de medir o bloqueio
- **Bloqueia:** nada do código. A frente 2 detecta e avisa; a frente 3 traz fonte substituta.

✅ **Medido em 2026-09-22:** o serviço SRU do LexML (`https://www.lexml.gov.br/busca/SRU`) está
atrás de um **desafio de JavaScript** ("Verificação de segurança — Senado Federal"). Devolve
HTTP 200 com `text/html` em vez de XML. A home do `lexml.gov.br` abre normalmente — é só o
serviço de busca. User-Agent descritivo não muda nada. Não há OAI-PMH (`/oai` → 404).

⛔ **Contornar o desafio programaticamente está fora de escopo** — é proteção anti-robô.

**O pedido, pronto para formular:**

> A ferramenta de levantamento normativo do Nuati/Secin consome o serviço SRU público do LexML
> (`/busca/SRU`) para localizar normativos por CQL. Desde [data] as requisições recebem a página
> de verificação de segurança em vez do XML SRU, o que inviabiliza o uso programático.
> Existe caminho oficial para acesso automatizado — allowlist de IP institucional, credencial de
> API, ou endpoint alternativo para consumo por sistema?

**Estado:** aguardando o Rodrigo decidir se abre o pedido e por qual canal.

---

## 🔴 B-06 · Três fatos do servidor do Nuati que só você (ou o Alexandro) sabe

- **Aberto em:** 2026-09-22 · **Origem:** D-C14 (deploy) · **Bloqueia:** só a frente de deploy pós-v2.0.

1. O app pode rodar **no mesmo host** do LM Studio (`10.10.111.125`)? Se sim, `base_url` vira `localhost`.
2. **Quem opera** lá — instala, sobe o serviço, atualiza a cada release? (Alexandro?)
3. O servidor tem **saída para a internet** (LexML, TCU, DuckDuckGo)? Sem ela, só a web aberta some, mas as
   fontes catalogadas também dependem de rede.

4. ✅ **Resolvido em parte (22/09, noite):** o Rodrigo deu ao Streamlit acesso a repo privado e subiu
   **`https://buscador-normativos.streamlit.app/`** a partir de B (`master`). **Resta:** o app antigo
   (`levantamento-normativos.streamlit.app`, do repo A arquivado) ainda responde — apagar? E confirmar que os segredos
   foram copiados para o app novo. ✅ **22/09:** app antigo **apagado**; chave Gemini `nuati.secin` gravada nos Secrets
   do app novo. ✅ Nome do segredo confirmado (`GEMINI_API_KEY`). Consertos: reboot (chave lida só no import) + modelo trocado para
   `gemini-3.5-flash-lite` (o antigo dava 404 para chave nova). ✅ IA gerando palavras-chave na nuvem, já na branch `deploy` (22/09).
   📝 Rotacionar a chave (um trecho dela passou pelo chat em 22/09). Histórico do item: ~~O app `https://levantamento-normativos.streamlit.app/` já existe~~ (privado). No painel
   `share.streamlit.io` → app → *Settings*: **qual repo, branch e main file** ele usa, e **quais segredos** estão
   lá (há `GEMINI_API_KEY`?). ⚠ Se for o repo A: ele foi **arquivado e ficou privado hoje** — o app fica congelado
   em `af88593`/`eb91277` e pode perder acesso ao repo num reboot. ⚠ O Community Cloud **não troca o repo de um
   app existente**: repontar para B = apagar e recriar — **copiar os segredos antes de apagar**.

Bônus: existe **GitHub/GitLab institucional** onde o repo deva viver? (Você citou `git.camara.gov.br`
como espelho pelo PC do trabalho — registrado no state file §8.)

---

## 🟢 B-07 · Apagar as branches remotas da execução da frente 2 (opcional)

- **Aberto em:** 2026-09-23 · **Bloqueia:** nada (limpeza).
- `origin/frente2/trilha-a` e `origin/frente2/trilha-b` foram backups das trilhas; o conteúdo está em `master` (fast-forward
  `08d9d8c` e `9e259ca`). Se quiser limpar: `git push origin --delete frente2/trilha-a frente2/trilha-b` e depois
  `git branch -D frente2/trilha-a frente2/trilha-b`. Deixar também não custa nada.

---

## ✅ DONE

- [x] **2026-09-22 · Repo A aposentado (T9).** Tag `levantamento-v1-streamlit` no remoto de B; README de
      arquivamento (`af88593`); `rodilpinto/levantamento-normativos` privado e arquivado, confirmado por
      `gh repo view`. Antecipado com o Rodrigo na hora, porque a consolidação já estava provada.

- [x] **2026-09-16 · Tag `levantamento-v1-streamlit` empurrada para o remoto.** Era o ponto de
      restauração de toda a trava anti-regressão e existia **só nesta máquina**
      (`git ls-remote --tags origin` voltava vazio). O plano só a empurrava na T9, a última task —
      até lá, perder o disco perderia o rollback. Fechado no checkpoint de 16/09; confirmado por
      `git ls-remote --tags origin`.
