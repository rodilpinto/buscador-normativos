# Revisão final · manutenibilidade, arquitetura e preservação de docs (code-reviewer, `1c063ea..d4cab80`, 23/09)

Veredito: sólido. **Auditoria de preservação limpa** — nenhuma explicação removida sem casa nova (uma perda parcial abaixo).
Line endings: os 21 arquivos alterados em `w/crlf`.

## Importante
1. `searchers/base.py:165-168` — `FonteIndisponivel._CONHECIDOS` é cópia de `models.MOTIVOS` sem teste de sincronia: um
   motivo novo só em `MOTIVOS` vira `erro_interno` em silêncio. → validar contra `MOTIVOS - {""}` (o import lazy já existe)
   ou teste de sincronia.
2. `models.py:79` — docstring de `rotulo_status` diz "UNICO lugar (planilha e tela usam)"; a tela não usa. → corrigir.
3. `google_searcher.py:297-300` — o detalhe novo do `bloqueio_waf` diz "0 resultados em N palavras-chave **seguidas**", mas
   `consecutive_zeros` conta todo status anterior com 0 (inclusive erro), não seguidos. → corrigir o texto ou a contagem.
4. Deriva do retry LexML × Google: guarda B2 (não rebaixar motivo) só no LexML; recuperação do Google apaga o detalhe;
   "retry pulado: max_results" só no Google. → helper pequeno `aplicar_retry(...)` em `base.py` (sem reescrita).
5. `app.py:1003-1010` duplica a regra "indisponível" de `:929` → `e_indisponivel(s)` em `models.py`.

## Menor (resumo)
`_exigir_sru`/`_exigir_json` duplicam regex de `<title>` e marcadores de WAF; formatos de prefixo de página e cortes de
corpo divergentes (120 × 160; `[:200]` em `erro_interno`); timeout/conexão do Google sem query (talvez de propósito — dizer);
`motivo` não validado em `__setattr__`; `_fetch_sru -> Optional[str]` já não devolve None; tupla de URLs repetida;
`import time` local repetido; `_erro_paginacao` fora do `__init__`; `base.py:63-65` docstring desatualizada e
`keyword_statuses` não declarado; definição de `fallback_erro` em `models.py:37` estreita demais; rótulos de origem em dois
lugares; `_md_codigo` docstring; `f.get("parcial")` redundante; ids de fonte hardcoded em `app.py:1002/:1019`; `app.py`
com 1.427 linhas (helpers de escape → `ui_texto.py` como primeiro corte); `test_header_row_has_10_columns` afirma 11;
`tcu_searcher.py:324` comentário "2s, 4s, 8s" errado (são 2s e 4s); `google_searcher.py:167` cita linha do ddgs;
`tools/dirigir_app.py` roda no import.

## Perda parcial de explicação
O log do 503 do TCU dizia "…das 20h às 21h (horário de Brasília). **Tente novamente mais tarde.**" — a hipótese da janela
sobrevive no detalhe (`tcu:311`), o conselho de tentar depois sumiu. → acrescentar "tente de novo após 21h BRT" ao
detalhe quando a hora está dentro da janela.
