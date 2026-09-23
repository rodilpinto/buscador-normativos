---
task: 1
fase: "Fase 1 — Fundação"
plan: docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md (linhas 246-579)
reference: spec/frente2-honestidade-fontes/reference/global-constraints.md
depends_on: []
---

> Extraído **verbatim** do plano v4 (linhas 246-579). **O plano segue fonte de verdade**:
> divergência entre o plano e esta cópia → o plano ganha. Status só no `_TODO.md` — **não marque
> os checkboxes aqui**. Antes de começar, ler `../reference/global-constraints.md` (Global
> Constraints, Estrutura de arquivos, BASELINE por task). Ordem e dependências: `../00-overview.md`.

# T1 · vocabulário fechado, `redigir()`, `rotulo_status()`, `statuses_para_falha_total()`, `FonteIndisponivel`, `SOURCE_ID`

**Fase 1 — Fundação.**

## Depende de

- nada — é o gate inicial da frente (a frente 1 já entregou runner e golden-master).

**Arquivos compartilhados com outras tasks:** `models.py` (T4 volta nele, só docstring) · `test_phase4.py` (T7, T8, T9) · `tools/run_all_tests.py` (todas) · spec (T4)

## Critérios de aceite

> Derivados do próprio plano (os "Ver passar", "Expected" e gates da task e das Global
> Constraints) — **nenhum critério novo**. Números são previsões do plano: se o observado
> divergir, contar os `def test_` do bloco da task antes de suspeitar do código.

- `python -m pytest test_phase4.py -q` (em `levantamento-normativos/`) → **`58 passed`** (41 + 17 novos) — plano Step 5.
- `MOTIVOS` e `ORIGENS_RELEVANCIA` iguais aos conjuntos das Interfaces; `KeywordStatus` rejeita motivo inventado e redige `detalhe`/`error_message` **também em mutação pós-construção** (testes `TestVocabularioHonestidade`).
- `FonteIndisponivel` com motivo desconhecido vira `erro_interno`, sem levantar; `str(e)` é dinâmico.
- `BASELINE["test_phase4.py"] = 58`; `_rodar` do runner passa `env` com `GEMINI_API_KEY` e `GOOGLE_API_KEY` vazias (Step 6).
- Spec §3.1 emendada com a lista de `MOTIVOS` e a nota `⚠ Emendado em 22/09` (Step 6).
- Runner TUDO VERDE (total previsto **222**); `golden_master.py comparar` OK; os 2 comandos de auditoria lidos inteiros; commit + push (Step 7).

---

## Conteúdo da task (verbatim do plano)

### Task 1: Vocabulário, `redigir()`, `statuses_para_falha_total()`, `FonteIndisponivel`

**Files:**
- Modify: `levantamento-normativos/models.py` (topo; `NormativoResult:59-63` e `__post_init__:65-76`; `KeywordStatus:95-100`)
- Modify: `levantamento-normativos/searchers/base.py` (fim do arquivo)
- Test: `levantamento-normativos/test_phase4.py` (classes novas no fim)
- Modify: `tools/run_all_tests.py` (`BASELINE["test_phase4.py"]`)
- Modify: spec §3.1 (emenda dos motivos novos)

**Interfaces — Produces:**
- `MOTIVOS: frozenset[str]` = `{"", "bloqueio_waf", "http_5xx", "http_4xx", "rate_limit", "manutencao_503", "timeout", "conexao", "resposta_ilegivel", "endpoint_inexistente", "nao_consultada", "erro_interno"}`
- `ORIGENS_RELEVANCIA: frozenset[str]` = `{"modelo", "heuristica", "fallback_erro", "padrao_fonte"}`
- `redigir(texto: str, limite: int = 2000) -> str` — redige `key=`/`cx=`/`api_key=`/`apikey=`/`token=`/`access_token=`/`secret=`/`client_secret=`/`password=` (valor → `***`) e `Bearer <x>`, remove chars de controle (exceto `\n`, `\t`), prefixa `'` **só** se começar com `=` (R2), corta em `limite` (2000 = teto de célula; **não** é para caber na tela — R2-B1).
- `rotulo_status(s: KeywordStatus) -> str` — `"OK" | "Sem resultado" | "Indisponível" | "Não consultada"` (o último quando `motivo == "nao_consultada"`); usado pela planilha e pela tela (R2-B6).
- `KeywordStatus(..., motivo: str = "", detalhe: str = "", parcial: bool = False)`; `__post_init__`: `ValueError` se `motivo ∉ MOTIVOS`; **`__setattr__` aplica `redigir` a `detalhe` e `error_message` em toda atribuição** — construtor e mutações posteriores (R2-H1).
- `NormativoResult(..., relevancia_origem: str = "padrao_fonte")`; `__post_init__`: `ValueError` se fora de `ORIGENS_RELEVANCIA`.
- `statuses_para_falha_total(source: str, keywords: list[str], exc: BaseException) -> list[KeywordStatus]` — um `error`/`erro_interno` por keyword.
- `searchers.base.FonteIndisponivel(motivo, detalhe="")` — motivo desconhecido vira `erro_interno`; `detalhe` passa por `redigir` já aqui (o log sai redigido); `str(e)` lê `self.motivo`/`self.detalhe` dinamicamente.
- `searchers.base.BaseSearcher.SOURCE_ID: str` — `"lexml" | "tcu" | "google"`, definido em cada subclasse (T2/T3/T5); é o `source` de todo `KeywordStatus` e o que `app.py` usa no `except`.

- [ ] **Step 1: Testes que falham** — ao fim de `levantamento-normativos/test_phase4.py`:

```python
# ===========================================================================
#  FRENTE 2 — VOCABULARIO DE HONESTIDADE (spec 2026-09-22 §3.1, plano v2 T1)
# ===========================================================================

from models import (KeywordStatus, MOTIVOS, ORIGENS_RELEVANCIA, redigir,
                    statuses_para_falha_total)


class TestVocabularioHonestidade:
    def test_motivos_fechados(self):
        assert MOTIVOS == frozenset({
            "", "bloqueio_waf", "http_5xx", "http_4xx", "rate_limit", "manutencao_503",
            "timeout", "conexao", "resposta_ilegivel", "endpoint_inexistente",
            "nao_consultada", "erro_interno",
        })

    def test_origens_fechadas(self):
        assert ORIGENS_RELEVANCIA == frozenset({"modelo", "heuristica", "fallback_erro", "padrao_fonte"})

    def test_keyword_status_construtor_antigo_continua_valido(self):
        s = KeywordStatus(keyword="lgpd", source="lexml", result_count=0, status="empty")
        assert (s.motivo, s.detalhe, s.parcial) == ("", "", False)

    def test_keyword_status_aceita_motivo_valido(self):
        s = KeywordStatus(keyword="lgpd", source="lexml", status="error",
                          motivo="bloqueio_waf", detalhe="HTTP 200 text/html")
        assert s.motivo == "bloqueio_waf"

    def test_keyword_status_rejeita_motivo_inventado(self):
        with pytest.raises(ValueError, match="motivo"):
            KeywordStatus(keyword="lgpd", source="lexml", status="error", motivo="waf")

    def test_keyword_status_redige_detalhe_e_error_message(self):
        s = KeywordStatus(keyword="k", source="google", status="error", motivo="http_4xx",
                          detalhe="GET https://g/api?key=AIzaSECRET&cx=abc&q=x -> 403",
                          error_message="500 for url: https://g/x?key=AIzaSECRET")
        assert "AIzaSECRET" not in s.detalhe and "key=***" in s.detalhe
        assert "AIzaSECRET" not in s.error_message

    def test_keyword_status_redige_tambem_na_mutacao_pos_construcao(self):
        """R2-H1: os retries mutam error_message/detalhe depois do construtor."""
        s = KeywordStatus(keyword="k", source="google", status="error", motivo="http_5xx")
        s.error_message = "Retry failed: 500 for url: https://g/x?key=AIzaSECRET"
        s.detalhe = "GET https://g/x?cx=SEGREDO -> 500"
        assert "AIzaSECRET" not in s.error_message and "SEGREDO" not in s.detalhe

    def test_normativo_origem_default_e_padrao_fonte(self):
        assert _make_result().relevancia_origem == "padrao_fonte"

    def test_normativo_rejeita_origem_inventada(self):
        with pytest.raises(ValueError, match="relevancia_origem"):
            NormativoResult(nome="x", tipo="Lei", numero="1", data=None, orgao_emissor="",
                            ementa="", link="", source="lexml", found_by="k",
                            relevancia_origem="ia")


class TestRedigir:
    def test_redige_segredos_em_query_e_bearer(self):
        assert redigir("u?key=ABC&cx=DEF&api_key=GHI&token=JKL&access_token=MNO&client_secret=PQR&q=x") == \
            "u?key=***&cx=***&api_key=***&token=***&access_token=***&client_secret=***&q=x"
        assert redigir("Authorization: Bearer eyJabc.def") == "Authorization: Bearer ***"

    def test_remove_controle_e_corta_no_meio_com_marcador(self):
        assert redigir("a\x00b\x07c\n") == "abc\n"
        assert len(redigir("x" * 1500)) == 1500
        cortado = redigir("A" * 1990 + " | GET https://fonte/x | retry pulado")
        assert len(cortado) <= 2000 and "[…cortado" in cortado          # R3: sufixo (URL, 'retry pulado') sobrevive
        assert cortado.startswith("AAAA") and cortado.endswith("| retry pulado")

    def test_neutraliza_so_formula(self):
        assert redigir('=HYPERLINK("http://evil","clique")').startswith("'=")
        assert redigir("-1") == "-1" and redigir("+1") == "+1" and redigir("@x") == "@x"   # openpyxl so trata '=' como formula

    def test_texto_normal_intacto(self):
        assert redigir("GET https://x/y?q=lgpd -> 200 text/html") == "GET https://x/y?q=lgpd -> 200 text/html"


class TestRotuloStatus:
    def test_rotulos(self):
        from models import rotulo_status
        mk = lambda **k: KeywordStatus(keyword="k", source="lexml", **k)
        assert rotulo_status(mk(status="ok")) == "OK"
        assert rotulo_status(mk(status="empty")) == "Sem resultado"
        assert rotulo_status(mk(status="error", motivo="bloqueio_waf")) == "Indisponível"
        assert rotulo_status(mk(status="error", motivo="nao_consultada")) == "Não consultada"   # R2-B6


class TestStatusesParaFalhaTotal:
    def test_um_status_por_keyword(self):
        sts = statuses_para_falha_total("tcu", ["a", "b"], AttributeError("'int' object has no attribute 'strip'"))
        assert [s.keyword for s in sts] == ["a", "b"]
        assert all((s.source, s.status, s.motivo) == ("tcu", "error", "erro_interno") for s in sts)
        assert "AttributeError" in sts[0].detalhe and "strip" in sts[0].detalhe

    def test_lista_vazia_de_keywords_da_um_status_generico(self):
        sts = statuses_para_falha_total("lexml", [], RuntimeError("x"))
        assert len(sts) == 1 and sts[0].keyword == "(todas)"
```

- [ ] **Step 2: Rodar e ver falhar** — em `levantamento-normativos/`: `python -m pytest test_phase4.py -q` → `ImportError: cannot import name 'MOTIVOS'` na coleta.

- [ ] **Step 3: `models.py`** — logo após `from dataclasses import dataclass, field`, acrescentar `import re` e:

```python
# ---------------------------------------------------------------------------
# Vocabulario fechado de honestidade (spec 2026-09-22 §3.1; plano v2 T1)
# ---------------------------------------------------------------------------

# Por que uma fonte NAO pode ser consultada. String (nao Enum) para caber na
# planilha e no JSON sem conversao. "" = nao se aplica (status ok/empty).
MOTIVOS: frozenset[str] = frozenset({
    "",
    "bloqueio_waf",          # HTTP 200 com pagina de desafio (Senado/LexML, medido em 22/09)
    "http_5xx",              # 5xx depois dos retries
    "http_4xx",              # 4xx que nao e 404 nem 429 (401, 403...) — sem retry
    "rate_limit",            # 429 / RatelimitException — esperar, nao "fonte caiu"
    "manutencao_503",        # 503 (o TCU tem janela diaria 20h-21h BRT; hipotese, ver detalhe)
    "timeout",               # requests.Timeout
    "conexao",               # requests.ConnectionError
    "resposta_ilegivel",     # HTTP 200, mas o corpo nao e o formato esperado
    "endpoint_inexistente",  # 404 em todos os URLs da cadeia
    "nao_consultada",        # a busca parou antes desta palavra-chave (limite de resultados/keywords)
    "erro_interno",          # excecao nao prevista — bug nosso, nao da fonte
})

# De onde veio a nota de relevancia. Tres procedencias colapsavam no mesmo
# numero (0.5 podia ser modelo, fallback de erro ou default da fonte).
ORIGENS_RELEVANCIA: frozenset[str] = frozenset({
    "modelo",         # nota dada pelo LLM
    "heuristica",     # fracao das palavras-chave presentes na ementa (deterministica)
    "fallback_erro",  # o LLM falhou nesse lote; 0.5 rotulado como tal
    "padrao_fonte",   # constante que o searcher atribui; nenhuma avaliacao rodou
})

_RE_SEGREDO = re.compile(r"(?i)(?<![A-Za-z0-9])(key|cx|api[_-]?key|token|access_token|secret|client_secret|password|sig(?:nature)?)=([^&\s]+)")
_RE_BEARER = re.compile(r"(?i)\bBearer\s+\S+")
_RE_CONTROLE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def redigir(texto: str, limite: int = 2000) -> str:
    """Torna um texto vindo de fora seguro para tela, log e planilha.

    Redige segredos em query string e Bearer (a mensagem do requests inclui a
    URL inteira: `?key=AIza...` ia para a aba de diagnostico), remove chars de
    controle (openpyxl levanta IllegalCharacterError), neutraliza formula
    (so '=': e o unico prefixo que o openpyxl trata como formula) e corta em
    `limite`. O limite e o TETO DE CELULA (2000), nao um tamanho de tela:
    com 300, a URL real do LexML (~230 chars) engolia o titulo do desafio e a
    cadeia de URLs — o fato central da frente nunca chegava a planilha
    (rodada 2, R2-B1). Quem precisa de texto curto corta na renderizacao.
    """
    texto = _RE_SEGREDO.sub(lambda m: f"{m.group(1)}=***", texto or "")
    texto = _RE_BEARER.sub("Bearer ***", texto)
    texto = _RE_CONTROLE.sub("", texto)
    if texto[:1] == "=":
        texto = "'" + texto
    if len(texto) > limite:
        # corta no MEIO, com marca: o comeco (fato) e o fim (URL, 'retry pulado')
        # sao o que importa; cortar o sufixo em silencio apagava exatamente os
        # appends que a T2/T5 fazem no detalhe (rodada 3)
        marca = f" […cortado {len(texto) - limite} chars…] "
        metade = (limite - len(marca)) // 2
        texto = texto[:metade] + marca + texto[-metade:]
    return texto


def rotulo_status(s: "KeywordStatus") -> str:
    """Rotulo humano de um KeywordStatus — UNICO lugar (planilha e tela usam).

    `nao_consultada` tem status="error" (vocabulario fechado), mas NAO e
    "indisponivel": a palavra-chave simplesmente nao foi enviada. Rotula-la de
    indisponivel fazia o caminho feliz (10 keywords, max_results atingido)
    parecer uma fonte caida (rodada 2, R2-B6).
    """
    if s.status == "error" and s.motivo == "nao_consultada":
        return "Não consultada"
    return {"ok": "OK", "empty": "Sem resultado", "error": "Indisponível"}.get(s.status, s.status)
```

Em `NormativoResult`: docstring ganha (após `relevancia`):

```
        relevancia_origem: De onde veio ``relevancia``. Um de ORIGENS_RELEVANCIA.
              Default "padrao_fonte": os searchers atribuem uma constante e
              nenhuma avaliacao rodou ainda.
```

campo `relevancia_origem: str = "padrao_fonte"` após `relevancia: float = 0.0`; e no `__post_init__`, **antes** do hash:

```python
        if self.relevancia_origem not in ORIGENS_RELEVANCIA:
            raise ValueError(
                f"relevancia_origem={self.relevancia_origem!r} fora de "
                f"ORIGENS_RELEVANCIA {sorted(ORIGENS_RELEVANCIA)}"
            )
```

Em `KeywordStatus`: docstring ganha `motivo`, `detalhe`, `parcial` (texto da spec §3.1); a linha `status: str = "ok"  # "ok" | "empty" | "error"` vira `... | "error" (= fonte indisponivel; ver motivo)`; após `retried: bool = False`: A docstring de `retried` passa a dizer (R3): *a palavra-chave foi REENVIADA à fonte depois do passe principal (LexML/Google); tentativas HTTP internas (o TCU faz 3) NÃO contam — ficam no detalhe; retry pulado NÃO marca*. E a de `parcial`: *a coleta NÃO terminou — paginação interrompida (ok/empty) ou, no TCU, um endpoint caído com o outro vivo (error)*.

```python
    motivo: str = ""
    detalhe: str = ""
    parcial: bool = False

    def __post_init__(self) -> None:
        if self.motivo not in MOTIVOS:
            raise ValueError(f"motivo={self.motivo!r} fora de MOTIVOS {sorted(MOTIVOS)}")

    def __setattr__(self, nome: str, valor) -> None:
        # Tudo que vem de fora passa por redigir() em TODA atribuicao — o
        # construtor (dataclass usa setattr) e as mutacoes dos retries
        # (`st.error_message = f"Retry failed: {erro}"`). So no __post_init__
        # deixava a porta dos fundos aberta (rodada 2, R2-H1).
        if nome in ("detalhe", "error_message"):
            valor = redigir(valor or "")
        object.__setattr__(self, nome, valor)
```

Ao fim de `models.py`:

```python
def statuses_para_falha_total(source: str, keywords: list[str], exc: BaseException) -> list[KeywordStatus]:
    """Quando search() de uma fonte LEVANTA, a fonte nao pode sumir do relatorio.

    Antes, app.py engolia a excecao e nao gravava status nenhum: a fonte
    desaparecia da tela e da aba de diagnostico, e o Passo 4 dizia "nenhum
    normativo encontrado" (achado H2 da rodada adversarial de 22/09).
    """
    detalhe = f"{type(exc).__name__}: {exc}"
    alvo = keywords or ["(todas)"]
    return [
        KeywordStatus(keyword=k, source=source, result_count=0, status="error",
                      motivo="erro_interno", detalhe=detalhe, error_message=detalhe)
        for k in alvo
    ]
```

- [ ] **Step 4: `searchers/base.py`** — em `BaseSearcher`, logo após `RATE_LIMIT_JITTER: float = 0.5`:

```python
    # Identificador curto da fonte — o `source` de todo KeywordStatus e o que
    # app.py usa quando search() levanta. Cada subclasse define o seu (T2/T3/T5).
    # Antes, app.py mapeava por nome de exibicao com fallback "google", e uma
    # fonte nova que levantasse viraria "web aberta" (rodada 2).
    SOURCE_ID: str = ""
```

E ao fim do arquivo:

```python
class FonteIndisponivel(Exception):
    """A fonte NAO pode ser consultada — distinto de "consultei e nao achei".

    Nasce no searcher (bloqueio, 5xx, timeout, corpo ilegivel) e sobe ate o
    KeywordStatus como status="error" + motivo + detalhe. Antes, um HTML de
    desafio com HTTP 200 virava lista vazia e a UI dizia "0 erros" (22/09).

    Um motivo desconhecido aqui vira erro_interno com o valor original no
    detalhe — barulho, nunca crash da fonte inteira (a validacao dura e a do
    KeywordStatus). O detalhe passa por models.redigir() JA AQUI, porque os
    searchers logam `str(e)` antes de qualquer KeywordStatus existir: sem isso
    a URL com a chave do CSE ia inteira para o log (rodada 2).
    """

    _CONHECIDOS = {
        "bloqueio_waf", "http_5xx", "http_4xx", "rate_limit", "manutencao_503", "timeout",
        "conexao", "resposta_ilegivel", "endpoint_inexistente", "nao_consultada", "erro_interno",
    }

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        if motivo not in self._CONHECIDOS:
            detalhe = f"motivo desconhecido {motivo!r}: {detalhe}"
            motivo = "erro_interno"
        from models import redigir  # models nao importa searchers: sem ciclo
        super().__init__(motivo)
        self.motivo = motivo
        self.detalhe = redigir(detalhe)

    def __str__(self) -> str:  # dinamico: quem edita .detalhe depois nao deixa str() velho
        return f"{self.motivo}: {self.detalhe}" if self.detalhe else self.motivo
```

Um teste em `test_phase4.py` (classe `TestVocabularioHonestidade`) para isso:

```python
    def test_fonte_indisponivel_motivo_desconhecido_vira_erro_interno_e_str_dinamico(self):
        from searchers.base import FonteIndisponivel
        e = FonteIndisponivel("http5xx", "GET x -> 500")
        assert (e.motivo, "http5xx" in e.detalhe) == ("erro_interno", True)
        e.detalhe = "novo"
        assert str(e) == "erro_interno: novo"
```

- [ ] **Step 5: Rodar e ver passar** — `python -m pytest test_phase4.py -q` → **`58 passed`** (41 + 17 novos: 10 em `TestVocabularioHonestidade`, 4 em `TestRedigir`, 1 em `TestRotuloStatus`, 2 em `TestStatusesParaFalhaTotal`). ⚠ Use o observado: se não for 58, contar os `def test_` antes de suspeitar do código.

- [ ] **Step 6: BASELINE, runner sem LLM, golden, spec** — `BASELINE["test_phase4.py"] = 58`. Em `tools/run_all_tests.py`, `_rodar` passa a chamar `subprocess.run(cmd, cwd=APP, env={**os.environ, "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, ...)` (+ `import os`), com o comentário `# 'roda sem LLM' so e garantido se o runner nao herdar a chave (rodada 2: test_comprehensive achou GEMINI_API_KEY no ambiente e levou 429 do Gemini)`. `python tools/golden_master.py comparar` → OK. Spec §3.1: trocar a lista de `motivo` pela de `MOTIVOS` acima e acrescentar `> ⚠ Emendado em 22/09 (plano v3, T1): endpoint_inexistente, erro_interno, http_4xx, rate_limit, nao_consultada; redigir() em toda atribuição de detalhe/error_message; rotulo_status() é o único rótulo humano; parcial pode acompanhar ok, empty e (TCU, um endpoint vivo) error.`

- [ ] **Step 7: Auditoria + commit**

```bash
git add levantamento-normativos/models.py levantamento-normativos/searchers/base.py levantamento-normativos/test_phase4.py tools/run_all_tests.py docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md
git commit -m "feat(frente2): vocabulario de honestidade, redigir() e FonteIndisponivel

MOTIVOS/ORIGENS_RELEVANCIA fechados; KeywordStatus ganha motivo/detalhe/
parcial e redige segredos/controle/formula em TODA atribuicao (a chave do
Google CSE ia para a planilha, inclusive pelo retry). rotulo_status() e
SOURCE_ID nascem aqui. Runner roda as suites com GEMINI_API_KEY vazia. statuses_para_falha_total() para a fonte
que levanta nao sumir do relatorio. FonteIndisponivel em searchers/base.
test_phase4: 41 -> 58."
git push origin master
```
