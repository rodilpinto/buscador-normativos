# Consolidação do Buscador — Fase 1 (merge sem regressão)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trazer as 6.533 linhas do app `levantamento-normativos` para dentro deste repo
preservando histórico, provar mecanicamente que nada regrediu, trocar o transporte do LLM para
OpenAI-compatível, e corrigir os documentos que afirmam falsamente que esse código não existe.

**Architecture:** O código de A entra por `git merge --allow-unrelated-histories`, mantendo
autoria e cadeia de commits. Antes de qualquer mudança, congela-se um golden-master das saídas
determinísticas (Excel e dedup); toda alteração posterior é provada contra ele por comparação de
bytes, nunca por leitura de código. O acoplamento ao Gemini é isolado atrás de um protocolo de
backend com três implementações (OpenAI-compatível, Gemini, nulo), de modo que o sistema rode
inteiro sem LLM — requisito B3.

**Tech Stack:** Python 3.13.7 · Streamlit · requests · openpyxl · beautifulsoup4 · ddgs ·
pytest 9.0.2 · `sentence-transformers` (só na Fase 2)

## Emendas da Rodada 1 — VINCULANTES, prevalecem sobre o corpo

> **Data:** 2026-09-16 · **Método:** 5 revisores independentes e cegos entre si (regressão ·
> dados/API · risco · arquitetura · teste), com trava de proporcionalidade obrigatória.
> **39 achados brutos → 21 aceitos, 3 adaptados, 3 rejeitados.** 38 dos 39 eram `verified`.
> **Precedência:** onde uma emenda contradiz o corpo, **a emenda vence**.
> ✅ = comportamento verificado por leitura de código ou execução · 📝 = recomendação de desenho.

### BLOCKERS — nada de código antes de resolver

**A1 · A ordem das tasks é impossível.** ✅ [convergente: lentes 1 e 4]
As Tasks 1 e 2 rodam `tools/golden_master.py` e `tools/run_all_tests.py`, que fazem
`APP = RAIZ / "levantamento-normativos"` — pasta que **só existe depois da Task 3** (o merge).
Resultado medido: `ModuleNotFoundError: No module named 'models'` na Task 1, e
`NotADirectoryError` na Task 2 (cwd inexistente), antes de qualquer teste rodar.
**Emenda:** **a Task 3 (merge) passa a ser a PRIMEIRA.** O merge é operação de git puro e não
altera um byte de `.py`, então "congelar antes de qualquer mudança" continua satisfeito. A nova
ordem é **3 → 1 → 2 → 4 → 5 → 6 → 7 → 8 → 9**. O Step 6 da Task 3 ("provar que nada regrediu")
**sai**, porque chama ferramentas que ainda não existem nesse ponto.

**A2 · `export_to_excel` não existe.** ✅ [convergente: lentes 1, 2 e 4]
A função pública real é **`generate_excel(results, topic)`** (`excel_export.py:274`); é o que
`app.py:26` e `test_phase4.py:19` importam. `deduplicate(results)` (`deduplicator.py:186`), essa
sim, está correta.
**Emenda:** trocar as duas ocorrências de `export_to_excel` por `generate_excel` no bloco da
Task 1, e apagar o aviso que mandava "conferir" — o nome certo já é conhecido.

**A3 · O sha256 do `.xlsx` NÃO é determinístico — o golden-master nasceria morto.** ✅ [convergente: lentes 1, 2 e 4, cada uma medindo por conta própria]
Três revisores rodaram o `generate_excel` real duas vezes com entrada idêntica e obtiveram
hashes diferentes (`71c0072e…`/`08a04d87…`, `bc84f2ba…`/`e240e5d1…`, `57498cbd…`/`e64ef12d…`).
Causa medida: `.xlsx` é um ZIP; o `date_time` de cada membro recebe o relógio do `save()`, e
`docProps/core.xml` embute `dcterms:created`/`modified`.
Consequência: `congelar && comparar` imprimiria `DIVERGIU` na sequência imediata, **sem nada ter
mudado** — e o executor seria empurrado a deletar a metade Excel da prova para destravar.
**Emenda:** hashear o **conteúdo**, não o arquivo. Substituir o corpo de `_sha_planilha`:

```python
def _sha_planilha(itens: list) -> str:
    """Hash dos VALORES das celulas, nao dos bytes do arquivo.

    .xlsx e um ZIP: o date_time de cada membro e o docProps/core.xml carregam
    o relogio da geracao, entao o sha dos bytes crus muda a cada execucao.
    Medido: dois runs com a mesma entrada dao hashes diferentes.
    load_workbook e a mesma tecnica que test_phase4.py:19 ja usa.
    """
    from excel_export import generate_excel
    from openpyxl import load_workbook

    ws = load_workbook(generate_excel(itens, topic="golden-master")).active
    linhas = [tuple(c.value for c in linha) for linha in ws.iter_rows()]
    return hashlib.sha256(repr(linhas).encode("utf-8")).hexdigest()
```

> **Conflito resolvido:** a lente 2 propôs hashear os membros do ZIP ignorando `docProps/`.
> **Rejeitado em favor do hash de células** — é mais simples, é a técnica que o projeto já usa
> em `test_phase4.py`, e não quebra quando openpyxl mudar estilos ou tema entre versões.

**A4 · As faixas de linha da Task 6 deixam quatro restos, e um deles impede o módulo de importar.** ✅ [convergente: lentes 1 e 3]
Um revisor **executou** as remoções propostas (28-48, 56-60, 74-105, 106-145) num clone e achou:
(a) a linha 49 `        logger.info("No Gemini SDK installed…")` fica com indentação de 8 espaços
em nível de módulo → **`IndentationError`, o módulo nem importa**; (b) o cabeçalho de comentário
`# Priority: st.secrets > env var > empty string` (51-54) sobrevive descrevendo comportamento
apagado — doc falso de pé; (c) `MODEL_NAME = "gemini-2.5-flash-lite"` (linha 68) executa **depois**
do `MODEL_NAME` novo e o sobrescreve; (d) o `is_available()` antigo (147-153) sobrescreve o novo e
faz `return _sdk != "none" and bool(api_key)` com ambos os nomes já deletados → **`NameError`**.
`app.py:24` importa essa função como `llm_available` e a chama em 6 pontos (291, 368, 395, 398,
418, 571): **o app quebra no Passo 1 do wizard.**
**Emenda:** o Step 3 passa a nomear **blocos**, não faixas: apagar do `# SDK import` até o fim do
`except ImportError`; o bloco `# API Key Resolution` inteiro; o bloco `# Model configuration`
com o `MODEL_NAME` literal; o bloco `# Lazy Singleton Client` com `_client`, `_no_key_logged` e
`_get_client`; e **`_generate` E `is_available`**. A seção **Files** da Task 6 passa a dizer
`linhas 28-68 e 74-153`.

**A5 · O runner descarta o exit code das suítes-script.** ✅ [lente 5]
No laço de `SUITES_SCRIPT`, `_, saida = _rodar(...)` joga fora o `returncode`: só o regex decide.
Não é hipotético — `test_llm_phase3.py` restaura `os.environ["GEMINI_API_KEY"]` **depois** de
imprimir o resumo; se essa linha levantar, a suíte sai com código ≠ 0 e o runner ainda imprime
`TUDO VERDE`.
**Emenda:** trocar por `code, saida = _rodar(...)` e acrescentar `if code != 0: falhou = True`,
espelhando o que o laço de `SUITES_PYTEST` já faz duas linhas abaixo.

### ALTOS — corrigir antes da task correspondente

**A6 · O isolamento de ambiente do `test_llm_phase3.py` fura com a variável nova.** ✅ [convergente: lentes 1 e 4]
A suíte se blinda com **uma** linha: `os.environ.pop("GEMINI_API_KEY", None)` (`test_llm_phase3.py:14`).
A Task 5 faz `escolher_backend()` ler também `BUSCADOR_LLM_BASE_URL` — que o próprio plano manda
documentar no `CLAUDE.md` como configuração de produção. Entrada concreta: essa variável setada
(o estado pretendido na máquina da Câmara) → `is_available()` True → a suíte entra no ramo que
exige resultado não-vazio → endpoint inalcançável → `[]` → **53/53 vira 52/53**, e o runner sai 1.
O critério de pronto só testava "ambos vazios", então o buraco passava batido.
**Emenda:** novo step na Task 6 trocando a linha 14 por
`for _v in ("GEMINI_API_KEY", "BUSCADOR_LLM_BASE_URL", "BUSCADOR_LLM_API_KEY"): os.environ.pop(_v, None)`.

**A7 · `timeout` escalar faz uma busca de 100 normativos travar 11 minutos.** ✅ [lente 2]
`requests` aplica o timeout escalar a connect **e** read. O endpoint de produção foi verificado
como inalcançável **por hang** (IP interno sem rota: o SYN morre sem RST), não por recusa. Com
`BATCH_SIZE = 20` (`gemini_client.py:160`), `score_relevance` e `categorize_results` fatiam 100
resultados em lotes, um `_generate` por lote → ~11 minutos de espera antes de cair na heurística.
**Emenda:** `timeout=(3.05, TIMEOUT_PADRAO)` — tupla `(connect, read)` que `requests` aceita
nativamente. Host sem rota falha em ~3s; 11 min viram ~33s, sem encurtar o read de quem está
realmente gerando.

**A8 · O gate de preservação de documentação dá falso verde.** ✅ [convergente: lentes 1, 3 e 4]
Rodado contra o diff real da Task 6 simulada: de **82 linhas removidas, o grep casa 12**. Entre
as 70 perdidas estão frases de contrato — `temperature: Sampling temperature (0.0 = deterministic).`,
`max_tokens: Maximum output tokens.`, `Returns None if no SDK is installed`. Causa: a alternância
exige `#`, aspas ou `[A-Z]` no começo, e linha de continuação de docstring começa minúscula. O
`| head -50` piora. **O gate que existe para provar que nenhuma explicação sumiu passava verde
tendo deixado passar a única linha que documenta que `temperature 0.0` significa determinístico.**
**Emenda:** trocar por `git diff -U0 levantamento-v1-streamlit HEAD -- '*.py' | grep '^-' | grep -v '^---'`
e **ler tudo, sem `head`**. São ~80 linhas; filtrar é o que cria o falso verde.

**A9 · O runner não compara contra a linha de base — suíte pode encolher em silêncio.** ✅ [lente 5]
`if failed or passed == 0` só olha a execução corrente. Se `test_comprehensive.py` cair de 98
para 40 testes executados e os 40 passarem, sai `Total: 40 | Passed: 40 | Failed: 0` e o runner
reporta `TUDO VERDE`. Hoje a prova de que os números batem depende de um humano lembrar do "anote
os números" — exatamente o que a regra anti-regressão proíbe.
**Emenda:** acrescentar ao runner
`BASELINE = {"test_searchers.py": 13, "test_llm_phase3.py": 53, "test_comprehensive.py": 98, "test_phase4.py": 41}`
e falhar com mensagem explícita quando `passed != BASELINE[nome]`, dizendo qual suíte encolheu e
de quanto.

**A10 · Os 10 testes do novo backend nunca entram no runner.** ✅ [convergente: lentes 1 e 4]
`SUITES_PYTEST` é hardcoded com uma suíte só. Os 8 testes da Task 5 e os 2 da Task 6 — **os
únicos que cobrem a troca de transporte, que é o refactor mais arriscado da fase** — rodam apenas
nos steps manuais dessas tasks e nunca mais.
**Emenda:** `SUITES_PYTEST = ["test_phase4.py", "test_backends.py"]`, e `BASELINE` ganha
`"test_backends.py": 10`.

**A11 · A docstring de módulo do `gemini_client.py` passa a mentir.** ✅ [lente 3]
Nenhum step a toca, e ela afirma duas coisas que ficam falsas: "encapsulates all communication
with the Google Gemini API using the google-genai SDK" e "It is the **ONLY** module in the
project that imports google.genai" — que deixa de ser verdade assim que `backends.py` o importa.
O próximo agente lê o contrato errado no primeiro parágrafo.
**Emenda:** reescrever as linhas 1-14 dizendo que o módulo hospeda prompts, parsing e heurística
e **delega transporte** a `llm/backends.py`, preservando o parágrafo
`Every public function degrades gracefully…`, que continua verdadeiro e é o contrato do B3.

**A12 · A entrada fixa não exercita duas das três estratégias de dedup.** ✅ [lente 5]
O deduplicador tem 3 estratégias (id exato · `tipo+numero` · ementa fuzzy ≥0.85), mas os 3
exemplos do esqueleto só acionam a primeira, e a instrução "complete até 12" nunca pede os outros
dois casos. O golden-master congelaria um comportamento que nunca cobre 2/3 do módulo.
**Emenda:** o Step 1 passa a exigir explicitamente (a) um par com mesmo `tipo`+`numero` e `data`
diferente; (b) um par com `tipo`/`numero` diferentes e ementas quase idênticas após normalização
(≥60 chars, ratio ≥0,85). E um check no Step 3: conferir que `len(dedup_esperado.json) < 12` —
prova de que o colapso realmente aconteceu.

### MÉDIOS — entram na task correspondente

**A13 · `pandas` é dependência de produção não declarada.** ✅ [lente 2]
`app.py:18` faz `import pandas as pd` e `app.py:1221` usa `pd.DataFrame(...)` em produção. Nem o
`requirements.txt` nem o `pyproject.toml` do plano o declaram: hoje funciona **por acidente**,
porque o Streamlit arrasta pandas transitivamente.
**Emenda:** acrescentar `"pandas",` a `[project] dependencies`.

**A14 · O golden-master hasheia itens já mutados pelo dedup.** ✅ [lente 2]
`deduplicator._merge()` altera o registro sobrevivente **in-place** (a própria docstring diz
"Modified in-place"), mexendo em `ementa`, `nome`, `source`, `found_by`, `relevancia` e `link` —
todos colunas da planilha. Como `congelar` chama `_saida_dedup(itens)` e depois
`_sha_planilha(itens)` sobre a mesma lista, o sha da planilha é congelado sobre itens mutados.
**Emenda:** em `congelar` e em `comparar`, usar `_sha_planilha(_carregar_entrada())` — entrada
limpa recarregada do JSON — com o comentário
`# entrada limpa: o dedup muta os itens in-place (deduplicator._merge)`.

**A15 · `app.py` manda o usuário configurar um arquivo que deixou de ser lido.** ✅ [lente 1]
`app.py:291-296` instrui: "configure `GEMINI_API_KEY` em `.streamlit/secrets.toml`". A Task 6
apaga a leitura de `st.secrets`. O usuário segue a instrução, nada muda, e conclui que o app
quebrou. A Task 6 não listava `app.py` nos Files.
**Emenda:** acrescentar `app.py` aos Files da Task 6 e trocar a mensagem para citar
`BUSCADOR_LLM_BASE_URL` / `GEMINI_API_KEY` **como variáveis de ambiente**.

**A16 · O `_TODO.md` carrega duas lições que não existem em nenhum outro arquivo.** ✅ [lente 3]
A seção P3 tem dois registros `[x]` históricos, um deles uma **lição de ambiente**: criar repo no
GitHub exigiu `winget install --id GitHub.cli`, porque criar repositório é chamada de **API**, não
operação git, e o token do Credential Manager que faz o `push` funcionar não bastava. Substituir
o arquivo apaga isso — perda seca de informação, contra a regra global.
**Emenda:** Step 4a antes da substituição: (i) mover os dois registros `[x]` para o `log.md`, que
é append-only; (ii) acrescentar a lição do `winget`/API-vs-git ao `~/.claude/ENVIRONMENT.md`, na
seção de gh/GitHub que já existe.

**A17 · O `MEMORY.md` do repo-pai some da Task 7.** ✅ [lente 3]
A §11 da spec lista seis documentos a alterar, incluindo `projetos-nuati/MEMORY.md` (ponteiro
para esta solução). A Task 7 não o lista nos Files.
**Emenda:** acrescentar `~/Documents/projetos-nuati/MEMORY.md` aos Files da Task 7, com o
ponteiro para este repo.

**A18 · O `.gitignore` do Step 3 não é união, é lista nova.** ✅ [lente 3]
Descarta quatro entradas de A. Duas são inócuas aqui, mas **`.pytest_cache/` morde**: as Tasks 4,
5 e 6 rodam pytest na raiz de B, o cache aparece não-ignorado, e o `git add -A` das Tasks 7 e 8 o
commita.
**Emenda:** acrescentar `.pytest_cache/` e `desktop.ini` ao heredoc.

**A19 · O runner não tem prova de que detecta falha.** 📝 [lente 5]
O `golden_master.py` tem um Step dedicado a provar que o comparador detecta mudança; o runner
não tem o equivalente, então nada garante que ele não esteja sempre verde.
**Emenda:** novo step na Task 2 — introduzir uma falha temporária numa suíte (um `assert False`),
confirmar que o runner devolve `HOUVE FALHA` e exit 1, desfazer.

**A20 · `disponivel()` responde sobre configuração, não sobre alcançabilidade.** ✅ **adaptada** [lente 2]
`OpenAICompatBackend.disponivel()` devolve `bool(base_url and modelo)` e nunca toca a rede, mas
`app.py` toma 6 decisões de UI em cima de `is_available()`. Com a variável apontando para um host
sem rota, a UI anuncia LLM ativo e todo resultado vem da heurística.
**Emenda adaptada:** ⛔ **probe de rede REJEITADO** — custaria 6 chamadas por rerun do Streamlit,
e a A7 já derruba o hang de 60s para ~3s. Fica só (a) a docstring de uma linha em `disponivel()`
dizendo que informa **configuração, não alcançabilidade**, e (b) a mensagem da UI dizer
"LLM **configurado**", não "disponível".

**A21 · Pequenas inconsistências do próprio plano.** ✅ [lentes 1, 2 e 4]
- A seção **Files** da Task 1 declara `tests/golden/planilha_esperada.xlsx`, mas o código grava
  `planilha_sha256.txt`. Corrigir o nome.
- A mensagem de divergência do dedup só imprime contagens, mas o teste que a dispara compara
  listas de dicts: duas listas do mesmo tamanho com conteúdo diferente produzem a mensagem
  "esperado 9, obtido 9". Incluir o primeiro item divergente.
- O `Interfaces` da Task 4 promete que `pip install -e ".[dev]"` "instala app e ferramentas". Com
  `packages = []` a metade do app é falsa — o app roda por caminho, não por instalação. Corrigir
  a promessa.
- A tabela de comandos do `CLAUDE.md` e o docstring de `test_phase4.py:6` citam caminhos que a
  Task 8 renomeia. Incluir os dois na varredura da Task 8.
- O Step 4 da Task 1 só prova o ramo do dedup; acrescentar a prova do ramo do sha.

### REJEITADOS — com a razão, para não voltarem na rodada 2

| # | Achado | Por que foi rejeitado |
|---|---|---|
| R1-26 | Os 22 PNGs e `.playwright-mcp/` de A somem no merge | ✅ São artefatos não-versionados de sessão de teste, por desenho. O próprio revisor marcou `nao-vale`. Preservá-los versionaria lixo. |
| R1-34 | A Task 3 também faz `git mv`, contradizendo a justificativa da Task 8 | A Task 3 move **documentos**, a Task 8 move **código**; a preocupação com `git log --follow` é sobre o código. Inconsistência de redação minha, não defeito do plano. |
| R1-13 (parte) | `disponivel()` deveria sondar a rede | Custo desproporcional: 6 chamadas de rede por rerun do Streamlit para informação que a A7 já torna barata de descobrir. Ver A20, que ficou com a parte barata. |

---

## Global Constraints

- **Texto normativo NUNCA é parafraseado.** Título e ementa são copiados literalmente da fonte;
  texto derivado de LLM vai para campo separado.
- **O sistema roda inteiro sem LLM.** Nenhum caminho de código pode exigir chave de API nem
  endpoint alcançável.
- **Rastreabilidade é essência, não conveniência:** fonte, URL, data da coleta e decisão humana
  ficam gravadas.
- **Separar fato de sugestão:** marcar `📝` o que for proposta não validada.
- **UTF-8 explícito em todo `open()`.** Encoding padrão do Windows corrompe acento.
- **Rodar Python via Bash, não PowerShell** — caminho acentuado quebra no PowerShell 5.1.
- **Acima de 260 caracteres o Python falha em silêncio no Windows** (`isfile` devolve `False`).
- **Documentação move junto com o código.** Perda seca de docstring conta como regressão, mesmo
  com saída byte-idêntica.
- **Push a cada task fechada** (decisão D-C7).

---

## Linha de base medida (2026-09-16, antes de qualquer mudança)

✅ Verificado executando nesta máquina:

| Suíte | Runner | Resultado |
|---|---|---|
| `test_phase4.py` | pytest | **41 passed** |
| `test_comprehensive.py` | script | **98/98 PASS**, incluindo 3 testes LIVE contra LexML e TCU |
| `test_searchers.py` | script | **13/13 passed** |
| `test_llm_phase3.py` | script | **53/53 PASS** |

**Total: 205 testes, todos verdes** em 2026-09-16, antes de qualquer mudança.

⚠ **Três das quatro suítes não são pytest.** Usam um helper `record()` que imprime `PASS`/`FAIL`
e um contador final; não têm funções `def test_`. Só `test_phase4.py` é pytest. A Task 2 existe
para dar a elas um runner único e um código de saída confiável — sem isso, "a suíte continua
verde" não é verificável por máquina.

⚠ **E cada suíte-script usa um formato de resumo DIFERENTE.** ✅ Verificado na execução:

```
test_searchers.py      →  Results: 13/13 passed, 0/13 failed
test_llm_phase3.py     →  Total: 53  |  PASS: 53  |  FAIL: 0
test_comprehensive.py  →  Total: 98 | Passed: 98 | Failed: 0
```

Três formatos, com separadores e rótulos distintos (`passed` vs `PASS` vs `Passed`). O runner da
Task 2 precisa de um padrão por suíte — um regex genérico **falha silenciosamente** em duas
delas, reportando zero teste como se fosse sucesso.

### ⚠ Testes LIVE variam com a rede — não confundir com regressão

`test_searchers.py` e `test_comprehensive.py` fazem chamadas reais a LexML e TCU. Na execução de
16/09 o `test_comprehensive` teve os 3 LIVE verdes, enquanto o `test_searchers` registrou
*"integration tests returned empty results, likely API unavailable"* — e **passou assim mesmo**,
por degradação graciosa, que é comportamento correto e testado.

**Consequência para todo critério "mesmos números da linha de base":** o que precisa se manter
constante é o **total e o número de falhas** (`0`). A quantidade de itens efetivamente
retornados pelas APIs **pode variar** sem que nada tenha regredido. Se uma suíte falhar,
verifique primeiro se a causa é rede: rode de novo antes de acusar regressão.

---

## Estrutura de arquivos

**Depois do merge (Task 3), o código de A fica em `levantamento-normativos/`** — nome mantido de
propósito durante o merge, para não atrapalhar `git log --follow`. A renomeação para `buscador/`
é a Task 8, em commit separado.

| Caminho | Responsabilidade | Origem |
|---|---|---|
| `tools/golden_master.py` | congela e compara saídas determinísticas | **novo** (Task 1) |
| `tests/golden/*.json`, `*.xlsx` | saídas de referência congeladas | **novo** (Task 1) |
| `tools/run_all_tests.py` | runner único das 4 suítes, com exit code | **novo** (Task 2) |
| `levantamento-normativos/` | app Streamlit completo | **merge de A** (Task 3) |
| `pyproject.toml` | dependências e metadados | **novo** (Task 4) |
| `buscador/llm/backends.py` | protocolo `LLMBackend` + 3 implementações | **novo** (Task 5) |
| `buscador/llm/client.py` | 3 funções de A, com transporte trocado | **modificado de A** (Task 6) |
| `docs/historico/levantamento-v1/` | spec antiga de A, preservada | **movido** (Task 3) |
| `log.md`, `SESSION-ONBOARD-buscador.md`, `_TODO.md`, `CLAUDE.md` | duráveis corrigidos | **modificado** (Task 7) |

---

## Task 1: Golden-master das saídas determinísticas

Congela o comportamento **antes** de qualquer mudança. Sem isto, toda prova de não-regressão
vira leitura de código — que é exatamente o que a regra anti-regressão proíbe.

**Files:**
- Create: `tools/golden_master.py`
- Create: `tests/golden/entrada_fixa.json`
- Create: `tests/golden/dedup_esperado.json`
- Create: `tests/golden/planilha_esperada.xlsx`

**Interfaces:**
- Consumes: nada (roda contra o código de A, ainda no repo original)
- Produces: `congelar(origem: Path, destino: Path) -> None`,
  `comparar(origem: Path, destino: Path) -> list[str]` (lista de divergências; vazia = idêntico)

- [ ] **Step 1: Criar a entrada fixa**

`tests/golden/entrada_fixa.json` — 12 normativos cobrindo os casos que o dedup e o Excel tratam
de forma diferente: com número, sem número, com acento, link duplicado, título quase-igual,
relevância nos extremos.

```json
[
  {"nome": "Lei nº 13.709, de 14 de agosto de 2018", "tipo": "Lei", "numero": "13.709",
   "data": "14/08/2018", "orgao_emissor": "Presidência da República",
   "ementa": "Lei Geral de Proteção de Dados Pessoais (LGPD).",
   "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
   "source": "lexml", "found_by": "protecao de dados", "categoria": "Proteção de Dados",
   "situacao": "Vigente", "relevancia": 1.0},
  {"nome": "Lei n. 13.709/2018 (LGPD)", "tipo": "Lei", "numero": "13.709",
   "data": "14/08/2018", "orgao_emissor": "Presidencia da Republica",
   "ementa": "Dispoe sobre o tratamento de dados pessoais.",
   "link": "https://www.lexml.gov.br/urn/urn:lex:br:federal:lei:2018-08-14;13709",
   "source": "google", "found_by": "LGPD", "categoria": "Nao categorizado",
   "situacao": "Nao identificado", "relevancia": 0.9},
  {"nome": "COBIT 2019 Framework: Governance and Management Objectives", "tipo": "Framework/Padrao",
   "numero": "", "data": null, "orgao_emissor": "ISACA",
   "ementa": "Framework de governanca de TI.",
   "link": "https://www.isaca.org/resources/cobit", "source": "google",
   "found_by": "governanca de TI", "categoria": "Governança", "situacao": "Vigente",
   "relevancia": 0.0}
]
```

> ⚠ Os 3 acima são o esqueleto. **Complete até 12** cobrindo: dois com `numero` vazio e links
> diferentes (prova que o `id` cai para o link), dois com título idêntico e link diferente, um
> com `data` `None`, um com ementa vazia, um com `relevancia` exatamente `0.0` e outro `1.0`.

- [ ] **Step 2: Escrever o congelador e o comparador**

`tools/golden_master.py`:

```python
# -*- coding: utf-8 -*-
"""Congela e compara as saidas deterministicas do app.

Uso:
    python tools/golden_master.py congelar   # grava as referencias
    python tools/golden_master.py comparar   # exit 0 se identico, 1 se divergiu

As referencias sao a prova mecanica de nao-regressao. Comparar le BYTES, nunca
codigo: e a unica forma de provar que um refactor nao mudou o comportamento.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "levantamento-normativos"
GOLDEN = RAIZ / "tests" / "golden"

sys.path.insert(0, str(APP))


def _carregar_entrada() -> list:
    from models import NormativoResult

    dados = json.loads((GOLDEN / "entrada_fixa.json").read_text(encoding="utf-8"))
    return [NormativoResult(**d) for d in dados]


def _saida_dedup(itens: list) -> list[dict]:
    from deduplicator import deduplicate

    unicos = deduplicate(itens)
    # ordem estavel: o dedup nao promete ordem, o golden-master exige
    return sorted(
        [{"id": r.id, "nome": r.nome, "link": r.link} for r in unicos],
        key=lambda d: d["id"],
    )


def _sha_planilha(itens: list) -> str:
    from excel_export import export_to_excel

    buffer = export_to_excel(itens, topic="golden-master")
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def congelar() -> None:
    GOLDEN.mkdir(parents=True, exist_ok=True)
    itens = _carregar_entrada()
    (GOLDEN / "dedup_esperado.json").write_text(
        json.dumps(_saida_dedup(itens), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (GOLDEN / "planilha_sha256.txt").write_text(_sha_planilha(itens), encoding="utf-8")
    print("congelado em", GOLDEN)


def comparar() -> list[str]:
    itens = _carregar_entrada()
    divergencias: list[str] = []

    esperado = json.loads((GOLDEN / "dedup_esperado.json").read_text(encoding="utf-8"))
    obtido = _saida_dedup(itens)
    if obtido != esperado:
        divergencias.append(
            f"dedup divergiu: esperado {len(esperado)} unicos, obtido {len(obtido)}"
        )

    sha_esperado = (GOLDEN / "planilha_sha256.txt").read_text(encoding="utf-8").strip()
    sha_obtido = _sha_planilha(itens)
    if sha_obtido != sha_esperado:
        divergencias.append(f"planilha divergiu: {sha_esperado[:12]} -> {sha_obtido[:12]}")

    return divergencias


if __name__ == "__main__":
    acao = sys.argv[1] if len(sys.argv) > 1 else "comparar"
    if acao == "congelar":
        congelar()
        sys.exit(0)
    problemas = comparar()
    for p in problemas:
        print("DIVERGIU:", p)
    print("golden-master OK" if not problemas else f"{len(problemas)} divergencia(s)")
    sys.exit(1 if problemas else 0)
```

⚠ **Antes de rodar, confirme os nomes reais das funções.** O plano assume `deduplicate(itens)`
em `deduplicator.py` e `export_to_excel(itens, topic=...)` em `excel_export.py`. Verifique com
`grep -n "^def " levantamento-normativos/deduplicator.py levantamento-normativos/excel_export.py`
e ajuste as duas chamadas — **não invente assinatura**.

- [ ] **Step 3: Congelar e verificar que o comparador passa**

Run:
```bash
python tools/golden_master.py congelar
python tools/golden_master.py comparar
```
Expected: `golden-master OK`, exit 0.

- [ ] **Step 4: Provar que o comparador DETECTA mudança**

Um golden-master que nunca falha não prova nada. Altere temporariamente um valor em
`tests/golden/dedup_esperado.json` (troque um `id` por `"xxx"`), rode `comparar`, confirme
`DIVERGIU` e exit 1, depois desfaça a alteração.

Run: `python tools/golden_master.py comparar`
Expected: `DIVERGIU: dedup divergiu...`, exit 1. Depois de desfazer: exit 0.

- [ ] **Step 5: Commit**

```bash
git add tools/golden_master.py tests/golden/
git commit -m "test: golden-master das saidas deterministicas antes do merge"
git push origin master
```

---

## Task 2: Runner único das quatro suítes

**Files:**
- Create: `tools/run_all_tests.py`

**Interfaces:**
- Consumes: as 4 suítes de A (ainda no repo de origem até a Task 3)
- Produces: `python tools/run_all_tests.py` → exit 0 se tudo verde, 1 caso contrário;
  imprime uma tabela `suite | passed | failed`

- [ ] **Step 1: Escrever o runner**

`tools/run_all_tests.py`:

```python
# -*- coding: utf-8 -*-
"""Roda as 4 suites do app e devolve um exit code confiavel.

Tres das quatro suites sao scripts com helper record() e NAO sao pytest:
elas imprimem "Total: N | Passed: N | Failed: N" no fim. Uma e pytest.
Este runner normaliza as duas formas num unico resultado.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "levantamento-normativos"

# ⚠ Cada suite-script imprime o resumo num formato DIFERENTE. Verificado em
# 2026-09-16 rodando as tres. Um regex generico casa so uma delas e devolve
# zero teste para as outras duas, o que passaria como sucesso silencioso.
# Cada padrao captura (passed, failed) NESSA ordem.
SUITES_SCRIPT = {
    # Results: 13/13 passed, 0/13 failed
    "test_searchers.py": re.compile(r"Results:\s*(\d+)/\d+\s*passed,\s*(\d+)/\d+\s*failed"),
    # Total: 53  |  PASS: 53  |  FAIL: 0
    "test_llm_phase3.py": re.compile(r"Total:\s*\d+\s*\|\s*PASS:\s*(\d+)\s*\|\s*FAIL:\s*(\d+)"),
    # Total: 98 | Passed: 98 | Failed: 0
    "test_comprehensive.py": re.compile(
        r"Total:\s*\d+\s*\|\s*Passed:\s*(\d+)\s*\|\s*Failed:\s*(\d+)"
    ),
}
SUITES_PYTEST = ["test_phase4.py"]

PADRAO_PYTEST = re.compile(r"(\d+) passed")


def _rodar(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd, cwd=APP, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    linhas: list[tuple[str, int, int]] = []
    falhou = False

    for s, padrao in SUITES_SCRIPT.items():
        _, saida = _rodar([sys.executable, s])
        m = padrao.search(saida)
        if not m:
            # Resumo ilegivel e FALHA, nunca "zero teste, tudo bem": a suite pode
            # ter morrido antes de imprimir, ou mudado de formato.
            print(f"[ERRO] {s}: nao consegui ler o resumo final")
            falhou = True
            continue
        passed, failed = int(m.group(1)), int(m.group(2))
        linhas.append((s, passed, failed))
        if failed or passed == 0:
            falhou = True

    for s in SUITES_PYTEST:
        code, saida = _rodar([sys.executable, "-m", "pytest", s, "-q"])
        m = PADRAO_PYTEST.search(saida)
        passed = int(m.group(1)) if m else 0
        linhas.append((s, passed, 0 if code == 0 else 1))
        if code != 0:
            falhou = True

    largura = max(len(n) for n, _, _ in linhas)
    print()
    print(f"{'suite'.ljust(largura)} | passed | failed")
    print("-" * (largura + 18))
    for nome, p, f in linhas:
        print(f"{nome.ljust(largura)} | {str(p).rjust(6)} | {str(f).rjust(6)}")
    print()
    print("TUDO VERDE" if not falhou else "HOUVE FALHA")
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Rodar e registrar a linha de base completa**

Run: `python tools/run_all_tests.py`
Expected: `TUDO VERDE`, exit 0. **Anote os números de cada suíte** — eles são a linha de base
contra a qual toda task seguinte é comparada.

⚠ Se alguma suíte falhar **agora**, pare e investigue antes de seguir: uma falha pré-existente
precisa ser registrada como tal, ou vai ser confundida com regressão do merge.

- [ ] **Step 3: Commit**

```bash
git add tools/run_all_tests.py
git commit -m "test: runner unico das quatro suites com exit code"
git push origin master
```

---

## Task 3: Merge do histórico de A

**Files:**
- Modify: `.gitignore` (resolver conflito unindo as duas listas)
- Move: `spec/context.md`, `spec/implementation-plan/`, `spec/insights.md`, `spec/todos.md`
  → `docs/historico/levantamento-v1/`

**Interfaces:**
- Consumes: o repo de A em `~/Documents/projeto-nuati-normativos-levantamento`
- Produces: `levantamento-normativos/` versionado neste repo, com histórico de A preservado

✅ **Colisão verificada:** só o `.gitignore` conflita. `spec/` de A ocupa `spec/context.md` e
`spec/implementation-plan/`; `spec/` de B ocupa `spec/buscador/` — caminhos distintos.

- [ ] **Step 1: Adicionar A como remoto e buscar**

```bash
cd ~/Documents/solucoes/buscador-normativos
git remote add levantamento ~/Documents/projeto-nuati-normativos-levantamento
git fetch levantamento
git log --oneline levantamento/main
```
Expected: os 2 commits de A (`b12b39a`, `eb91277`).

- [ ] **Step 2: Merge, esperando conflito só no .gitignore**

```bash
git merge levantamento/main --allow-unrelated-histories --no-commit
git status --short
```
Expected: `AA .gitignore` e nada mais em conflito. **Se conflitar outro arquivo, pare** — a
premissa da Task mudou e precisa ser reavaliada.

- [ ] **Step 3: Resolver o .gitignore unindo as duas listas**

```bash
cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/

# Ambientes virtuais
.venv/
venv/
env/

# Segredos — nunca commitar chave real
.streamlit/secrets.toml
.env

# Dados e banco locais
dados/
*.db

# IDE / Editor
.vscode/
.idea/
*.swp
*.swo
*~

# Sistema
.DS_Store
Thumbs.db

# Artefatos de sessao de teste
.playwright-mcp/
test_*.png
EOF
git add .gitignore
```

- [ ] **Step 4: Mover a spec antiga de A para o histórico**

```bash
mkdir -p docs/historico/levantamento-v1
git mv spec/context.md spec/insights.md spec/todos.md docs/historico/levantamento-v1/
git mv spec/implementation-plan docs/historico/levantamento-v1/implementation-plan
```

- [ ] **Step 5: Commitar o merge**

```bash
git commit -m "merge: traz o app levantamento-normativos preservando historico

O codigo de A entra por --allow-unrelated-histories para manter autoria e
cadeia de commits. Unico conflito real foi o .gitignore, resolvido unindo
as duas listas. A spec antiga de A foi para docs/historico/levantamento-v1/
para nao competir com o spec/ vivo deste repo."
git push origin master
```

- [ ] **Step 6: Provar que nada regrediu**

```bash
python tools/run_all_tests.py
python tools/golden_master.py comparar
```
Expected: `TUDO VERDE` e `golden-master OK`, ambos exit 0, **com os mesmos números da Task 2**.

---

## Task 4: Ambiente reproduzível (emenda R1-02)

Hoje as dependências estão instaladas **globalmente** nesta máquina — o projeto não declara
nada instalável. A emenda R1-02 registrou que isso quebra o ciclo TDD logo no primeiro passo.

**Files:**
- Create: `pyproject.toml`
- Delete: `levantamento-normativos/requirements.txt` (conteúdo migra para o `pyproject.toml`)

**Interfaces:**
- Produces: `pip install -e ".[dev]"` instala app e ferramentas de teste

- [ ] **Step 1: Escrever o pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "buscador-normativos"
version = "0.1.0"
description = "Constroi o acervo de criterio de uma acao de controle"
requires-python = ">=3.13"
dependencies = [
    "streamlit>=1.33.0",
    "requests",
    "openpyxl",
    "beautifulsoup4",
    "ddgs",
    "googlesearch-python",
]

[project.optional-dependencies]
llm-gemini = ["google-genai"]
dev = ["pytest>=9.0"]

[tool.setuptools]
packages = []
```

⚠ `google-genai` sai das dependências obrigatórias e vira **extra**. Isso materializa o
requisito B3: instalar o projeto não traz nenhum SDK de LLM.

- [ ] **Step 2: Criar o venv e instalar**

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
```
Expected: instalação sem erro; `google-genai` **não** instalado.

- [ ] **Step 3: Provar que a suíte roda no venv, sem LLM**

```bash
.venv/Scripts/python tools/run_all_tests.py
```
Expected: `TUDO VERDE`. ⚠ `test_llm_phase3.py` precisa passar **sem** o SDK do Gemini
instalado — é a primeira prova real do requisito B3. Se falhar, o problema é do código, não do
ambiente: registre e corrija antes de seguir.

- [ ] **Step 4: Commit**

```bash
git rm levantamento-normativos/requirements.txt
git add pyproject.toml
git commit -m "build: pyproject com SDK de LLM como extra opcional (R1-02)"
git push origin master
```

---

## Task 5: Protocolo de backend de LLM

**Files:**
- Create: `levantamento-normativos/llm/backends.py`
- Test: `levantamento-normativos/test_backends.py`

**Interfaces:**
- Produces: `LLMBackend` (Protocol com `nome: str`, `disponivel() -> bool`,
  `gerar(prompt: str, temperature: float, max_tokens: int) -> Optional[str]`),
  `NullBackend`, `OpenAICompatBackend`, `GeminiBackend`,
  `escolher_backend() -> LLMBackend`

- [ ] **Step 1: Escrever o teste que falha**

`levantamento-normativos/test_backends.py`:

```python
import pytest
from llm.backends import (
    LLMBackend, NullBackend, OpenAICompatBackend, escolher_backend,
)


def test_null_backend_nunca_esta_disponivel():
    b = NullBackend()
    assert b.disponivel() is False
    assert b.gerar("qualquer prompt", 0.0, 100) is None


def test_null_backend_satisfaz_o_protocolo():
    assert isinstance(NullBackend(), LLMBackend)


def test_openai_compat_satisfaz_o_protocolo():
    b = OpenAICompatBackend(base_url="http://x:1234/v1", modelo="m")
    assert isinstance(b, LLMBackend)


def test_openai_compat_indisponivel_sem_base_url():
    assert OpenAICompatBackend(base_url="", modelo="m").disponivel() is False


def test_openai_compat_monta_o_payload_correto(monkeypatch):
    capturado = {}

    class RespostaFake:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": "resposta"}}]}
        def raise_for_status(self):
            pass

    def post_fake(url, json=None, timeout=None, headers=None):
        capturado["url"] = url
        capturado["json"] = json
        return RespostaFake()

    import llm.backends as mod
    monkeypatch.setattr(mod.requests, "post", post_fake)

    b = OpenAICompatBackend(base_url="http://x:1234/v1", modelo="google/gemma-4")
    assert b.gerar("oi", 0.0, 50) == "resposta"
    assert capturado["url"] == "http://x:1234/v1/chat/completions"
    assert capturado["json"]["model"] == "google/gemma-4"
    assert capturado["json"]["messages"] == [{"role": "user", "content": "oi"}]
    assert capturado["json"]["temperature"] == 0.0
    assert capturado["json"]["max_tokens"] == 50


def test_openai_compat_devolve_none_em_erro_de_rede(monkeypatch):
    import llm.backends as mod

    def post_quebrado(*a, **k):
        raise mod.requests.exceptions.ConnectionError("sem rota")

    monkeypatch.setattr(mod.requests, "post", post_quebrado)
    b = OpenAICompatBackend(base_url="http://10.10.111.125:1234/v1", modelo="m")
    assert b.gerar("oi", 0.0, 50) is None


def test_escolher_backend_devolve_null_sem_configuracao(monkeypatch):
    for var in ("BUSCADOR_LLM_BASE_URL", "GEMINI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    assert isinstance(escolher_backend(), NullBackend)


def test_escolher_backend_prefere_o_local_quando_configurado(monkeypatch):
    monkeypatch.setenv("BUSCADOR_LLM_BASE_URL", "http://10.10.111.125:1234/v1")
    monkeypatch.setenv("BUSCADOR_LLM_MODEL", "google/gemma-4")
    b = escolher_backend()
    assert isinstance(b, OpenAICompatBackend)
    assert b.modelo == "google/gemma-4"
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `.venv/Scripts/python -m pytest levantamento-normativos/test_backends.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'llm.backends'`

- [ ] **Step 3: Implementar**

`levantamento-normativos/llm/backends.py`:

```python
# -*- coding: utf-8 -*-
"""Backends de LLM, atras de um protocolo unico.

O sistema roda INTEIRO sem LLM (requisito B3): NullBackend e o padrao e
nenhum caminho de codigo exige chave nem endpoint alcancavel.

Producao usa o servidor local da Camara, que e OpenAI-compativel. Gemini
permanece como alternativa configuravel. A escolha e por variavel de
ambiente, nunca fixa no codigo.
"""
from __future__ import annotations

import logging
import os
from typing import Optional, Protocol, runtime_checkable

import requests

logger = logging.getLogger(__name__)

TIMEOUT_PADRAO = 60


@runtime_checkable
class LLMBackend(Protocol):
    nome: str

    def disponivel(self) -> bool: ...

    def gerar(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]: ...


class NullBackend:
    """Backend inerte. Sempre indisponivel, sempre devolve None.

    NAO e um erro nem um modo degradado excepcional: e o padrao. As funcoes
    de alto nivel ja tem heuristica de fallback para quando nao ha LLM.
    """

    nome = "nulo"

    def disponivel(self) -> bool:
        return False

    def gerar(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        return None


class OpenAICompatBackend:
    """Qualquer servidor que fale a API de chat da OpenAI.

    Cobre o LM Studio do servidor local da Camara (10.10.111.125:1234/v1) e
    tambem vLLM, Ollama e afins. A chave e opcional: servidor local costuma
    nao exigir nenhuma.
    """

    nome = "openai-compat"

    def __init__(self, base_url: str, modelo: str, api_key: str = "") -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.modelo = modelo
        self.api_key = api_key

    def disponivel(self) -> bool:
        return bool(self.base_url and self.modelo)

    def gerar(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        if not self.disponivel():
            return None
        cabecalhos = {"Content-Type": "application/json"}
        if self.api_key:
            cabecalhos["Authorization"] = f"Bearer {self.api_key}"
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.modelo,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=TIMEOUT_PADRAO,
                headers=cabecalhos,
            )
            resp.raise_for_status()
            dados = resp.json()
            conteudo = dados["choices"][0]["message"]["content"]
            return conteudo or None
        except Exception as e:
            logger.warning("Backend %s falhou: %s", self.nome, e)
            return None


class GeminiBackend:
    """Alternativa em nuvem. Mantida para uso fora da rede da Camara.

    ⚠ O tier gratuito limita a 15 RPM e 1.000 chamadas/dia, o que morde
    exatamente no caso de uso que originou o projeto: acervo de 100+ itens.
    """

    nome = "gemini"

    def __init__(self, api_key: str, modelo: str = "gemini-2.5-flash-lite") -> None:
        self.api_key = api_key
        self.modelo = modelo
        self._cliente = None

    def disponivel(self) -> bool:
        if not self.api_key:
            return False
        try:
            from google import genai  # noqa: F401
        except ImportError:
            logger.info("google-genai nao instalado — backend gemini indisponivel.")
            return False
        return True

    def gerar(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        if not self.disponivel():
            return None
        try:
            from google import genai
            from google.genai import types

            if self._cliente is None:
                self._cliente = genai.Client(api_key=self.api_key)
            resp = self._cliente.models.generate_content(
                model=self.modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature, max_output_tokens=max_tokens
                ),
            )
            return resp.text or None
        except Exception as e:
            logger.warning("Backend %s falhou: %s", self.nome, e)
            return None


def escolher_backend() -> LLMBackend:
    """Escolhe o backend pela configuracao de ambiente.

    Ordem: servidor OpenAI-compativel > Gemini > nulo. O nulo e alcancavel
    sempre, entao esta funcao nunca levanta excecao nem devolve None.
    """
    base_url = os.environ.get("BUSCADOR_LLM_BASE_URL", "").strip()
    if base_url:
        return OpenAICompatBackend(
            base_url=base_url,
            modelo=os.environ.get("BUSCADOR_LLM_MODEL", "google/gemma-4").strip(),
            api_key=os.environ.get("BUSCADOR_LLM_API_KEY", "").strip(),
        )

    chave_gemini = os.environ.get("GEMINI_API_KEY", "").strip()
    if chave_gemini:
        return GeminiBackend(api_key=chave_gemini)

    return NullBackend()
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `.venv/Scripts/python -m pytest levantamento-normativos/test_backends.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add levantamento-normativos/llm/backends.py levantamento-normativos/test_backends.py
git commit -m "feat(llm): protocolo de backend com OpenAI-compativel, Gemini e nulo"
git push origin master
```

---

## Task 6: Ligar o cliente existente ao novo backend

Troca **só o transporte**. As ~400 linhas de prompt, parsing e fallback de A ficam intactas —
é o ponto inteiro da consolidação.

**Files:**
- Modify: `levantamento-normativos/llm/gemini_client.py` (linhas 28-48, 74-145)

**Interfaces:**
- Consumes: `escolher_backend()` da Task 5
- Produces: as 3 funções públicas **sem mudança de assinatura** —
  `expand_topic_to_keywords(topic) -> list[str]`,
  `score_relevance(topic, results, keywords=None) -> list[float]`,
  `categorize_results(topic, results) -> list[str]`, e `is_available() -> bool`

- [ ] **Step 1: Escrever o teste que falha**

Acrescente a `levantamento-normativos/test_backends.py`:

```python
def test_cliente_usa_o_backend_injetado(monkeypatch):
    import llm.gemini_client as cli

    class BackendFake:
        nome = "fake"
        def disponivel(self): return True
        def gerar(self, prompt, temperature, max_tokens):
            return '["palavra um", "palavra dois"]'

    monkeypatch.setattr(cli, "_backend", BackendFake())
    assert cli.is_available() is True
    assert cli.expand_topic_to_keywords("protecao de dados") == ["palavra um", "palavra dois"]


def test_cliente_cai_na_heuristica_quando_backend_indisponivel(monkeypatch):
    import llm.gemini_client as cli
    from llm.backends import NullBackend

    monkeypatch.setattr(cli, "_backend", NullBackend())
    assert cli.is_available() is False
    # score_relevance sem LLM e com keywords deve usar a heuristica, nao quebrar
    notas = cli.score_relevance(
        "protecao de dados",
        [{"nome": "Lei X", "ementa": "trata de protecao de dados pessoais"}],
        keywords=["protecao", "dados"],
    )
    assert len(notas) == 1
    assert 0.0 <= notas[0] <= 1.0
```

⚠ **Confirme antes de escrever o teste:** o primeiro teste assume que
`expand_topic_to_keywords` faz parsing de um array JSON devolvido pelo modelo (via
`_parse_json_array`, linha ~188). Verifique com
`grep -n "_parse_json_array" levantamento-normativos/llm/gemini_client.py` e ajuste o valor que
o `BackendFake` devolve para o formato que a função realmente espera. **Não invente o formato** —
se o teste fake não casar com o parser real, ele passa a testar o fake, não o código.

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `.venv/Scripts/python -m pytest levantamento-normativos/test_backends.py -v`
Expected: FAIL — `gemini_client` ainda não tem atributo `_backend`.

- [ ] **Step 3: Substituir o bloco de SDK e o `_generate`**

Em `llm/gemini_client.py`, **remova** o bloco de import de SDK (linhas 28-48), a resolução de
chave via `st.secrets` (linhas ~56-60), `_get_client()` (74-105) e o corpo de `_generate`
(106-145). **No lugar**, logo após o `logger`:

```python
from llm.backends import LLMBackend, escolher_backend

# Backend unico, escolhido por ambiente. Trocavel em teste por monkeypatch.
# Antes isto era acoplado ao SDK do Gemini e lia a chave de st.secrets, o que
# amarrava a camada de LLM ao Streamlit sem necessidade.
_backend: LLMBackend = escolher_backend()

# Mantido por compatibilidade com o codigo que loga qual modelo esta em uso.
MODEL_NAME = getattr(_backend, "modelo", _backend.nome)


def _generate(prompt: str, temperature: float = 0.0, max_tokens: int = 1024) -> Optional[str]:
    """Gera texto pelo backend configurado.

    Unico ponto por onde as tres funcoes publicas falam com o modelo.
    Devolve None quando nao ha LLM — as chamadoras ja tratam esse caso com
    heuristica propria, entao ausencia de LLM nunca e erro.
    """
    return _backend.gerar(prompt, temperature, max_tokens)


def is_available() -> bool:
    """Informa se ha LLM utilizavel. Nunca levanta excecao."""
    return _backend.disponivel()
```

⚠ **Preservação de documentação (regra global):** as docstrings de `_get_client` e do
`_generate` antigo explicavam a prioridade `st.secrets > env var > vazio` e a diferença entre os
dois SDKs. Essa explicação **não some**: ela está reescrita acima e em `backends.py`. Antes de
commitar, rode
`git show levantamento-v1-streamlit:levantamento-normativos/llm/gemini_client.py | sed -n '28,150p'`
e confirme que nenhuma explicação foi perdida sem herdeiro.

- [ ] **Step 4: Rodar e confirmar que passa**

Run:
```bash
.venv/Scripts/python -m pytest levantamento-normativos/test_backends.py -v
.venv/Scripts/python tools/run_all_tests.py
.venv/Scripts/python tools/golden_master.py comparar
```
Expected: todos verdes, **com os mesmos números da Task 2**.

- [ ] **Step 5: Commit**

```bash
git add levantamento-normativos/llm/gemini_client.py levantamento-normativos/test_backends.py
git commit -m "refactor(llm): troca o transporte por backend injetavel, preserva os prompts

As ~400 linhas de prompt, parsing e fallback ficam intactas. Some o
acoplamento a st.secrets, que amarrava a camada de LLM ao Streamlit."
git push origin master
```

---

## Task 7: Corrigir os documentos com premissa falsa

Afirmação sabidamente falsa deixada de pé faz o próximo agente repetir o erro.

**Files:**
- Modify: `log.md`, `SESSION-ONBOARD-buscador.md`, `_TODO.md`, `CLAUDE.md`
- Modify: `docs/superpowers/specs/2026-09-08-buscador-normativos-design.md`

- [ ] **Step 1: Corrigir a spec de 08/09**

Em `docs/superpowers/specs/2026-09-08-buscador-normativos-design.md`, acrescente logo abaixo do
título:

```markdown
> ⚠ **CORREÇÃO (2026-09-16).** A §1 desta spec afirma que só existe um formatador sem chamadas
> de rede. **Isso é falso.** O app `levantamento-normativos` existe desde março de 2026, tem
> 6.533 linhas e busca por API (LexML SRU/CQL, TCU Dados Abertos, Google CSE/DuckDuckGo). A
> varredura de 08/09 não cobriu `~/Documents/projeto-nuati-normativos-levantamento/`.
> **Prova:** suíte executada em 16/09 — 41 passed (pytest) e 98/98 PASS, incluindo três testes
> LIVE contra LexML e TCU, todos verdes.
> A decisão **B2** (FastAPI sobre Streamlit) também foi **revertida**, por ter sido tomada sob
> essa premissa falsa. Ver `2026-09-16-consolidacao-buscador-design.md`, que **prevalece**.
```

- [ ] **Step 2: Corrigir o `log.md`**

Acrescente no topo (o formato do arquivo é "mais recente primeiro"):

```markdown
## [2026-09-16] consolidação | o artefato original existia — correção de premissa

A entrada de 08/09 afirma que "o artefato original não existe" e que o buscador "nunca foi
código". **Está errado.** O app `levantamento-normativos` existia desde março: 6.533 linhas,
busca por API, revisões de segurança e qualidade aplicadas. A varredura de 08/09 cobriu
`solucoes/`, as skills e `projeto-AI-com-IA/`, mas **não** a pasta onde o app mora.

**Prova medida em 16/09:** `test_phase4.py` 41 passed; `test_comprehensive.py` 98/98 PASS,
com `LIVE: LexML search`, `LIVE: TCU search` e `LIVE: End-to-end search + export` verdes.
Enquanto isso, a emenda R1-10 verificou que duas das três rotas de scraping planejadas
retornam **404** hoje.

Consequência: o projeto deixa de ser greenfield. O código de A entra por merge com histórico
preservado, a decisão B2 é revertida, e o escopo cai de 16 tasks para 7 features sobre código
que roda. Ver a spec de consolidação de 16/09.
```

- [ ] **Step 3: Corrigir o `SESSION-ONBOARD-buscador.md`**

Reescreva a §2 (fase), o item 2 da §3 (o achado falso) e a §5 (próximo movimento):
- §2: a fase deixa de ser "planejamento concluído, zero linha de código" e passa a refletir o
  merge feito e os números da suíte.
- §3 item 2: substituir "o artefato original não existe" pela correção e pela prova.
- §5: o próximo movimento passa a ser o Plano 2 (features F1-F7).

- [ ] **Step 4: Substituir o `_TODO.md`**

As 16 tasks saem; entram as 7 tasks deste plano (marcadas como feitas) e as 7 features do
Plano 2. Mantenha a seção "Fora de escopo", atualizada com as decisões do board de 16/09.

- [ ] **Step 5: Atualizar o `CLAUDE.md`**

Substitua a seção "Convenções" por:

```markdown
## Convenções

- **Texto normativo NUNCA é parafraseado.** Título e ementa são copiados literalmente da
  fonte; texto derivado de LLM vai para campo separado (`ementa_llm`).
- **Procedência é obrigatória** em todo resultado: `catalogada` ou `web-aberta`.
- **O sistema roda inteiro sem LLM.** Nenhum caminho de código pode exigir chave de API.
  `pip install -e .` não traz SDK de LLM nenhum — Gemini é o extra `[llm-gemini]`.
- **Rastreabilidade é a essência**, não conveniência.
- **Separar fato de sugestão:** marcar `📝` o que for proposta não validada.
- Python 3.13, UTF-8 explícito em todo `open()`, rodar via **Bash** (não PowerShell).
- Acima de **260 caracteres** o Python falha em silêncio no Windows.

## Arquitetura (decidida em 2026-09-16)

- **Base: Streamlit**, não FastAPI. A decisão B2 de 08/09 foi revertida — ela escolheu
  FastAPI sem saber que o app `levantamento-normativos` já existia. Ver a spec de
  consolidação de 16/09.
- **LLM por backend injetável** (`buscador/llm/backends.py`): OpenAI-compatível para o
  servidor local da Câmara, Gemini como alternativa, `NullBackend` como padrão inerte.
  Configuração por ambiente: `BUSCADOR_LLM_BASE_URL`, `BUSCADOR_LLM_MODEL`,
  `BUSCADOR_LLM_API_KEY`, `GEMINI_API_KEY`.
- **Agrupamento é aditivo**: nunca remove, oculta ou filtra item da visão do usuário.

## Comandos

| Comando | O que faz |
|---|---|
| `.venv/Scripts/python tools/run_all_tests.py` | roda as 4 suítes, exit 0 se tudo verde |
| `.venv/Scripts/python tools/golden_master.py comparar` | prova de não-regressão |
| `.venv/Scripts/python -m streamlit run buscador/app.py` | sobe o app |
```

- [ ] **Step 6: Verificar que nenhuma afirmação falsa sobrou**

```bash
grep -rniE "nunca foi codigo|nao existe|apenas um formatador|greenfield" \
  log.md SESSION-ONBOARD-buscador.md _TODO.md CLAUDE.md docs/superpowers/specs/
```
Expected: só ocorrências **dentro de blocos de correção** que explicam o erro. Qualquer
afirmação solta ainda de pé é falha desta task.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "docs: corrige a premissa falsa de 08/09 com a prova medida"
git push origin master
```

---

## Task 8: Renomear o pacote e fechar a fase

**Files:**
- Move: `levantamento-normativos/` → `buscador/`

- [ ] **Step 1: Renomear em commit isolado**

Commit separado, para não atrapalhar `git log --follow` sobre o merge da Task 3.

```bash
git mv levantamento-normativos buscador
```

- [ ] **Step 2: Ajustar os caminhos nas ferramentas**

Em `tools/golden_master.py` e `tools/run_all_tests.py`, trocar
`RAIZ / "levantamento-normativos"` por `RAIZ / "buscador"`.

- [ ] **Step 3: Provar que nada quebrou**

```bash
.venv/Scripts/python tools/run_all_tests.py
.venv/Scripts/python tools/golden_master.py comparar
```
Expected: `TUDO VERDE` e `golden-master OK`, **com os mesmos números da Task 2**.

- [ ] **Step 4: Auditoria de preservação de documentação (gate explícito)**

Não é formalidade: é o gate que o golden-master **não** consegue ver, porque comentário não
afeta saída.

```bash
git diff levantamento-v1-streamlit HEAD -- '*.py' | grep -E "^-\s*(#|\"\"\"|'''|\s*[A-Z])" | head -50
```

Para cada linha de explicação removida, confirme que ela tem **herdeiro** — foi para outro
módulo, para uma docstring nova, ou para a spec. Perda seca é regressão e precisa ser
restaurada antes do commit.

- [ ] **Step 5: Commit e fechamento**

```bash
git add -A
git commit -m "refactor: renomeia levantamento-normativos para buscador"
git push origin master
```

---

## Task 9: Aposentar o repo A (decisão D-C6)

⛔ **Só execute depois de TODOS os critérios de pronto abaixo estarem verdes**, e
**confirme com o Rodrigo no momento** — arquivar é ação externa, visível a terceiros, e a
autorização da D-C6 foi condicionada a "depois de provado".

**Files:**
- Create: `README.md` no repo A (`~/Documents/projeto-nuati-normativos-levantamento`)

- [ ] **Step 1: Provar que o histórico de A sobrevive aqui**

```bash
cd ~/Documents/solucoes/buscador-normativos
git log --oneline | grep -E "b12b39a|eb91277"
```
Expected: os dois commits de A presentes neste repo. **Se não estiverem, NÃO arquive** — o
merge não preservou o histórico e a Task 3 precisa ser refeita.

- [ ] **Step 2: Deixar o ponteiro no repo A**

```bash
cd ~/Documents/projeto-nuati-normativos-levantamento
cat > README.md <<'EOF'
# levantamento-normativos — ARQUIVADO

Este projeto foi consolidado em **[buscador-normativos](https://github.com/rodilpinto/buscador-normativos)**
em 2026-09-16. Todo o código e o histórico de commits vivem lá.

O estado desta versão está preservado na tag anotada `levantamento-v1-streamlit`.

Não faça alterações aqui. Continue o trabalho no repo consolidado.
EOF
git add README.md
git commit -m "docs: arquiva o repo, aponta para buscador-normativos"
git push origin main
git push origin levantamento-v1-streamlit
```

⚠ O `git push origin levantamento-v1-streamlit` é obrigatório: a tag hoje só existe **local**.
Sem ela no remoto, arquivar perde o ponto de restauração nomeado.

- [ ] **Step 3: Arquivar no GitHub**

```bash
gh repo archive rodilpinto/levantamento-normativos --yes
gh repo view rodilpinto/levantamento-normativos --json isArchived
```
Expected: `{"isArchived":true}`. Reversível a qualquer momento por `gh repo unarchive`.

---

## Critérios de pronto da Fase 1

- [ ] `python tools/run_all_tests.py` devolve `TUDO VERDE`, com **205 passed e 0 failed**
      (13 + 53 + 98 + 41). Variação no que as APIs retornam é aceitável; falha não é.
- [ ] `python tools/golden_master.py comparar` devolve exit 0
- [ ] `git log --oneline | grep b12b39a` encontra o commit inicial de A neste repo
- [ ] `pip install -e .` **não** instala nenhum SDK de LLM
- [ ] A suíte passa com `BUSCADOR_LLM_BASE_URL` e `GEMINI_API_KEY` ambos vazios
- [ ] O grep da Task 7 Step 6 não encontra afirmação falsa solta
- [ ] A auditoria da Task 8 Step 4 não encontra explicação perdida sem herdeiro

## O que a Fase 2 recebe

Um app funcionando neste repo, com histórico preservado, ambiente reproduzível, LLM trocável e
duas provas mecânicas de não-regressão já montadas. As 7 features (F1 procedência · F2
vinculação · F3 pré-marcação · F4 já-tenho · F5 download/organização · F6 SQLite+planilha ·
F7 agrupamento semântico) entram sobre essa base, cada uma com o golden-master como rede.
