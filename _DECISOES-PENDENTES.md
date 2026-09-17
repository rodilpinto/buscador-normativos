---
title: "Decisões abertas — Buscador de Base Normativa"
maintained_by: sessões do Claude Code; só o Rodrigo resolve
last_updated: 2026-09-16
related: [_TODO.md, SESSION-ONBOARD-buscador.md, log.md, decisions/DECISIONS-LOG.md]
---

# Decisões — o que espera o humano

> Sugestões aqui são propostas, não fatos validados — marcadas com 📝.
> Histórico de rodadas respondidas: `decisions/DECISIONS-LOG.md`.

> **Legenda de estados usada neste arquivo:** 🔴 ABERTA · 🟡 EM ANÁLISE · 🟢 DECIDIDA · ⛔ bloqueada
> em autorização. Ao procurar o que está aberto, procure **🔴 e 🟡 e ⛔**, não só 🔴.

## 🔴 D-C9 — Dobrar as emendas no corpo do plano, ou construir com elas como estão?

- **Onde aparece:** fim da sessão de 16/09, depois das 3 rodadas adversariais. **Não respondida.**
- **Trava:** o início da Fase 1. As duas opções levam à mesma primeira task (T3, o merge).

O plano da Fase 1 tem emendas vinculantes em três camadas (A1-A21, B1-B12, C1-C5), com
precedência **C > B > A > corpo**. Cada seção do corpo derrubada já carrega um marcador `⛔`
apontando qual emenda a derruba (feito no checkpoint de 16/09).

| Opção | Ganha | Perde / risco |
|---|---|---|
| **a** Dobrar as emendas no corpo primeiro | plano linear, lido de cima a baixo sem saltar | ~1 passada de edição sobre 1.7k linhas; risco de errar ao transcrever |
| **b** Construir com as emendas como estão | começa agora; a precedência está explícita e marcada | o executor precisa ler 3 seções + o corpo por task; é onde alguém escorrega |

📝 **Recomendação:** `a`, mas é preferência fraca — os marcadores `⛔` já mitigam boa parte do
risco da `b`.

**Decisão tomada:** _(pendente)_

---

## ⛔ Bloqueadas em autorização (não são escolhas, são permissões)

- **Registrar este repo no `MEMORY.md` do `projetos-nuati`** — é auto-memória, e a regra global
  `memory-write-policy` exige autorização explícita do Rodrigo. Item no `_TODO.md` §P3.

---

## 🟢 Decididas em 2026-09-16 (board da consolidação)

- **D-C1 · Indexação semântica:** **só `1a`** — agrupar os resultados da busca por assunto.
  Ficam de fora `1b` (selo já-tenho por embedding; a dedup bibliográfica de A atende por ora)
  e `1c` (busca no acervo baixado; é o `wiki-chat`).
  ### ⚠ Requisito vinculante — o agrupamento é aditivo
  > "não remover do usuário a capacidade de ver tudo. os agrupamentos devem facilitar e não
  > remover opções." — Rodrigo, 2026-09-16

  O agrupamento **oferece** um atalho para decidir em bloco; **nunca** remove, oculta ou filtra
  itens da visão do usuário. Reforça a decisão B5 ("mostrar todos, nada é ocultado") e derruba o
  principal risco da feature: se nada some, cluster mal formado custa uma conferência a mais,
  não um normativo perdido. **Precisa de teste próprio** — não "simplificar".
- **D-C1.2 · Modelo de embeddings:** **`2b`** — `sentence-transformers` local no próprio app.
  Roda offline, inclusive nesta máquina, sem depender de terceiros para destravar.
  ➡ **Follow-up registrado:** tentar depois mover o modelo de embeddings para o servidor local.
  Pedido a repassar ao Alexandro — ver `BLOCKED-ON-RODRIGO.md`.

- **D-C2 · Chat sobre o acervo:** **não entra**. É o `wiki-chat`, projeto distinto.
- **D-C3 · Extração de dispositivos e geração de checklist:** **não entra no MVP**. O handoff
  para `/analise-normativa` e `checklist-conformidade` vai para **roadmap de feature futura**.
- **D-B2 · Adaptadores Planalto e LEGIN:** **ficam para depois**. Não entram agora; a lacuna de
  cobertura que deixam **precisa ser medida** contra um tema real (ver requisito abaixo).
- **D-B1 · Provedor de web aberta:** **reusar o que A já tem** — DuckDuckGo sem chave e Google
  CSE quando houver chave, ambos já revisados em segurança. Fecha decisão aberta desde 09/09.
- **D-C5 · Configuração do LLM:** **local primário** (`gemma-4` em `10.10.111.125:1234`),
  Gemini como alternativa configurável, `NullLLM` como padrão inerte.
- **D-C6 · Destino do repo A:** **arquivar no GitHub** depois que o golden-master provar a
  consolidação. Reversível; a tag `levantamento-v1-streamlit` garante restauração.
- **D-C7 · Push:** **a cada chunk fechado**, para o outro PC enxergar o andamento.
- **D-C8 · Lição do endpoint inalcançável:** registrar em **`~/.claude/ENVIRONMENT.md`**.

### ⚠ Requisito derivado do comentário do Rodrigo (grupo 5)

> "essa é uma ferramenta de pesquisar, então devemos conseguir pegar o máximo de coisas possível
> senão a ferramenta não será segura."

**Cobertura é requisito, não preferência.** Adiar Planalto/LEGIN (D-B2) só é aceitável porque a
web aberta (D-B1) é a **via subsidiária**. Decorre disto, e é obrigatório antes de fechar o MVP:
**medir a lacuna de cobertura** das fontes catalogadas contra um tema real, e registrar o
resultado. Cobertura insuficiente conta como falha, não como limitação conhecida.

---

## 🟢 Decididas no brainstorm de 2026-09-08

Detalhe na spec de 08/09 §4. ⚠ **A decisão B2 foi revertida em 2026-09-16** — ver spec de
consolidação §2: a base é o Streamlit já escrito, não um FastAPI novo. As demais seguem válidas.

- **B1 · Fontes:** híbrido — catalogadas primeiro, web aberta como rede de segurança, com
  procedência marcada por resultado.
- ~~**B2 · Arquitetura:** app web local (FastAPI + SQLite)~~ → **revertida em 16/09**.
- **B3 · LLM:** híbrido — o sistema roda **inteiro sem LLM**; quando configurado, enriquece.
- **B4 · Organização:** por tema/ação de controle. Mitigação obrigatória: dedup sha256 com
  detecção e relatório — nunca duplicação silenciosa.
- **B5 · Já-tenho:** mostrar todos os resultados com selo, nada é ocultado. Mitigação
  obrigatória: ação de grupo "desmarcar todos os já-tenho".

## ⚠ Decisão do repo-pai que este projeto reverte

**D-AI-01** (`projetos-nuati/projeto-AI-com-IA/decisions/`) dizia "nesta rodada não se constrói
nada". Construir o buscador **reverte isso** — decisão do Rodrigo em 08/09, já registrada no
`DECISIONS-LOG.md` daquela área.
