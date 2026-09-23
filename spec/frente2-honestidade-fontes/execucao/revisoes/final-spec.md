# Revisão final · conformidade ponta a ponta com a spec (code-reviewer, `d4cab80`, 23/09)

121 testes das duas suítes pytest verdes; golden OK; `dedup_esperado.json` intocado desde `d054d5b`.

| Req | Status |
|---|---|
| §3.1 V1 vocabulário/`redigir`/`rotulo_status` | MET |
| §3.2 V2-V4 LexML | PARTIAL (N2) |
| §3.3 V5-V6 TCU | MET |
| §3.4 V7-V8 origem da nota / `_merge` | MET |
| §3.5 V9-V10 coluna + aba | MET |
| §3.6 relatório e cards | MET |
| §3.6 aviso "Nenhuma fonte catalogada respondeu" | **NOT MET** num cenário (N1) |
| V11 | PARTIAL — verde, mas só exercita TCU com atos em 500; nunca "LexML morto + TCU saudável" |
| §7.1-7.4 | MET · §7.5-7.6 PENDENTE (T10) |

## Bloqueador
- **N1** `app.py:1023` — `if mortas and not parciais_fonte` não confere que `mortas` cobre TODAS as fontes de `por_fonte`.
  Repro (AppTest): LexML `bloqueio_waf` + TCU `ok, result_count=1` com 1 resultado → "**Nenhuma fonte catalogada (lexml,
  tcu) entregou resultado** … lexml indisponível" com o card do TCU na tela. É o estado provável assim que o TCU atos
  voltar. Conserto: `todas_mortas = mortas and set(mortas) == set(por_fonte)`; senão cair em "Cobertura incompleta"
  listando só as mortas; AppTest "LexML morto, TCU saudável".

## Importante
- **N2** `lexml_searcher.py:575-589` — XML válido que não é resultado vira "Sem resultado": SRU com `<srw:diagnostics>`
  (Query syntax error, `numberOfRecords=0`) → `empty`; `<error><message>…indisponivel</message></error>` → `empty`.
  Conserto: raiz que não termina em `searchRetrieveResponse` → `resposta_ilegivel`; `srw:diagnostics` presente → levantar
  com a `diag:message` no detalhe.
- **N3** coleta TCU **parcial sem match** aparece como "nada encontrado" limpo: sem aviso, `st.info` "Tente ampliar…"
  (`app.py:1047-1054`) e legenda "buscadas **com sucesso**" (`:980-983`); `parciais_fonte` (`:1019`) exige `erros > 0`.
  Conserto: contar `parcial` em `parciais_fonte`; `st.warning` no ramo sem resultado quando há parciais; tirar "com sucesso"
  dos parciais.
- **N4** `tcu_searcher.py:141-143,161-162` — `kw_count` só conta ids novos: keyword 2 que casa um acórdão já trazido pela 1
  sai `empty`; o LexML diz `ok` 0; o TCU nunca acrescenta ao `found_by`. Pré-existente, mas quebra "empty = consultei e não
  achei". Conserto: contar matches, separar "novos", acrescentar ao `found_by` como o LexML.

## Menor
- N5 `max_results` corta em silêncio a keyword EM CURSO (sai `ok N`, sem `parcial`) — tcu:137/146, lexml:462/495, google:313.
- N6 os dois endpoints do TCU caídos → o aviso por fonte mostra só o motivo dos acórdãos (o detalhe tem os dois).
- N7 `nome` montado por nós parecendo título da fonte (TCU atos `f"{tipo} TCU n. {numero}"`, LexML sem `dc:title`, Google
  com a URL) — pré-existente, contra "título literal".
- N8 aba de diagnóstico: `redigir(s.keyword)` altera a keyword (`token=x` → `token=***`) — só neutralizar fórmula.
- N9 Passo 3: "Busca concluida - N normativos" sempre verde, inclusive 0 com tudo indisponível (`app.py:618,644`).

## Conhecidos
- D-C17: concorda 🔴 (perda silenciosa; o `_merge` ainda troca o `nome` pelo do outro acórdão); não deveria passar do
  início da frente 5. P3: concorda, exceto T2 M2 (WAF no `_sru_url` cacheado), que é da classe do N2 → subir para importante.
