---
task: 8
fase: "Fase 4 — Saída honesta"
plan: docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md (linhas 2390-2637)
reference: spec/frente2-honestidade-fontes/reference/global-constraints.md
depends_on: [T1, T7]
---

> Extraído **verbatim** do plano v4 (linhas 2390-2637). **O plano segue fonte de verdade**:
> divergência entre o plano e esta cópia → o plano ganha. Status em `../execucao/TODOS.md` — **não marque
> os checkboxes aqui**. Antes de começar, ler `../reference/global-constraints.md` (Global
> Constraints, Estrutura de arquivos, BASELINE por task). Ordem e dependências: `../00-overview.md`.

# T8 · planilha ganha a coluna "Origem da nota" e a aba "Diagnostico da busca"; golden nas duas abas

**Fase 4 — Saída honesta.**

## Depende de

- **T1** — `rotulo_status`, `redigir`, `KeywordStatus` novos, `ORIGENS_RELEVANCIA`
- **T7** — só a contagem: `test_phase4` sai de 61 (T7) para 71

**Arquivos compartilhados com outras tasks:** `excel_export.py` · `test_phase4.py` · `tools/golden_master.py` · `tests/golden/` · runner

## Critérios de aceite

> Derivados do próprio plano (os "Ver passar", "Expected" e gates da task e das Global
> Constraints) — **nenhum critério novo**. Números são previsões do plano: se o observado
> divergir, contar os `def test_` do bloco da task antes de suspeitar do código.

- Na coleta, antes de implementar: `ImportError` de `ORIGEM_LABEL` (Step 2). Depois: `test_phase4.py` → **`71 passed`** (Step 5).
- `golden_master.py comparar` → **`DIVERGIU: planilha divergiu` e NENHUMA linha `dedup divergiu`** (se houver: parar, é regressão) → `congelar` → `comparar` **2×** OK com sha idêntico (Step 6).
- `git diff --stat tests/golden/` → só `planilha_sha256.txt` (+ `ambiente.txt` se mudou) e `diagnostico_fixo.json` novo; `dedup_esperado.json` **ausente** do diff.
- Aba `Diagnostico da busca` sempre presente; `Normativos` continua a aba ativa; campo vazio = `—`; detalhe até 2000 chars inteiro.
- Recongelamento **no mesmo commit**, com o porquê na mensagem; `BASELINE` 71; runner TUDO VERDE (total **282**); auditoria; push.

---

## Conteúdo da task (verbatim do plano)

### Task 8: Planilha — coluna "Origem da nota", aba "Diagnostico da busca", golden nas duas abas

**Files:** `excel_export.py` (`:14-30` imports; `COLUMNS:75-87`; `_write_data_row:186-270`; `generate_excel:274-357`; função nova); `test_phase4.py` (`:421-447`; classes novas); `tools/golden_master.py` (`_sha_planilha:63-84`, docstring); `tests/golden/diagnostico_fixo.json` (novo), `planilha_sha256.txt`, `ambiente.txt`; `tools/run_all_tests.py`.

**Interfaces — Produces:** `COLUMNS` com 11 entradas (11ª = `("Origem da nota", 16, "relevancia_origem")`); `ORIGEM_LABEL`, `VAZIO = "—"`, `DIAGNOSTICO_SHEET`, `DIAGNOSTICO_COLUMNS`; `generate_excel(results, topic, diagnostico=None, quando=None) -> BytesIO`; aba `"Diagnostico da busca"` sempre presente; `wb.active` = `"Normativos"`; título da aba: `f"Diagnóstico da busca: {topic} — {quando or 'data/hora não informada'}"`.

- [ ] **Step 1: Testes** — em `test_phase4.py`:

(a) `TestExcelColumnCount` (`:421-447`): `test_has_10_columns` → `test_has_11_columns` com `== 11`; `range(1, 11)` → `range(1, 12)` e `== 10` → `== 11` nos outros dois; `expected` ganha `"Origem da nota"` no fim; docstring da classe `"""Verify all 11 expected columns are present."""`. ⚠ (M12) hoje só `test_has_10_columns` falha; os outros passam por omissão — atualizar os três mesmo assim.

(b) Classes novas ao fim (10 testes):

```python
from models import KeywordStatus as _KS, rotulo_status
from excel_export import ORIGEM_LABEL, VAZIO, DIAGNOSTICO_SHEET


class TestExcelHonestidade:
    def test_origem_em_portugues_na_coluna_11(self):
        r = _make_result(relevancia=0.85); r.relevancia_origem = "heuristica"
        ws = _load_workbook_from_buffer(generate_excel([r], "t")).active
        assert ws.cell(row=2, column=11).value == "Origem da nota"
        assert ws.cell(row=3, column=11).value == "Heurística (palavras-chave)"

    def test_default_padrao_fonte(self):
        ws = _load_workbook_from_buffer(generate_excel([_make_result()], "t")).active
        assert ws.cell(row=3, column=11).value == "Padrão da fonte"

    def test_aba_diagnostico_sempre_existe_e_normativos_continua_ativa(self):
        wb = _load_workbook_from_buffer(generate_excel([_make_result()], "t"))
        assert wb.sheetnames == ["Normativos", DIAGNOSTICO_SHEET]
        assert wb.active.title == "Normativos"
        assert wb[DIAGNOSTICO_SHEET].cell(row=3, column=1).value == "Nenhum diagnóstico registrado nesta exportação"

    def test_aba_diagnostico_lista_vazia_igual_a_none(self):
        a = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=None))[DIAGNOSTICO_SHEET]
        b = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=[]))[DIAGNOSTICO_SHEET]
        assert a.cell(row=3, column=1).value == b.cell(row=3, column=1).value

    def test_aba_diagnostico_uma_linha_por_status_com_traco_no_vazio(self):
        diag = [
            _KS(keyword="lgpd", source="lexml", status="error", motivo="bloqueio_waf",
                detalhe="HTTP 200 text/html; título: x | GET http://x", error_message="bloqueio"),
            _KS(keyword="lgpd", source="tcu", status="ok", result_count=4, parcial=True,
                detalhe="pagina 2 (inicio=20): http_5xx: HTTP 500 | GET http://y"),
            _KS(keyword="lgpd", source="google", status="empty"),
            _KS(keyword="outra", source="lexml", status="error", motivo="nao_consultada",
                detalhe="busca parou em max_results=50 antes desta palavra-chave"),
        ]
        wb = _load_workbook_from_buffer(generate_excel([_make_result()], "t", diagnostico=diag, quando="22/09/2026 10:00"))
        ws = wb[DIAGNOSTICO_SHEET]
        assert "22/09/2026 10:00" in ws.cell(row=1, column=1).value
        assert [ws.cell(row=2, column=c).value for c in range(1, 9)] == [
            "Fonte", "Palavra-chave", "Status", "Motivo", "Detalhe", "Resultados", "Parcial", "Retentado"]
        linhas = [[ws.cell(row=r, column=c).value for c in range(1, 9)] for r in range(3, 7)]
        assert linhas[0] == ["lexml", "lgpd", "Indisponível", "bloqueio_waf", "HTTP 200 text/html; título: x | GET http://x", 0, "Não", "Não"]
        assert linhas[1] == ["tcu", "lgpd", "OK", VAZIO, "pagina 2 (inicio=20): http_5xx: HTTP 500 | GET http://y", 4, "Sim", "Não"]
        assert linhas[2] == ["google", "lgpd", "Sem resultado", VAZIO, VAZIO, 0, "Não", "Não"]
        assert linhas[3][2:4] == ["Não consultada", "nao_consultada"]            # R2-B6
        assert ws.cell(row=7, column=1).value is None

    def test_rotulo_da_planilha_e_o_de_models(self):
        diag = [_KS(keyword="k", source="tcu", status="error", motivo="http_5xx")]
        ws = _load_workbook_from_buffer(generate_excel([], "t", diagnostico=diag))[DIAGNOSTICO_SHEET]
        assert ws.cell(row=3, column=3).value == rotulo_status(diag[0]) == "Indisponível"

    def test_sem_quando_o_titulo_diz_nao_informada(self):
        ws = _load_workbook_from_buffer(generate_excel([], "t"))[DIAGNOSTICO_SHEET]
        assert "data/hora não informada" in ws.cell(row=1, column=1).value      # R2-B5: informadA

    def test_detalhe_longo_cabe_na_celula_inteiro(self):
        longo = "HTTP 500; " + "x" * 1500 + " | GET http://z"
        diag = [_KS(keyword="k", source="lexml", status="error", motivo="http_5xx", detalhe=longo)]
        ws = _load_workbook_from_buffer(generate_excel([], "t", diagnostico=diag))[DIAGNOSTICO_SHEET]
        assert ws.cell(row=3, column=5).value == longo                          # R2-B1: nada cortado


class TestRotulosSincronizados:
    def test_origem_label_cobre_o_vocabulario(self):
        assert set(ORIGEM_LABEL) == ORIGENS_RELEVANCIA

    def test_status_label_vem_de_models(self):
        from excel_export import STATUS_LABEL
        assert STATUS_LABEL is rotulo_status   # unico lugar (R2-B6)
```

- [ ] **Step 2: Ver falhar** — na coleta: `ImportError: cannot import name 'ORIGEM_LABEL' from 'excel_export'` (nenhum teste roda — R3). Depois do Step 3c só, `1 + 10 failed` (M12: dos três testes de contagem só `test_has_10_columns` falha hoje).

- [ ] **Step 3: `excel_export.py`**

**3a.** Imports (`:14-30`): `from typing import Optional`; `from models import KeywordStatus, NormativoResult, redigir, rotulo_status`.

**3b.** `COLUMNS` ganha, após `("Relevancia", 12, "relevancia")`: `("Origem da nota", 16, "relevancia_origem"),` com o comentário `# ⚠ test_phase4.py fixa len(COLUMNS); mudar aqui = mudar la no mesmo commit`.

**3c.** Constantes, logo após `COLUMNS`:

```python
# Rotulos em portugues para a planilha (o vocabulario tecnico vive em models.py)
ORIGEM_LABEL = {
    "modelo": "Modelo (IA)",
    "heuristica": "Heurística (palavras-chave)",
    "fallback_erro": "Fallback (erro do modelo)",
    "padrao_fonte": "Padrão da fonte",
}
STATUS_LABEL = rotulo_status          # UNICO lugar: models.rotulo_status (R2-B6)
VAZIO = "—"                            # celula vazia le como None no round-trip do openpyxl; o traco diz
                                       # "campo considerado, sem valor" (B6)
DIAGNOSTICO_SHEET = "Diagnostico da busca"
DIAGNOSTICO_COLUMNS = [
    ("Fonte", 12), ("Palavra-chave", 28), ("Status", 14), ("Motivo", 20),
    ("Detalhe", 90), ("Resultados", 11), ("Parcial", 9), ("Retentado", 10),
]
```

**3d.** `_write_data_row`: antes do `elif field_name == "nome":`:

```python
        elif field_name == "relevancia_origem":
            cell.value = ORIGEM_LABEL.get(value, value)
            cell.font = DATA_FONT
            cell.alignment = RELEVANCIA_ALIGNMENT
```

Docstring de `_write_data_row`: acrescentar `- Origem da nota em portugues (ORIGEM_LABEL)` à lista.

**3e.** Função nova, antes de `generate_excel`:

```python
def _write_diagnostico_sheet(wb, topic: str, diagnostico: Optional[list[KeywordStatus]], quando: Optional[str]) -> None:
    """Aba 'Diagnostico da busca': uma linha por (fonte, palavra-chave).

    Existe SEMPRE, mesmo sem dados, para que quem abre a planilha saiba que o
    registro e previsto. E o que diz, seis meses depois, que o LexML nao
    respondeu naquele dia — a planilha e o artefato que sobrevive a sessao.
    `quando` vem formatado pelo chamador (o golden passa um valor fixo).
    """
    ws = wb.create_sheet(DIAGNOSTICO_SHEET)
    n = len(DIAGNOSTICO_COLUMNS)
    ws.merge_cells(f"A1:{get_column_letter(n)}1")
    t = ws.cell(row=1, column=1)
    t.value = f"Diagnóstico da busca: {topic} — {quando or 'data/hora não informada'}"
    t.font, t.alignment, t.fill = TITLE_FONT, TITLE_ALIGNMENT, TITLE_FILL
    ws.row_dimensions[1].height = 40
    for col, (nome, largura) in enumerate(DIAGNOSTICO_COLUMNS, start=1):
        c = ws.cell(row=2, column=col)
        c.value, c.font, c.fill, c.alignment, c.border = nome, HEADER_FONT, HEADER_FILL, HEADER_ALIGNMENT, THIN_BORDER
        ws.column_dimensions[get_column_letter(col)].width = largura
    if not diagnostico:
        c = ws.cell(row=3, column=1)
        c.value = "Nenhum diagnóstico registrado nesta exportação"
        c.font = DATA_FONT
        return
    sim_nao = lambda b: "Sim" if b else "Não"
    for row, s in enumerate(diagnostico, start=3):
        # keyword e source vem do usuario/LLM: '=1+1' viraria formula (R3); redigir neutraliza
        valores = [redigir(s.source), redigir(s.keyword), STATUS_LABEL(s), s.motivo or VAZIO,
                   (s.detalhe or s.error_message) or VAZIO, s.result_count, sim_nao(s.parcial), sim_nao(s.retried)]
        for col, v in enumerate(valores, start=1):
            c = ws.cell(row=row, column=col)
            c.value, c.font, c.border = v, DATA_FONT, THIN_BORDER
            c.alignment = EMENTA_ALIGNMENT if col == 5 else DATA_ALIGNMENT
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:{get_column_letter(n)}{len(diagnostico) + 2}"
```

**3f.** `generate_excel(results, topic, diagnostico: Optional[list[KeywordStatus]] = None, quando: Optional[str] = None)`: docstring — `The workbook contains a single sheet` vira `The workbook contains two sheets: 'Normativos' (active) and 'Diagnostico da busca'`; `Args` ganha `diagnostico: KeywordStatus list from the search; None or empty writes a placeholder row.` e `quando: search date/time already formatted (dd/mm/yyyy HH:MM); None writes 'não informada'.` Antes de `buffer = BytesIO()`: `_write_diagnostico_sheet(wb, topic, diagnostico, quando)` e em seguida `wb.active = 0` (garante `Normativos` ativa). `redigir` **não** é chamada aqui — o `KeywordStatus` já redigiu.

- [ ] **Step 4: `tools/golden_master.py`** (M7):

```python
def _carregar_diagnostico() -> list:
    from models import KeywordStatus
    dados = json.loads((GOLDEN / "diagnostico_fixo.json").read_text(encoding="utf-8"))
    return [KeywordStatus(**d) for d in dados]


def _sha_planilha(itens: list) -> str:
    """Hash dos VALORES das celulas, nao dos bytes do arquivo — de TODAS as abas.

    .xlsx e um ZIP: o date_time de cada membro e o docProps/core.xml carregam o
    relogio da geracao, entao o sha dos bytes crus muda a CADA execucao, com
    entrada identica (medido por tres revisores em 2026-09-16). Congelar bytes
    faria o comparador imprimir DIVERGIU sem nada ter mudado.

    Hasheia TODAS as abas (M7 da rodada de 22/09): a aba 'Diagnostico da busca'
    e o registro de que a fonte nao respondeu; sem ela no hash, uma regressao
    ali passaria com 'golden-master OK'. O diagnostico fixo cobre: error com
    motivo e detalhe; ok parcial; empty; nao_consultada; error retentado sem
    detalhe (so error_message). `quando` e fixo para o hash ser estavel.

    ⚠ O hash da aba de diagnostico depende de models.redigir e rotulo_status e
    de excel_export.ORIGEM_LABEL, VAZIO e do titulo com `quando` fixo (rodada 3):
    mudanca INTENCIONAL em qualquer um deles = recongelar com justificativa,
    nao regressao do dedup/export.

    A funcao publica e generate_excel(results, topic, diagnostico=None, quando=None)
    (excel_export.py) — e o que app.py e test_phase4.py usam.
    """
    from excel_export import generate_excel
    from openpyxl import load_workbook

    wb = load_workbook(generate_excel(itens, topic="golden-master",
                                      diagnostico=_carregar_diagnostico(), quando="22/09/2026 00:00"))
    linhas = []
    for ws in wb.worksheets:
        linhas.append(("__aba__", ws.title))
        linhas.extend(tuple(c.value for c in linha) for linha in ws.iter_rows())
    return hashlib.sha256(repr(linhas).encode("utf-8")).hexdigest()
```

`tests/golden/diagnostico_fixo.json` (5 linhas):

```json
[
  {"keyword": "protecao de dados", "source": "lexml", "result_count": 0, "status": "error",
   "error_message": "bloqueio_waf", "motivo": "bloqueio_waf",
   "detalhe": "HTTP 200 text/html; título: Verificação de segurança — Senado Federal; corpo: '<!DOCTYPE html>' | GET https://www.lexml.gov.br/busca/SRU?operation=searchRetrieve&query=x | cadeia: busca/SRU: bloqueio_waf (HTTP 200); sru/SRU: endpoint_inexistente (HTTP 404); srw/SRU: endpoint_inexistente (HTTP 404) | retry pulado: os 3 URLs já falharam nesta busca"},
  {"keyword": "protecao de dados", "source": "tcu", "result_count": 4, "status": "ok", "parcial": true,
   "detalhe": "pagina 2 (inicio=20): http_5xx: HTTP 500 em 3 tentativas; corpo: '' | GET https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos?inicio=20"},
  {"keyword": "LGPD", "source": "google", "result_count": 0, "status": "empty"},
  {"keyword": "governanca", "source": "lexml", "result_count": 0, "status": "error", "motivo": "nao_consultada",
   "detalhe": "busca parou em max_results=50 antes desta palavra-chave"},
  {"keyword": "LGPD", "source": "tcu", "result_count": 0, "status": "error", "motivo": "timeout",
   "retried": true, "error_message": "Retry failed: timeout: sem resposta em 15s x 3 | GET https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos?inicio=0"}
]
```

- [ ] **Step 5: Ver passar** — `python -m pytest test_phase4.py -q` → `71 passed`.

- [ ] **Step 6: Recongelar no mesmo commit** — na raiz: `python tools/golden_master.py comparar` → **esperado `DIVERGIU: planilha divergiu`, e NENHUMA linha `dedup divergiu`** (se houver, parar: regressão). `python tools/golden_master.py congelar`; `comparar` **2×** → OK e sha idêntico. `git diff --stat tests/golden/` → só `planilha_sha256.txt` (+ `ambiente.txt` se mudou) + `diagnostico_fixo.json` novo; `dedup_esperado.json` **ausente**.

- [ ] **Step 7: BASELINE 71; runner; auditoria; commit**

```bash
git add levantamento-normativos/excel_export.py levantamento-normativos/test_phase4.py tests/golden/ tools/golden_master.py tools/run_all_tests.py
git commit -m "feat(frente2): planilha ganha 'Origem da nota' e a aba 'Diagnostico da busca'; golden cobre as duas abas

COLUMNS 10 -> 11. Aba de diagnostico sempre presente, com data/hora da
busca, rotulo unico (models.rotulo_status: 'Nao consultada' nao e
'Indisponivel'), traco explicito no campo vazio, detalhe inteiro (ate
2000 chars). GOLDEN-MASTER RECONGELADO DE PROPOSITO (spec 3.5 + M7):
coluna nova e hash de todas as abas com diagnostico_fixo.json (5 linhas).
dedup_esperado.json inalterado — conferido pelo ramo do dedup antes de
recongelar. O hash da aba nova depende de redigir/rotulo_status/
ORIGEM_LABEL/VAZIO: mudanca intencional neles = recongelar.
test_phase4: 61 -> 71."
git push origin master
```
