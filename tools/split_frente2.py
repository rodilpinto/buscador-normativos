# -*- coding: utf-8 -*-
"""Corta o plano v4 da frente 2 em arquivos por task (verbatim) + reference + overview.

Regra herdada do split de 10/09: o PLANO segue fonte de verdade; os arquivos sao copia.
Cobertura verificada aqui: toda linha nao-vazia e nao '---' do plano cai em exatamente um arquivo.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent   # tools/ -> raiz do repo
PLANO_REL = "docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md"
OUT_REL = "spec/frente2-honestidade-fontes"
OUT = REPO / OUT_REL
linhas = (REPO / PLANO_REL).read_text(encoding="utf-8").split("\n")
N = len(linhas)


def L(i):  # 1-indexed
    return linhas[i - 1]


def aparar(ini, fim):
    """Tira linhas vazias e '---' das pontas; devolve (ini, fim) reais."""
    while ini <= fim and L(ini).strip() in ("", "---"):
        ini += 1
    while fim >= ini and L(fim).strip() in ("", "---"):
        fim -= 1
    return ini, fim


def fatia(ini, fim):
    return "\n".join(linhas[ini - 1:fim])


cabecalhos = [i for i in range(1, N + 1) if L(i).startswith("### Task ")]
self_review = next(i for i in range(1, N + 1) if L(i).startswith("## Self-review"))
global_ini = next(i for i in range(1, N + 1) if L(i) == "## Global Constraints")
triagem_ini = next(i for i in range(1, N + 1) if L(i).startswith("## Rodada 1 adversarial"))
assert len(cabecalhos) == 10, cabecalhos

TASKS = [
    # (slug, fase, titulo curto, depende_de [(n, porque)], compartilha, criterios)
    ("01-vocabulario-honestidade", "Fase 1 — Fundação",
     "vocabulário fechado, `redigir()`, `rotulo_status()`, `statuses_para_falha_total()`, `FonteIndisponivel`, `SOURCE_ID`",
     [],
     "`models.py` (T4 volta nele, só docstring) · `test_phase4.py` (T7, T8, T9) · `tools/run_all_tests.py` (todas) · spec (T4)",
     [
         "`python -m pytest test_phase4.py -q` (em `levantamento-normativos/`) → **`58 passed`** (41 + 17 novos) — plano Step 5.",
         "`MOTIVOS` e `ORIGENS_RELEVANCIA` iguais aos conjuntos das Interfaces; `KeywordStatus` rejeita motivo inventado e redige `detalhe`/`error_message` **também em mutação pós-construção** (testes `TestVocabularioHonestidade`).",
         "`FonteIndisponivel` com motivo desconhecido vira `erro_interno`, sem levantar; `str(e)` é dinâmico.",
         "`BASELINE[\"test_phase4.py\"] = 58`; `_rodar` do runner passa `env` com `GEMINI_API_KEY` e `GOOGLE_API_KEY` vazias (Step 6).",
         "Spec §3.1 emendada com a lista de `MOTIVOS` e a nota `⚠ Emendado em 22/09` (Step 6).",
         "Runner TUDO VERDE (total previsto **222**); `golden_master.py comparar` OK; os 2 comandos de auditoria lidos inteiros; commit + push (Step 7).",
     ]),
    ("02-lexml-falhas-declaradas", "Fase 2 — Fontes honestas",
     "LexML declara bloqueio, timeout, 5xx, paginação parcial e `nao_consultada`",
     [(1, "`FonteIndisponivel`, campos `motivo`/`detalhe`/`parcial` de `KeywordStatus`, `redigir`, `SOURCE_ID` na base")],
     "`tests/test_fontes_indisponiveis.py` (**criado aqui**; T3, T4, T5 acrescentam) · `test_comprehensive.py` (T3, T4) · runner",
     [
         "`python -m pytest tests/test_fontes_indisponiveis.py -q` → **`16 passed`** (Step 12).",
         "`python test_comprehensive.py | tail -3` → `Total: 98 | Passed: 98 | Failed: 0`; `python test_searchers.py | tail -2` → `13/13 passed` (**anotar o tempo**, era ~390s); `test_phase4.py` → `58 passed`.",
         "Cenário real de 22/09 (primário = desafio HTML, fallbacks = 404): as 3 keywords saem `bloqueio_waf`, com 3 requisições no total, `retried=False` e `retry pulado` no detalhe (teste `test_lexml_cenario_real_…`).",
         "`git grep -n \"_search_keyword_safe\" -- '*.py'` → só `lexml_searcher.py` e os testes (Step 11c).",
         "Runner: `SUITES_PYTEST` inclui a suíte nova; `BASELINE[\"tests/test_fontes_indisponiveis.py\"] = 16`; TUDO VERDE (total **238**); golden OK; auditoria; commit + push.",
     ]),
    ("03-tcu-falhas-declaradas", "Fase 2 — Fontes honestas",
     "TCU classifica 5xx/4xx/503/HTML, declara paginação parcial e classifica por endpoint",
     [(1, "`FonteIndisponivel`, `KeywordStatus` novos"),
      (2, "a suíte `tests/test_fontes_indisponiveis.py` (`RespostaFake`, `DESAFIO_HTML`, fixture `autouse`) e o registro dela no runner")],
     "`tests/test_fontes_indisponiveis.py` · `test_comprehensive.py` · `requirements.txt` · runner",
     [
         "Suíte nova → **`25 passed, 1 xfailed`** (26 coletados; o `xfail strict` é destravado na T4) — Step 5.",
         "`test_comprehensive.py` → 98/98; `test_searchers.py` → 13/13.",
         "`tzdata` no `requirements.txt`; `git grep -n \"_fetch_all_pages\\|_request_with_retry\" -- '*.py'` sem call site além dos previstos (Step 4).",
         "O `detalhe` do TCU é gravado **sempre**, inclusive em `empty`, e conta `N sem sumário` (R3-H5, R3-B1).",
         "`BASELINE` da suíte = 25; runner TUDO VERDE (total **247**); golden OK; auditoria; commit + push.",
     ]),
    ("04-tcu-esquema-real", "Fase 2 — Fontes honestas",
     "TCU lê o esquema REAL do acórdão (⚠ emenda à spec §3.7)",
     [(3, "`_texto_do_acordao`, o teste `xfail` a destravar, o dublê `_tcu_com` e o formato do `detalhe`")],
     "`tcu_searcher.py` (T3) · `models.py` (docstring de `situacao`) · `test_comprehensive.py` · suíte nova · spec §3.7",
     [
         "Suíte nova → **`29 passed`** (o `xfail` vira passed + 3 novos) — Step 4.",
         "`_map_acordao` do acórdão real: `nome ← titulo`, `numero ← numeroAcordao/anoAcordao`, `data ← dataSessao`, `ementa ← sumario` **literal**, `link ← urlAcordao`, `situacao` literal (teste `test_tcu_acordao_real_…`).",
         "Data vazia continua `\"\"`, não `None` (`assert r.data == \"\"` acrescentado em `test_tcu_map_acordao_missing_fields`) — ids preservados.",
         "`test_comprehensive` 98/98; `test_searchers` 13/13; golden OK (o corpus fixo não passa por `_map_acordao`).",
         "Spec §3.7 emendada; `BASELINE` 29; runner TUDO VERDE (total **251**); auditoria; commit + push.",
     ]),
    ("05-google-vocabulario", "Fase 2 — Fontes honestas",
     "Google/DuckDuckGo entra no vocabulário mínimo (⚠ emenda à spec §5)",
     [(1, "`FonteIndisponivel`, `KeywordStatus` novos"),
      (2, "`RespostaFake` e a suíte nova (usada pelo teste do CSE)")],
     "`tests/test_fontes_indisponiveis.py` · runner. **Não** consome código da T3/T4, mas soma na mesma suíte e no mesmo `BASELINE` — por isso vem depois delas.",
     [
         "Suíte nova → **`37 passed`** (29 + 8) — Step 4.",
         "`python -c \"from searchers import GoogleSearcher\"` importa (R3-B2: sem `from typing import Optional` o app inteiro não sobe).",
         "`DDGSException(\"No results found.\")` → `empty` sem motivo; timeout/ratelimit mapeados; keywords além de 5 e as cortadas por `max_results` ganham `nao_consultada`; retry pulado **não** marca `retried`.",
         "`git grep` sem resto de `error_msg` em `google_searcher.py`; `test_searchers` 13/13; `test_comprehensive` 98/98.",
         "`BASELINE` 37; runner TUDO VERDE (total **259**); golden OK; auditoria; commit + push.",
     ]),
    ("06-origem-da-nota", "Fase 3 — Procedência da nota",
     "`score_relevance_com_origem` — a nota diz de onde veio",
     [(1, "`ORIGENS_RELEVANCIA` em `models.py`")],
     "`llm/gemini_client.py` · `llm/__init__.py` · `test_llm_phase3.py` · runner. Nenhum arquivo da Fase 2.",
     [
         "Antes de implementar: `python test_llm_phase3.py | tail -5` → `Total: 54 | PASS: 53 | FAIL: 1` (Step 2).",
         "Depois: **`Total: 63 | PASS: 63 | FAIL: 0`** (Step 4).",
         "`score_relevance` vira wrapper com o contrato antigo (os 53 testes antigos intactos); `git grep -n 'score_relevance\\b' -- '*.py'` → só o wrapper, `__init__.py`, `app.py` (a T9 troca) e os testes.",
         "Docstring de módulo (`gemini_client.py:11`) e do pacote atualizadas; frases sobre Gemini/API key **intocadas** (emenda B7, frente 5).",
         "`BASELINE[\"test_llm_phase3.py\"] = 63`; runner TUDO VERDE (total **269**); golden OK; auditoria; commit + push.",
     ]),
    ("07-merge-origem", "Fase 3 — Procedência da nota",
     "`_merge` leva a origem da nota vencedora (invariante declarado)",
     [(1, "campo `NormativoResult.relevancia_origem`")],
     "`deduplicator.py` · `test_phase4.py` (T8, T9) · runner",
     [
         "`python -m pytest test_phase4.py -q` → **`61 passed`** (Step 4).",
         "**`dedup_esperado.json` inalterado — obrigatório**; golden OK.",
         "Docstring de `_merge` declara o invariante (hoje o efeito prático é nulo: o dedup roda antes da pontuação).",
         "`BASELINE` 61; runner TUDO VERDE (total **272**); auditoria; commit + push.",
     ]),
    ("08-planilha-diagnostico", "Fase 4 — Saída honesta",
     "planilha ganha a coluna \"Origem da nota\" e a aba \"Diagnostico da busca\"; golden nas duas abas",
     [(1, "`rotulo_status`, `redigir`, `KeywordStatus` novos, `ORIGENS_RELEVANCIA`"),
      (7, "só a contagem: `test_phase4` sai de 61 (T7) para 71")],
     "`excel_export.py` · `test_phase4.py` · `tools/golden_master.py` · `tests/golden/` · runner",
     [
         "Na coleta, antes de implementar: `ImportError` de `ORIGEM_LABEL` (Step 2). Depois: `test_phase4.py` → **`71 passed`** (Step 5).",
         "`golden_master.py comparar` → **`DIVERGIU: planilha divergiu` e NENHUMA linha `dedup divergiu`** (se houver: parar, é regressão) → `congelar` → `comparar` **2×** OK com sha idêntico (Step 6).",
         "`git diff --stat tests/golden/` → só `planilha_sha256.txt` (+ `ambiente.txt` se mudou) e `diagnostico_fixo.json` novo; `dedup_esperado.json` **ausente** do diff.",
         "Aba `Diagnostico da busca` sempre presente; `Normativos` continua a aba ativa; campo vazio = `—`; detalhe até 2000 chars inteiro.",
         "Recongelamento **no mesmo commit**, com o porquê na mensagem; `BASELINE` 71; runner TUDO VERDE (total **282**); auditoria; push.",
     ]),
    ("09-tela-honesta", "Fase 4 — Saída honesta",
     "tela: pontuar sempre, relatório por motivo, avisos por fonte, origem no card/preview, fonte que levanta não some",
     [(1, "`statuses_para_falha_total`, `ORIGENS_RELEVANCIA`"),
      (2, "`SOURCE_ID` do LexML e o `bloqueio_waf` que o gate V11 procura"),
      (3, "`SOURCE_ID` do TCU, o `parcial` por endpoint (V11: \"tcu respondeu parcialmente\") e o `tzdata` no `requirements.txt` que o `ZoneInfo` do app exige no Windows"),
      (4, "acórdãos que casam de verdade (senão o TCU nunca entrega nada na tela)"),
      (5, "`SOURCE_ID` do Google"),
      (6, "`score_relevance_com_origem`"),
      (8, "`generate_excel(..., diagnostico=, quando=)` e a classe `TestRotulosSincronizados` em `test_phase4.py`, onde o Step 1 acrescenta `test_origem_curta_do_app_cobre_o_vocabulario`")],
     "`app.py` · `test_phase4.py` · `.gitignore` · `tools/dirigir_app.py` (novo) · runner",
     [
         "`test_phase4.py` → **72** (+1: `test_origem_curta_do_app_cobre_o_vocabulario`); total **283**; o executor atualiza o `BASELINE` no commit (Step 1).",
         "Sem LLM a relevância é calculada pela heurística (origem `heuristica`); com LLM, pelo modelo; origem desconhecida é validada sem `assert` (Step 3).",
         "Gate visual V11: com o app no ar, `PYTHONIOENCODING=utf-8 python tools/dirigir_app.py` → `GATE V11 OK`, **e o PNG em `tests/evidencia/` aberto e olhado** (Step 7). `tests/evidencia/` no `.gitignore`.",
         "Runner TUDO VERDE; golden OK; auditoria dos 2 comandos; commit + push (Step 8).",
     ]),
    ("10-fechar-frente", "Fase 5 — Fechamento",
     "fechar a frente 2: critérios de pronto da spec §7, duráveis, lições",
     [(9, "todas as anteriores fechadas (9 commits de task)")],
     "ledgers e docs do repo",
     [
         "Critérios de pronto da spec §7 com comandos e saídas no commit: runner TUDO VERDE **sem** `[AVISO] cresceu`; `golden_master.py comparar` OK e `git diff d054d5b -- tests/golden/dedup_esperado.json` vazio; V11 rodado de novo; auditoria dos 2 comandos sobre `dc99d73..HEAD`.",
         "Duráveis atualizados como a task lista (`_TODO.md`, `log.md`, `SESSION-ONBOARD` §2/§6 → próxima: frente 5, `BLOCKED-ON-RODRIGO.md` B-04, `LESSONS.md` com as 3 lições).",
         "Commit `docs: fecha a frente 2`; push; `/checkpoint`.",
     ]),
]

aviso = (
    "> Extraído **verbatim** do plano v4 (linhas {ini}-{fim}). **O plano segue fonte de verdade**:\n"
    "> divergência entre o plano e esta cópia → o plano ganha. Status em `../execucao/TODOS.md` — **não marque\n"
    "> os checkboxes aqui**. Antes de começar, ler `../reference/global-constraints.md` (Global\n"
    "> Constraints, Estrutura de arquivos, BASELINE por task). Ordem e dependências: `../00-overview.md`.\n"
)

OUT.joinpath("tasks").mkdir(parents=True, exist_ok=True)
OUT.joinpath("reference").mkdir(parents=True, exist_ok=True)
cobertas: list[int] = []
faixas = {}

for k, (slug, fase, titulo, deps, compartilha, criterios) in enumerate(TASKS):
    n = k + 1
    fim_bruto = (cabecalhos[k + 1] - 1) if k + 1 < len(cabecalhos) else self_review - 1
    ini, fim = aparar(cabecalhos[k], fim_bruto)
    faixas[n] = (ini, fim)
    cobertas += range(ini, fim + 1)
    dep_ids = [d for d, _ in deps]
    partes = [
        "---",
        f"task: {n}",
        f"fase: \"{fase}\"",
        f"plan: {PLANO_REL} (linhas {ini}-{fim})",
        f"reference: {OUT_REL}/reference/global-constraints.md",
        f"depends_on: [{', '.join(f'T{d}' for d in dep_ids)}]",
        "---",
        "",
        aviso.format(ini=ini, fim=fim),
        f"# T{n} · {titulo}",
        "",
        f"**{fase}.**",
        "",
        "## Depende de",
        "",
    ]
    if deps:
        partes += [f"- **T{d}** — {porque}" for d, porque in deps]
    else:
        partes += ["- nada — é o gate inicial da frente (a frente 1 já entregou runner e golden-master)."]
    partes += [
        "",
        f"**Arquivos compartilhados com outras tasks:** {compartilha}",
        "",
        "## Critérios de aceite",
        "",
        "> Derivados do próprio plano (os \"Ver passar\", \"Expected\" e gates da task e das Global",
        "> Constraints) — **nenhum critério novo**. Números são previsões do plano: se o observado",
        "> divergir, contar os `def test_` do bloco da task antes de suspeitar do código.",
        "",
    ]
    partes += [f"- {c}" for c in criterios]
    partes += ["", "---", "", "## Conteúdo da task (verbatim do plano)", "", fatia(ini, fim), ""]
    (OUT / "tasks" / f"{slug}.md").write_text("\n".join(partes), encoding="utf-8")

# reference/global-constraints.md: cabecalho do plano + Global Constraints + Estrutura + BASELINE
h_ini, h_fim = aparar(1, triagem_ini - 1)
g_ini, g_fim = aparar(global_ini, cabecalhos[0] - 1)
cobertas += list(range(h_ini, h_fim + 1)) + list(range(g_ini, g_fim + 1))
(OUT / "reference" / "global-constraints.md").write_text("\n".join([
    f"> Material transversal extraído **verbatim** do plano (`{PLANO_REL}`, linhas {h_ini}-{h_fim} e",
    f"> {g_ini}-{g_fim}). Citado pelo header de cada task. O plano segue fonte de verdade.",
    "",
    fatia(h_ini, h_fim), "", "---", "", fatia(g_ini, g_fim), "",
]), encoding="utf-8")

# reference/triagem-adversarial.md: registro das 3 rodadas (trilha de auditoria)
t_ini, t_fim = aparar(triagem_ini, global_ini - 1)
cobertas += range(t_ini, t_fim + 1)
(OUT / "reference" / "triagem-adversarial.md").write_text("\n".join([
    f"> Trilha de auditoria das 3 rodadas adversariais, extraída **verbatim** do plano (`{PLANO_REL}`,",
    f"> linhas {t_ini}-{t_fim}). **Não é instrução de build**: tudo o que foi aceito já está dobrado no",
    "> corpo das tasks. Serve para saber POR QUE um trecho é como é (ids R2-*, R3-*, B*, H*, M*).",
    "",
    fatia(t_ini, t_fim), "",
]), encoding="utf-8")

# reference/self-review-v4.md
s_ini, s_fim = aparar(self_review, N)
cobertas += range(s_ini, s_fim + 1)
(OUT / "reference" / "self-review-v4.md").write_text("\n".join([
    f"> Self-review do plano v4, extraído **verbatim** (`{PLANO_REL}`, linhas {s_ini}-{s_fim}).",
    "",
    fatia(s_ini, s_fim), "",
]), encoding="utf-8")

# --- cobertura: toda linha nao-vazia/nao-'---' coberta exatamente uma vez ---
assert len(cobertas) == len(set(cobertas)), "sobreposicao"
faltando = [i for i in range(1, N + 1) if i not in set(cobertas) and L(i).strip() not in ("", "---")]
assert not faltando, f"linhas nao cobertas: {faltando[:20]}"
for f in list((OUT / "tasks").glob("*.md")) + list((OUT / "reference").glob("*.md")):
    cercas = sum(1 for x in f.read_text(encoding="utf-8").split("\n") if x.startswith("```"))
    assert cercas % 2 == 0, f"cercas impares em {f.name}"
print("faixas:", faixas)
print("reference:", (h_ini, h_fim), (g_ini, g_fim), "triagem", (t_ini, t_fim), "self-review", (s_ini, s_fim))
print("OK: cobertura completa, sem sobreposicao, cercas pares")
