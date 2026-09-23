---
task: 9
fase: "Fase 4 — Saída honesta"
plan: docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md (linhas 2632-2865)
reference: spec/frente2-honestidade-fontes/reference/global-constraints.md
depends_on: [T1, T2, T3, T4, T5, T6, T8]
---

> Extraído **verbatim** do plano v4 (linhas 2632-2865). **O plano segue fonte de verdade**:
> divergência entre o plano e esta cópia → o plano ganha. Status só no `_TODO.md` — **não marque
> os checkboxes aqui**. Antes de começar, ler `../reference/global-constraints.md` (Global
> Constraints, Estrutura de arquivos, BASELINE por task). Ordem e dependências: `../00-overview.md`.

# T9 · tela: pontuar sempre, relatório por motivo, avisos por fonte, origem no card/preview, fonte que levanta não some

**Fase 4 — Saída honesta.**

## Depende de

- **T1** — `statuses_para_falha_total`, `ORIGENS_RELEVANCIA`
- **T2** — `SOURCE_ID` do LexML e o `bloqueio_waf` que o gate V11 procura
- **T3** — `SOURCE_ID` do TCU, o `parcial` por endpoint (V11: "tcu respondeu parcialmente") e o `tzdata` no `requirements.txt` que o `ZoneInfo` do app exige no Windows
- **T4** — acórdãos que casam de verdade (senão o TCU nunca entrega nada na tela)
- **T5** — `SOURCE_ID` do Google
- **T6** — `score_relevance_com_origem`
- **T8** — `generate_excel(..., diagnostico=, quando=)` e a classe `TestRotulosSincronizados` em `test_phase4.py`, onde o Step 1 acrescenta `test_origem_curta_do_app_cobre_o_vocabulario`

**Arquivos compartilhados com outras tasks:** `app.py` · `test_phase4.py` · `.gitignore` · `tools/dirigir_app.py` (novo) · runner

## Critérios de aceite

> Derivados do próprio plano (os "Ver passar", "Expected" e gates da task e das Global
> Constraints) — **nenhum critério novo**. Números são previsões do plano: se o observado
> divergir, contar os `def test_` do bloco da task antes de suspeitar do código.

- `test_phase4.py` → **72** (+1: `test_origem_curta_do_app_cobre_o_vocabulario`); total **283**; o executor atualiza o `BASELINE` no commit (Step 1).
- Sem LLM a relevância é calculada pela heurística (origem `heuristica`); com LLM, pelo modelo; origem desconhecida é validada sem `assert` (Step 3).
- Gate visual V11: com o app no ar, `PYTHONIOENCODING=utf-8 python tools/dirigir_app.py` → `GATE V11 OK`, **e o PNG em `tests/evidencia/` aberto e olhado** (Step 7). `tests/evidencia/` no `.gitignore`.
- Runner TUDO VERDE; golden OK; auditoria dos 2 comandos; commit + push (Step 8).

---

## Conteúdo da task (verbatim do plano)

### Task 9: Tela — pontuar sempre, relatório honesto, avisos por fonte, card, preview, fonte que levanta

**Files:** `app.py` — imports (`:21-24`); `except` do laço de fontes (`:545-564`); pontuação (`:570-596`); `_render_search_diagnostics` (`:840-905`); `render_step4` (`:907-946`); card (`:1049-1065`); `generate_excel` (`:1195`); preview (`:1221-1232`). ⚠ **Linhas do HEAD:** os Steps 1-3 inserem ~20 linhas antes de `:840`; a partir daí, ancorar pelo **nome da função**, não pelo número. `tools/dirigir_app.py` (novo); `.gitignore`.

- [ ] **Step 1: Imports** — `from models import KeywordStatus, NormativoResult, ORIGENS_RELEVANCIA, statuses_para_falha_total` (⚠ **não** importar `rotulo_status`: a tela agrupa por motivo, só a planilha rotula — R3); `from datetime import datetime` (⚠ **não** `import datetime`); `from zoneinfo import ZoneInfo`; no topo, `ORIGEM_CURTA = {"modelo": "modelo", "heuristica": "heurística", "fallback_erro": "fallback", "padrao_fonte": "padrão da fonte"}`. O teste de sincronia `set(ORIGEM_CURTA) == ORIGENS_RELEVANCIA` **não** fica como `assert` no app (some com `-O`, R3): vai para `test_phase4.py::TestRotulosSincronizados` como `test_origem_curta_do_app_cobre_o_vocabulario` (`from app import ORIGEM_CURTA` — ⚠ importar `app` executa `st.set_page_config`; se isso levantar fora do Streamlit, mover `ORIGEM_CURTA` para `models.py` e importar de lá nos dois lugares). ⚠ Isso muda a contagem da T8/T9: +1 em `test_phase4` = **72** e total **283** — o executor atualiza a tabela e o BASELINE no commit da T9.

- [ ] **Step 2: Fonte que levanta não some (H2, R2)** — no `except Exception as e:` de `:556`, **antes** do `status_text.write`:

```python
                # H2: os statuses ja coletados antes da excecao ficam; o resto vira erro_interno por keyword
                ja = getattr(searcher, "keyword_statuses", []) or []
                all_keyword_statuses.extend(ja)
                cobertas = {s.keyword for s in ja}
                faltam = [k for k in keywords if k not in cobertas]
                if faltam or not keywords:   # R3: com tudo coberto, nao inventar uma linha "(todas)"
                    all_keyword_statuses.extend(statuses_para_falha_total(searcher.SOURCE_ID, faltam, e))
```

- [ ] **Step 3: Pontuação sempre** — `app.py:570-596`, trocar o bloco por:

```python
        # Relevancia SEMPRE roda (frente 2): com LLM e o modelo; sem LLM e a
        # heuristica por palavras-chave. Antes, sem chave, a nota ficava na
        # constante do searcher e a heuristica era codigo inalcancavel.
        if all_results:
            topic = st.session_state.get("topic", "")
            result_dicts = [{"nome": r.nome, "ementa": r.ementa} for r in all_results]
            status_text.write(
                "Avaliando relevancia com IA..." if llm_available()
                else "Avaliando relevancia por palavras-chave (sem LLM configurado)..."
            )
            pares = gemini_client.score_relevance_com_origem(topic, result_dicts, keywords)
            for i, (score, origem) in enumerate(pares):
                if i < len(all_results):
                    if origem not in ORIGENS_RELEVANCIA:   # M8/R3: validacao real, nao assert (some com -O)
                        logger.error("origem de relevancia desconhecida %r; gravando padrao_fonte", origem)
                        origem = "padrao_fonte"
                    all_results[i].relevancia = score
                    all_results[i].relevancia_origem = origem

            # Categorizacao continua condicionada ao LLM: nao ha heuristica
            # para ela, e "Nao categorizado" ja e honesto.
            if llm_available():
                status_text.write("Categorizando normativos...")
                categories = gemini_client.categorize_results(topic, result_dicts)
                for i, cat in enumerate(categories):
                    if i < len(all_results):
                        all_results[i].categoria = cat
```

- [ ] **Step 4: Relatório** — substituir `_render_search_diagnostics` inteira:

```python
def _render_search_diagnostics(kw_statuses: list[KeywordStatus]) -> None:
    """Relatorio da busca: indisponiveis, parciais, nao consultadas, sem resultado, OK.

    Classifica por MOTIVO, nao so por status (R2-B6): nao_consultada tem
    status="error" no vocabulario, mas nao e "fonte indisponivel" — e uma
    palavra-chave que nao foi enviada. Rotulos vem de models.rotulo_status.
    """
    if not kw_statuses:
        return

    indisponiveis = [s for s in kw_statuses if s.status == "error" and s.motivo != "nao_consultada"]
    nao_consultadas = [s for s in kw_statuses if s.motivo == "nao_consultada"]
    empty_statuses = [s for s in kw_statuses if s.status == "empty"]
    ok_statuses = [s for s in kw_statuses if s.status == "ok"]
    parciais = [s for s in kw_statuses if s.parcial and s.status != "error"]   # R3: disjunto de indisponiveis
    total = len(kw_statuses)

    label = (f"Relatório da busca — {len(ok_statuses)} OK · {len(indisponiveis)} indisponíveis · "
             f"{len(empty_statuses)} sem resultado · {len(nao_consultadas)} não consultadas ({total} buscas)")

    with st.expander(label, expanded=bool(indisponiveis or parciais)):
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total de buscas", total)
        c2.metric("OK", len(ok_statuses))
        c3.metric("Sem resultado", len(empty_statuses))
        c4.metric("Indisponíveis", len(indisponiveis))
        c5.metric("Não consultadas", len(nao_consultadas))

        if indisponiveis:
            st.markdown("**:red[Fontes indisponíveis (a fonte não pôde ser consultada):]**")
            for s in indisponiveis:
                retry_badge = " (retentado)" if s.retried else ""
                extra = f" — {s.result_count} resultado(s) do endpoint que respondeu" if s.result_count else ""
                badge_parcial = " (parcial)" if s.parcial else ""
                st.markdown(f"- :red[**{html_module.escape(s.keyword)}**] em *{html_module.escape(s.source)}*"
                            f"{retry_badge}{badge_parcial}: `{html_module.escape(s.motivo or 'erro')}`{extra}")
                st.code(s.detalhe or s.error_message or "(sem detalhe)", language=None)   # M13: nao passa pelo Markdown
            st.caption("A fonte não pôde ser consultada. Isso NÃO significa que não existem normativos — "
                       "significa que esta busca não os viu. Motivo e detalhe acima; a aba "
                       "'Diagnostico da busca' da planilha registra o mesmo.")

        if parciais:
            st.markdown("**:orange[Buscas parciais (a coleta não terminou):]**")
            for s in parciais:
                st.markdown(f"- :orange[**{html_module.escape(s.keyword)}**] em *{html_module.escape(s.source)}*: "
                            f"{s.result_count} resultado(s)")
                st.code(s.detalhe or "(sem detalhe)", language=None)

        if nao_consultadas:
            st.markdown("**:gray[Palavras-chave não consultadas (limite da busca atingido antes delas):]**")
            for s in nao_consultadas:
                st.markdown(f"- {html_module.escape(s.keyword)} em *{html_module.escape(s.source)}* — "
                            f"{html_module.escape(s.detalhe)}")

        if empty_statuses:
            st.markdown("**:orange[Palavras-chave sem resultados (nenhum normativo encontrado):]**")
            for s in empty_statuses:
                st.markdown(f"- :orange[**{html_module.escape(s.keyword)}**] em *{html_module.escape(s.source)}*")
                if s.detalhe:   # R3-H5: "500 acordaos sem sumario" nao e "nao ha acordao"
                    st.code(s.detalhe, language=None)
            st.caption("Essas palavras-chave foram buscadas com sucesso, mas nenhum normativo "
                       "correspondente foi encontrado na fonte. Quando há detalhe, ele diz o que a fonte entregou.")

        if ok_statuses:
            st.markdown("**:green[Palavras-chave com resultados:]**")
            for s in ok_statuses:
                st.markdown(f"- :green[**{html_module.escape(s.keyword)}**] em *{html_module.escape(s.source)}*: "
                            f"{s.result_count} resultado(s){' (parcial)' if s.parcial else ''}")
```

⚠ A assinatura mudou (só `kw_statuses`): as **duas** chamadas em `render_step4` (`:934` e `:946`) passam a `_render_search_diagnostics(kw_statuses)`, e as três listas `error_statuses/empty_statuses/ok_statuses` de `:914-916` saem — o `st.error` do ramo `if not results:` passa a usar `indisponiveis` calculado ali (Step 5).

- [ ] **Step 5: Avisos por fonte (H3, R2, R3-H4)** — em `render_step4`, o bloco abaixo entra **depois** do `st.header(...)` de cada um dos dois ramos (com e sem resultados — R3: antes do header ficava acima do título); as listas `catalogadas`/`indisponiveis`/`por_fonte` são calculadas uma vez, logo após `kw_statuses = ...`:

```python
    catalogadas = [s for s in kw_statuses if s.source in ("lexml", "tcu")]
    indisponiveis = [s for s in kw_statuses if s.status == "error" and s.motivo != "nao_consultada"]
    por_fonte = {}
    for s in catalogadas:
        f = por_fonte.setdefault(s.source, {"entregues": 0, "erros": 0, "total": 0, "motivos": set(), "parcial": False})
        f["total"] += 1
        f["entregues"] += s.result_count
        if s.status == "error" and s.motivo != "nao_consultada":
            f["erros"] += 1
            f["motivos"].add(s.motivo)
        f["parcial"] = f.get("parcial", False) or s.parcial
    # R3-H4: "morta" exige que NENHUM status da fonte seja parcial — TCU com acordaos 200
    # (0 match) e atos 500 respondeu pela metade, nao "esta indisponivel"
    mortas = [f for f, v in por_fonte.items() if v["total"] and v["erros"] == v["total"]
              and v["entregues"] == 0 and not v["parcial"]]
    parciais_fonte = [f for f, v in por_fonte.items() if v["erros"] and f not in mortas]
    nomes = ", ".join(sorted(por_fonte)) or "nenhuma selecionada"
    tem_web_aberta = any(s.source == "google" for s in kw_statuses)
    if mortas and not parciais_fonte:
        resto = " O que aparece abaixo vem só da web aberta." if tem_web_aberta else " Nenhuma outra fonte foi consultada."
        st.warning(f"Nenhuma fonte catalogada ({nomes}) entregou resultado nesta busca: "
                   + "; ".join(f"{f} indisponível ({', '.join(sorted(por_fonte[f]['motivos']))})" for f in mortas)
                   + "." + resto + " Veja o relatório da busca.")
    elif mortas or parciais_fonte:
        partes = [f"{f} indisponível ({', '.join(sorted(por_fonte[f]['motivos']))})" for f in mortas]
        partes += [f"{f} respondeu parcialmente ({por_fonte[f]['entregues']} resultado(s); "
                   f"{', '.join(sorted(por_fonte[f]['motivos']))})" for f in parciais_fonte]
        st.warning("Cobertura incompleta nas fontes catalogadas: " + "; ".join(partes)
                   + ". O restante pode estar faltando. Veja o relatório da busca.")
    if results and all(r.relevancia_origem == "heuristica" for r in results):
        st.caption("Sem LLM configurado, a relevância é a fração das palavras-chave presentes na ementa: "
                   "0% significa 'nenhuma palavra-chave na ementa', não 'irrelevante'.")   # M14
```

E no ramo `if not results:`, o `st.error` passa a ser: `if indisponiveis: st.error(f"Nenhum normativo encontrado. {len(indisponiveis)} busca(s) não puderam consultar a fonte (indisponível). Isso não significa que o normativo não existe — veja o relatório.")`.

- [ ] **Step 6: Card, preview, exportação** — card (`Relevancia:` na `:1065`): `f"<b>Relevancia:</b> {relevancia_pct}% <i>({ORIGEM_CURTA.get(item.relevancia_origem, item.relevancia_origem)})</i> &middot; "` (`.get`: lookup duro vira traceback na página — R3); preview (`:1221-1232`): depois de `"Relevancia": ...,` acrescentar `"Origem": ORIGEM_CURTA.get(item.relevancia_origem, item.relevancia_origem),`; exportação (`:1195`): `generate_excel(selected, topic, diagnostico=st.session_state.get("keyword_statuses", []), quando=datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M"))` (BRT como o 503 do TCU — R3).

- [ ] **Step 7: Gate visual V11** — `tools/dirigir_app.py`:

```python
# -*- coding: utf-8 -*-
"""Gate visual da frente 2: dirige o app pelo navegador e AFIRMA o que a UI diz.

Pre-requisito: o app no ar em http://localhost:8501
    (em levantamento-normativos/: python -m streamlit run app.py --server.headless true)
Uso (na raiz):  PYTHONIOENCODING=utf-8 python tools/dirigir_app.py
Usa o Chrome instalado (channel="chrome"): os navegadores do Playwright nao
estao baixados nesta maquina (ENVIRONMENT.md, 2026-09-22).
Assume o cenario de 22/09 (LexML bloqueado). Se o LexML voltar, o gate
avisa e o humano decide — nao ha como ser verde e vermelho ao mesmo tempo.
"""
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "tests" / "evidencia" / "v11_passo4.png"   # evidencia de sessao, NAO versionada
SAIDA.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 1440, "height": 1600})
    pg.goto("http://localhost:8501", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(3000)
    pg.get_by_text("Inserir palavras-chave manualmente").click()
    pg.wait_for_timeout(2000)
    ta = pg.locator("textarea").first
    ta.click(); ta.fill("LGPD\nprotecao de dados pessoais")
    pg.keyboard.press("Control+Enter"); pg.wait_for_timeout(2500)
    pg.get_by_role("button", name="Proximo >>").click(); pg.wait_for_timeout(3000)
    pg.get_by_role("button", name="Iniciar Busca").click()
    for _ in range(60):
        pg.wait_for_timeout(5000)
        if "Passo 4 - " in pg.inner_text("body"):
            break
    pg.wait_for_timeout(3000)
    pg.screenshot(path=str(SAIDA), full_page=True)
    texto = pg.inner_text("body")
    print(texto[:4000])
    b.close()

print("\n=== GATE V11 ===")
m = re.search(r"Revisar Resultados \((\d+) normativos\)", texto)
n_cab = int(m.group(1)) if m else 0
n_cards = texto.count("Ver detalhes")
checks = {
    "relatório mostra ≥1 indisponível": bool(re.search(r"·\s*[1-9]\d*\s*indisponíveis", texto)),
    "bloqueio_waf visível na tela": "bloqueio_waf" in texto,
    "aviso por fonte presente": ("indisponível (" in texto),
    "TCU declarado parcial (acórdãos 200, atos 500 — cenário de 22/09)": ("tcu respondeu parcialmente" in texto),
    "origem no card": any(o in texto for o in ("(heurística)", "(modelo)", "(fallback)")),
    "nenhum card sumiu (cards == N do cabeçalho)": n_cab > 0 and n_cards == n_cab,
    "'0 erros' não aparece": "0 erros" not in texto,   # mantido por historia; nao e o gate
}
for k, v in checks.items():
    print(f"  {'OK ' if v else 'FALHOU'} {k}")
if not checks["relatório mostra ≥1 indisponível"]:
    print("  ⚠ Se o LexML voltou a responder, este gate nao se aplica hoje — confirmar no relatório.")
assert all(v for k, v in checks.items() if k not in ("'0 erros' não aparece",)), "gate V11 reprovou"
print("GATE V11 OK — abrir e OLHAR:", SAIDA)
```

`.gitignore` ganha `tests/evidencia/`. Rodar com o app no ar; **abrir o PNG e olhar**.

- [ ] **Step 8: Runner, golden, auditoria; commit** `feat(frente2): a tela classifica por motivo, avisa por fonte e mostra a origem da nota`. Push.
