---
task: 4
fase: "Fase 2 — Fontes honestas"
plan: docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md (linhas 1768-1882)
reference: spec/frente2-honestidade-fontes/reference/global-constraints.md
depends_on: [T3]
---

> Extraído **verbatim** do plano v4 (linhas 1768-1882). **O plano segue fonte de verdade**:
> divergência entre o plano e esta cópia → o plano ganha. Status em `../execucao/TODOS.md` — **não marque
> os checkboxes aqui**. Antes de começar, ler `../reference/global-constraints.md` (Global
> Constraints, Estrutura de arquivos, BASELINE por task). Ordem e dependências: `../00-overview.md`.

# T4 · TCU lê o esquema REAL do acórdão (⚠ emenda à spec §3.7)

**Fase 2 — Fontes honestas.**

## Depende de

- **T3** — `_texto_do_acordao`, o teste `xfail` a destravar, o dublê `_tcu_com` e o formato do `detalhe`

**Arquivos compartilhados com outras tasks:** `tcu_searcher.py` (T3) · `models.py` (docstring de `situacao`) · `test_comprehensive.py` · suíte nova · spec §3.7

## Critérios de aceite

> Derivados do próprio plano (os "Ver passar", "Expected" e gates da task e das Global
> Constraints) — **nenhum critério novo**. Números são previsões do plano: se o observado
> divergir, contar os `def test_` do bloco da task antes de suspeitar do código.

- Suíte nova → **`29 passed`** (o `xfail` vira passed + 3 novos) — Step 4.
- `_map_acordao` do acórdão real: `nome ← titulo`, `numero ← numeroAcordao/anoAcordao`, `data ← dataSessao`, `ementa ← sumario` **literal**, `link ← urlAcordao`, `situacao` literal (teste `test_tcu_acordao_real_…`).
- Data vazia continua `""`, não `None` (`assert r.data == ""` acrescentado em `test_tcu_map_acordao_missing_fields`) — ids preservados.
- `test_comprehensive` 98/98; `test_searchers` 13/13; golden OK (o corpus fixo não passa por `_map_acordao`).
- Spec §3.7 emendada; `BASELINE` 29; runner TUDO VERDE (total **251**); auditoria; commit + push.

---

## Conteúdo da task (verbatim do plano)

### Task 4: TCU — mapear o esquema REAL do acórdão (⚠ emenda à spec §3.7)

✅ **Fato medido em 22/09** (`tests/fixtures/tcu_acordaos_real.json`, `curl` em `recupera-acordaos?quantidade=2`): as chaves são `anoAcordao, colegiado, dataSessao, key, numeroAcordao, numeroAta, relator, situacao, sumario, tipo, titulo, urlAcordao, urlArquivo, urlArquivoPdf`. **Não existem `ementa`, `numero`, `ano`** — as três chaves que `_map_acordao` lê (`tcu_searcher.py:265-266,279`) e a que o filtro usa (`:104`). Consequência na v1.0: todo acórdão mapeia para `nome="Acordao / - TCU - Plenário"`, `numero="/"`, mesmo `id`, e **nunca casa palavra-chave** — a fonte diz "ok (500 itens)" e entrega zero. A spec §3.7 dizia "nenhum searcher muda o que mapeia"; **essa regra cai aqui**, porque manter o mapeamento é manter uma fonte estruturalmente cega. Decisão do Rodrigo em 22/09: "todos os consertos da v1 entram".

✅ **Limite medido pela rodada 2 (ao vivo):** `sumario` vem **nulo em 20/20** acórdãos das sessões mais recentes e em ~40% da janela de 500 registros; `titulo` é só "ACÓRDÃO N/AAAA ATA X/AAAA - PLENÁRIO". Ou seja: depois desta task, casam os acórdãos **que a API já preencheu** — a contagem "N sem texto" do detalhe (T3) é o que diz isso ao usuário. Não é "voltaram a casar"; é "deixaram de ser invisíveis".

📝 **Mapeamento** (literal, sem parafrasear): `nome ← titulo`; `numero ← f"{numeroAcordao}/{anoAcordao}"`; `data ← dataSessao` (⚠ R3: a precedência **inverte** — antes era `dataAta or dataSessao`; a API real só tem `dataSessao`; e o vazio continua `""`, **não** `None`, porque `data` entra no `id` e `None` mudaria o id de todo acórdão sem data); `orgao_emissor ← f"TCU - {colegiado}"`; `ementa ← sumario`; `link ← urlAcordao` (fallback `_build_acordao_link`); `situacao ← situacao` (a API traz `"OFICIALIZADO"` em 100% dos medidos — vai literal; a docstring de `NormativoResult.situacao` passa a admitir "o valor literal da fonte"). O filtro procura em `sumario` **e** `titulo`. Chaves antigas continuam aceitas como fallback.

> ⚠ **23/09 — EXECUÇÃO (teste da T4, commit `bdd89a1` na branch `frente2/trilha-a`):** `numero ← f"{numeroAcordao}/{anoAcordao}"`
> **colidia**: 1ª e 2ª Câmara numeram em séries próprias e se reúnem no mesmo dia → mesmo `id`, e o segundo acórdão sumia
> (212 colisões de id e ~1.175 fusões no dedup `tipo_numero`, medidos em 3.200 acórdãos reais). O executado é
> `numero ← f"{numeroAcordao}/{anoAcordao}-TCU-{colegiado}"` quando há colegiado (forma de citação do TCU, campos literais);
> no CÓDIGO executado, o assert do Step 1 (`r.numero == …`) e o bloco `_map_acordao` do Step 3 foram ajustados de
> acordo — os blocos abaixo NÃO foram editados e mostram a forma original. Registro:
> `spec/frente2-honestidade-fontes/execucao/revisoes/T4.md` e a nota "Complemento de 23/09" na spec §3.7. O texto abaixo
> fica como estava (histórico do plano).

**Files:** `tcu_searcher.py` (`_map_acordao`, `_texto_do_acordao`); `models.py` (docstring de `situacao`); `tests/test_fontes_indisponiveis.py`; `tools/run_all_tests.py`; spec §3.7.

- [ ] **Step 1: Testes** — (a) remover o decorator `@pytest.mark.xfail(...)` de `test_tcu_item_que_quebra_o_mapeamento_vira_erro_interno_declarado`; (b) em `test_tcu_500_num_endpoint_e_error_parcial_mesmo_com_o_outro_ok` trocar `assert len(resultados) == 0` por `assert len(resultados) == 1` (o acórdão real casa "turismo" no sumário); (c) acrescentar:

```python
def test_tcu_acordao_real_mapeia_titulo_numero_ano_sumario_link_situacao():
    from searchers.tcu_searcher import TCUSearcher
    r = TCUSearcher()._map_acordao(ACORDAO, "turismo")
    assert r.nome == ACORDAO["titulo"]
    assert r.numero == f'{ACORDAO["numeroAcordao"]}/{ACORDAO["anoAcordao"]}'
    assert r.data == ACORDAO["dataSessao"]
    assert r.ementa == ACORDAO["sumario"]          # literal, sem parafrase
    assert r.link == ACORDAO["urlAcordao"]
    assert r.orgao_emissor == f'TCU - {ACORDAO["colegiado"]}'
    assert r.situacao == ACORDAO["situacao"]


def test_tcu_acordaos_reais_tem_ids_distintos_e_casam_o_sumario(monkeypatch):
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=ACORDAOS_REAIS),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    resultados = s.search(["turismo"], max_results=10)
    ids = {s._map_acordao(a, "x").id for a in ACORDAOS_REAIS}
    assert len(ids) == len(ACORDAOS_REAIS)
    assert len(resultados) >= 1 and all("TURISMO" in (r.ementa + r.nome).upper() for r in resultados)


def test_tcu_pagina_cheia_com_numeros_distintos_da_page_size_resultados(monkeypatch):
    from searchers import tcu_searcher
    pagina = [dict(ACORDAO, key=f"A-{i}", numeroAcordao=str(i), titulo=f"ACÓRDÃO {i}/2026 - TURISMO") for i in range(tcu_searcher.PAGE_SIZE)]
    s, _ = _tcu_com(monkeypatch, {"recupera-acordaos": lambda p: RespostaFake(200, json_data=pagina if p["inicio"] == 0 else []),
                                  "recupera-atos-normativos": lambda p: RespostaFake(200, json_data=[])})
    resultados = s.search(["turismo"], max_results=100)
    assert len(resultados) == tcu_searcher.PAGE_SIZE
    assert len({r.id for r in resultados}) == tcu_searcher.PAGE_SIZE
```

- [ ] **Step 2: Ver falhar** — `-k "acordao_real or pagina_cheia or quebra_o_mapeamento or 500_num"` → 4 failed. E em `test_comprehensive.py`, no teste `test_tcu_map_acordao_missing_fields` (`:465-468`), acrescentar `assert r.data == ""` (R3: fixa que o vazio continua `""`).

- [ ] **Step 3: Implementar** — em `tcu_searcher.py`:

```python
    def _texto_do_acordao(self, item: dict) -> str:
        """Onde a palavra-chave e procurada: sumario + titulo (esquema real da
        API, medido em 22/09) — com fallback para `ementa` se a API tiver dois
        formatos. Antes lia so `ementa`, que a API nao devolve: zero match, sempre.
        Acordaos recentes vem SEM sumario (medido): so o titulo casa neles."""
        return " ".join(x for x in (item.get("sumario"), item.get("titulo"), item.get("ementa")) if x)

    def _map_acordao(self, item: dict, found_by: str) -> NormativoResult:
        """Map a raw acordao JSON item (esquema real de 22/09) to a NormativoResult.

        Campos literais da API, sem parafrase: titulo -> nome, sumario -> ementa,
        numeroAcordao/anoAcordao -> numero, dataSessao -> data, urlAcordao -> link,
        situacao -> situacao. Chaves antigas (numero/ano/ementa) aceitas como fallback.

        Returns:
            NormativoResult with tipo="Acordao TCU".
        """
        numero = str(item.get("numeroAcordao") or item.get("numero") or "")
        ano = str(item.get("anoAcordao") or item.get("ano") or "")
        colegiado = item.get("colegiado", "")
        date_raw = item.get("dataSessao") or item.get("dataAta") or ""   # precedencia invertida de proposito (API real)
        date_str = self._safe_date_format(str(date_raw)) if date_raw else ""  # "" e nao None: `data` entra no id
        return NormativoResult(
            nome=item.get("titulo") or f"Acordao {numero}/{ano} - TCU - {colegiado}",
            tipo="Acordao TCU",
            numero=f"{numero}/{ano}",
            data=date_str,
            orgao_emissor=f"TCU - {colegiado}",
            ementa=item.get("sumario") or item.get("ementa", "") or "",
            link=item.get("urlAcordao") or self._build_acordao_link(numero, ano),
            source="tcu",
            found_by=found_by,
            situacao=item.get("situacao") or "Nao identificado",
            relevancia=0.5,
            raw_data=item,
        )
```

Em `models.py`, docstring de `NormativoResult.situacao`: `"Vigente", "Revogado" ou "Nao identificado" (default)` → `"Vigente", "Revogado", "Nao identificado" (default) ou o valor literal da fonte (ex.: "OFICIALIZADO" do TCU).`

- [ ] **Step 4: Ver passar** — suíte `29 passed` (26 coletados na T3, o xfail vira passed, + 3 novos). `test_comprehensive` 98/98; `test_searchers` 13/13 (✅ rodada 2 verificou: nenhum teste antigo afirma o nome antigo; `test_comprehensive:424-441,461-468` passam pelo fallback). Golden OK (o corpus fixo não passa por `_map_acordao`).

- [ ] **Step 5: BASELINE 29; spec; commit**

Na spec §3.7: `> ⚠ Emendado em 22/09 (plano v3, T4): o mapeamento do acórdão do TCU MUDA — a API real não devolve as chaves que o código lia. Ver a fixture real. Limite medido: sumário vazio nos acórdãos recentes.`

```bash
git add levantamento-normativos/searchers/tcu_searcher.py levantamento-normativos/models.py levantamento-normativos/test_comprehensive.py levantamento-normativos/tests/ tools/run_all_tests.py docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md
git commit -m "fix(frente2): TCU le o esquema REAL do acordao (titulo/sumario/numeroAcordao/anoAcordao/urlAcordao/situacao)

Medido em 22/09: a API nao devolve ementa/numero/ano; _map_acordao lia so
essas chaves, entao todo acordao colapsava num id e nunca casava
palavra-chave. Emenda a spec 3.7. Textos literais, sem parafrase. Limite
medido (rodada 2): acordaos recentes chegam sem sumario — o detalhe conta
'N sem sumario'. Data vazia continua \"\" (id preservado). Suite: 25 -> 29."
git push origin master
```
