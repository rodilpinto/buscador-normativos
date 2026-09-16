# Log de decisões — Buscador de Base Normativa

<!-- entradas mais recentes no topo · uma seção por board respondido -->

## [2026-09-16] board-2026-09-16-1610-consolidacao-buscador.html — 2ª rodada (grupos 1 e 2)

Fecha os dois grupos que ficaram abertos na 1ª rodada, depois da explicação da feature pedida
pelo Rodrigo.

Resposta literal: `1a 2b`

| # | Código | Decisão | Escolha |
|---|---|---|---|
| 1 | D-C1 | Indexação semântica | **a** — só agrupar os resultados da busca |
| 2 | D-C1.2 | Modelo de embeddings | **b** — `sentence-transformers` local no app |

### Comentários do Rodrigo (verbatim)

**Grupo 1:** "mas não remover do usuário a capacidade de ver tudo. os agrupamentos devem
facilitar e não remover opções."

**Grupo 2:** "depois me vamos tentar colocar esse modelo de embeddings no servidor local. deixe
como task para repassarmos ao alexandro"

### Consequências registradas

1. **O agrupamento é aditivo, nunca subtrativo** — requisito vinculante, com teste próprio.
   Reforça a decisão B5 de 08/09. Efeito colateral bom: derruba o risco principal que a própria
   feature carregava (cluster ruim → decisão em bloco errada), porque nada é ocultado.
2. **`1b` não entra agora.** O selo já-tenho segue casando por sha256 mais a dedup bibliográfica
   que A já tem. A lacuna conhecida — material sem numeração, como manuais e guias — fica
   registrada e não mitigada nesta rodada.
3. **`2b` destrava o desenvolvimento nesta máquina**, sem depender de confirmação de terceiros.
   Custo aceito: PyTorch e ~500MB de modelo.
4. **Novo bloqueio no humano:** pedir ao Alexandro um modelo de embeddings no LM Studio do
   servidor local, para migrar de `2b` para `2a` depois. Registrado em `BLOCKED-ON-RODRIGO.md`.

## [2026-09-16] board-2026-09-16-1610-consolidacao-buscador.html

Board de 10 grupos sobre a consolidação dos dois projetos (`levantamento-normativos` +
`buscador-normativos`). **Respondidos 8; os grupos 1 e 2 seguem abertos** a pedido do Rodrigo,
que pediu explicação da feature antes de decidir.

Resposta literal: `3a  4a  5c  6a  7a  8a  9a  10a`

| # | Código | Decisão | Escolha | Obs |
|---|---|---|---|---|
| 1 | D-C1 | Indexação semântica — onde entra | **em aberto** | pediu explicação robusta |
| 2 | D-C1.2 | Modelo de embeddings | **em aberto** | depende do grupo 1 |
| 3 | D-C2 | Chat sobre o acervo | **a** — não entra | é o `wiki-chat`, projeto distinto |
| 4 | D-C3 | Dispositivos e checklist | **a** — handoff | ⚠ movido para **roadmap**, fora do MVP |
| 5 | D-B2 | Adaptadores Planalto/LEGIN | **c** — ficam para depois | divergiu da sugestão (era `a`) |
| 6 | D-B1 | Provedor de web aberta | **a** — reusar o de A | fecha decisão aberta desde 09/09 |
| 7 | D-C5 | Configuração do LLM | **a** — local primário | Gemini alternativa, `NullLLM` inerte |
| 8 | D-C6 | Destino do repo A | **a** — arquivar depois de provado | tag já criada |
| 9 | D-C7 | Push dos commits | **a** — a cada chunk fechado | |
| 10 | D-C8 | Lição do endpoint | **a** — `~/.claude/ENVIRONMENT.md` | regra global de lições de ambiente |

### Comentários do Rodrigo (verbatim)

**Grupo 1 (D-C1):** "não entendi direito esse tema, vou precisar de uma explicação bem robusta
da feature. e também não entendi qual a relação disso com a solução wiki-chat, q é outro projeto
bem distinto."

**Grupo 4 (D-C3):** "vamos colocar esse handoff num roadmap para feature futura, uma vez q não é
necessária para o nosso mvp."

**Grupo 5 (D-B2):** "essa é uma ferramenta de pesquisar, então devemos conseguir pegar o máximo
de coisas possível senão a ferramenta não será segura. então temos de ter formas de pegar os
resultados e formas subsidiárias de pegar o q a ferramenta original não pegar"

### Consequências registradas

1. **Cobertura vira requisito, não preferência** (do comentário do grupo 5). A combinação
   escolhida — 5c (adiar Planalto/LEGIN) + 6a (web aberta ligada) — só é aceitável porque a web
   aberta é a **via subsidiária**. Decorre daí um item obrigatório: **medir a lacuna de cobertura**
   das fontes catalogadas contra um tema real antes de considerar o MVP fechado. Falta de
   cobertura é falha de segurança da ferramenta, na formulação do Rodrigo.
2. **O handoff da D-C3 sai do MVP** e entra num roadmap. O MVP entrega acervo organizado +
   planilha-registro; a ponte formatada para `/analise-normativa` e `checklist-conformidade` fica
   para depois.
3. **D-B1 e D-B2 fecham**, as duas abertas desde 2026-09-09. As duas mudaram de natureza quando
   se descobriu que o `levantamento-normativos` existia.
