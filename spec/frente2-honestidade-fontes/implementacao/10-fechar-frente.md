# T10 · Fechar a frente 2: critérios de pronto da spec §7, duráveis, lições — registro de implementação

> Escopo: `../tasks/10-fechar-frente.md` (plano v4, linhas 2878-2882), com o brief do orquestrador de 23/09.
> Worktree `bn-t10`, branch `frente2/t10`, criada de master `a782d11`. Nela já estão T1–T9 e as trilhas FIX-FONTES e
> FIX-SAÍDA. Data: 23/09/2026. Commit: `docs: fecha a frente 2`. O SHA fica no `git log` da branch, porque um commit não
> consegue citar o próprio SHA.
> **Sem código de produção.** Todos os critérios da §7 passaram, então não houve motivo para parar.
> O que **não** está nesta task: push, merge, `/checkpoint` da fase 5, limpeza dos worktrees e qualquer toque na branch
> `deploy` (⛔). Isso fica com o orquestrador e, no caso do `deploy`, com o Rodrigo.

## 1. Critérios de pronto da spec §7

| § | Critério | Resultado | Evidência |
|---|---|---|---|
| 7.1 | V1–V11 verdes, cada um com o commit que o introduziu | ✅ | tabela na §2 abaixo; runner verde (§3) |
| 7.2 | runner TUDO VERDE com BASELINE atualizado; nenhum `[AVISO] cresceu` | ✅ | §3: 336, TUDO VERDE, nenhum aviso |
| 7.3 | `golden_master.py comparar` OK; `dedup_esperado.json` idêntico ao de `d054d5b` | ✅ | §4 |
| 7.4 | com LexML e TCU quebrados como estão hoje, é impossível ver "0 erros" | ✅ | §5: V11 7/7, com o LexML em `bloqueio_waf` e os atos do TCU em 500 ao vivo |
| 7.5 | auditoria de documentação feita e citada no commit final | ✅ com ressalva | §6: a faixa `dc99d73..HEAD` do plano sai **vazia por construção**; a auditoria real foi feita sobre `1c063ea..HEAD` |
| 7.6 | `_TODO.md`, `log.md` e `SESSION-ONBOARD` atualizados; push feito (D-C7) | ✅ duráveis · ⏳ push | §7. O push é do orquestrador (regra do brief: "não fazer push") |

## 2. V1–V11 → o commit que introduziu cada um

| V | O quê (spec §5) | Introduzido em | Ajustado depois |
|---|---|---|---|
| V1 | vocabulário fechado (`MOTIVOS`), defaults compatíveis | `da543be` (T1) | F-MT1 `9fb4aeb`: `FonteIndisponivel` passa a validar contra `MOTIVOS` |
| V2 | LexML: HTML real do desafio do Senado → `bloqueio_waf` | `8f5ccfc` (T2) | F-M2 `9fb4aeb` (WAF no URL cacheado) |
| V3 | LexML: HTML genérico / XML truncado → `resposta_ilegivel`; SRU válido → `ok` | `8f5ccfc` (T2) | `407e341` (URL no detalhe); F-N2 `9fb4aeb` (`srw:diagnostics`) |
| V4 | LexML: cada URL tentado uma vez por busca | `8f5ccfc` (T2) | — |
| V5 | TCU: atos 500×3 + acórdãos 200 → `http_5xx`, parcial, endpoint nomeado | `f044a3c` (T3) | `e8d59a4`; esquema real `e960497`/`bdd89a1` (T4) |
| V6 | TCU: 503 → `manutencao_503`; `None` na 2ª página → `parcial=True` | `f044a3c` (T3) | `e8d59a4`; F-MT503 `9fb4aeb` (conselho "após 21h") |
| V7 | `score_relevance_com_origem` (`heuristica`/`fallback_erro`; o wrapper mantém `list[float]`) | `7d8f1ce` (T6) | `6594cd8` (NaN/bool); F-UX2 `66b7145` (sem acento) |
| V8 | `_merge` leva a origem vencedora; `dedup_esperado.json` não muda | `7d5e69b` (T7) | — |
| V9 | planilha: 11 colunas, "Origem da nota", aba "Diagnostico da busca" | `6178f9d` (T8) | `04b2947`; S-SEC `624bed5`; `f749360` |
| V10 | golden recongelado no commit de V9, citando §3.5 | `6178f9d` (T8): `git log -- tests/golden/planilha_sha256.txt` → `6178f9d`, `d054d5b` | — |
| V11 | app dirigido pelo navegador: indisponíveis ≥ 1, aviso por fonte, origem no card | `49d19e1` (T9, `tools/dirigir_app.py`) | `0370a21`; S-N1 `624bed5` (o aviso deixou de ser "Nenhuma fonte catalogada…" quando só parte das catalogadas caiu; ver §5) |

### Commits reais da frente (`git log --oneline dc99d73..HEAD`, 94 commits)

O plano fala em "9 commits das tasks". A execução real, por trilhas e com ciclo de teste e review, ficou assim (código e
docs de cada task; os commits só de orquestração, `docs(frente2): … no ciclo`, checkpoints e dogfoods, estão no `git log`):

| Task / trilha | impl | fix do review | doc (`implementacao/`) | merge em master |
|---|---|---|---|---|
| T1 vocabulário | `da543be` | — | `ed50b6b` | direto em master |
| T2 LexML | `8f5ccfc` | `407e341` | `3be5d85` | `08d9d8c` (trilha A) |
| T3 TCU falhas | `f044a3c` | `e8d59a4` | `dfa6f6f` | `08d9d8c` |
| T4 TCU esquema | `e960497` | `bdd89a1` (reprovação do testador) + `38a110d` | `3751b2a` | `08d9d8c` |
| T5 Google | `5dad3c7` | `e70d9f6` | `a0fc6c6` | `08d9d8c` |
| T6 origem da nota | `7d8f1ce` | `6594cd8` | `272f83a` | `9e259ca` (trilha B) |
| T7 `_merge` | `7d5e69b` | — | `c68bd79` | `9e259ca` |
| T8 planilha | `6178f9d` | `04b2947` | `6eaf590` | `9e259ca` |
| T9 tela + V11 | `49d19e1` | `0370a21` | `0566533` | `d4cab80` |
| revisão final | — (só leitura; vereditos em `e024ec3`) | — | — | — |
| FIX-FONTES | `66b7145` + `9fb4aeb` | `cb9e0b5` | `89b2492` | `7322cc0` |
| FIX-SAÍDA | `624bed5` | `f749360` | `9a7a240` | `51883f6` |
| T10 | — | — | este arquivo | (orquestrador) |

⚠ A faixa `dc99d73..HEAD` inclui também `b12b39a` e `eb91277`, a história do repo A que entrou pelo merge `4f36080` (frente 1),
e os commits de spec/plano da frente 2 (`b489d00` … `a457e84`).

## 3. Runner

Comando (raiz do worktree): `export PYTHONIOENCODING=utf-8; ( time timeout 900 python tools/run_all_tests.py ) > runner.log 2>&1`.
⚠ Rodado com `run_in_background` do agente, **não** em foreground: a ferramenta Bash do agente corta em 600 s, e o
`timeout 900` pedido não caberia. Nada rodou em paralelo: o app e o V11 só subiram depois que o runner terminou (INSIGHTS,
T6/T2: runner em background travou quando concorreu com e2e).

```
suite                              | passed | failed | baseline |   tempo
-------------------------------------------------------------------------
test_searchers.py                  |     13 |      0 |       13 |  204.0s
test_llm_phase3.py                 |     65 |      0 |       65 |    2.8s
test_comprehensive.py              |     98 |      0 |       98 |   74.3s
test_phase4.py                     |     94 |      0 |       94 |    6.4s
tests/test_fontes_indisponiveis.py |     66 |      0 |       66 |    2.0s

TUDO VERDE

real	4m49.548s
exit=0
```

Total **336** (13 + 65 + 98 + 94 + 66), igual à soma do `BASELINE`. Nenhuma linha `[AVISO] cresceu`. O tempo caiu de ~9 min
para 4m50s. 📝 Suposição minha, não medida: a queda deve vir do teto de páginas e do cache de falha, porque o gargalo
medido na T3 era a paginação do TCU.

## 4. Golden-master e dedup

```
$ PYTHONIOENCODING=utf-8 python tools/golden_master.py comparar
golden-master OK
exit=0
$ git diff d054d5b -- tests/golden/dedup_esperado.json | wc -c
0
$ git diff --stat d054d5b -- tests/golden/
 tests/golden/diagnostico_fixo.json | 12 ++++++++++++
 tests/golden/planilha_sha256.txt   |  2 +-
 2 files changed, 13 insertions(+), 1 deletion(-)
```

`dedup_esperado.json` está byte-idêntico ao de `d054d5b`. Só a planilha foi recongelada, e só na T8 (`6178f9d`, V10), com o
`diagnostico_fixo.json` novo. As trilhas de conserto mantiveram o sha.

## 5. Gate visual V11 (rodado de novo)

App no ar na porta 8501, que estava livre (`netstat` sem LISTEN em 85x1). Foi lançado **sem as chaves de LLM**, que estão
definidas no ambiente desta máquina:
`env -u GEMINI_API_KEY -u GOOGLE_API_KEY -u OPENAI_API_KEY PYTHONIOENCODING=utf-8 python -m streamlit run app.py --server.headless true --server.port 8501`
(em `levantamento-normativos/`; não há `.streamlit/secrets.toml`, só o `.example`). Depois:
`env -u … PYTHONIOENCODING=utf-8 timeout 580 python tools/dirigir_app.py` (busca "LGPD" + "protecao de dados pessoais").

```
=== GATE V11 ===
  OK  relatório mostra ≥1 indisponível
  OK  bloqueio_waf visível na tela
  OK  aviso por fonte presente
  OK  TCU declarado parcial (acórdãos 200, atos 500 — cenário de 22/09)
  OK  origem no card
  OK  nenhum card sumiu (cards == N do cabeçalho)
  OK  '0 erros' não aparece
GATE V11 OK — abrir e OLHAR: …\bn-t10\tests\evidencia\v11_passo4.png
exit=0
```

Nenhuma chamada ao Gemini: o log do app tem uma única linha de LLM, `llm.gemini_client: LLM indisponivel — heuristica por
palavras-chave.` O app foi parado depois (`taskkill`), e a porta 8501 ficou livre.

**O PNG, olhado** (`tests/evidencia/v11_passo4.png`, 1440×1600, ignorado pelo `.gitignore:47`):
- Cabeçalho: "Passo 4 - Revisar Resultados (**7 normativos**)".
- Aviso amarelo: "Cobertura incompleta nas fontes catalogadas: lexml indisponível (bloqueio_waf); tcu respondeu
  parcialmente (0 resultado(s); http_5xx). O restante pode estar faltando."
- Legenda da heurística: "0% significa 'nenhuma palavra-chave na ementa', não 'irrelevante'".
- Relatório: "1 OK · 2 indisponíveis · 2 parciais · 1 sem resultado · 0 não consultadas (6 buscas)", com as 6 métricas.
- Seção vermelha: LexML com `bloqueio_waf`, a cadeia dos 3 URLs (busca/SRU 200 WAF, sru/SRU e srw/SRU 404), a URL com a
  query e "retry pulado".
- Seção laranja "Fontes parciais": TCU com "Acórdãos: ok (500 itens, 327 sem sumário — nesses só o título casa; **os 500
  acórdãos mais recentes, de 08/09/2026 a 22/09/2026**); Atos: http_5xx em HTTP 500 em 3 tentativas" e a URL.
- "LGPD em google" sem resultado.
- Nenhuma entidade HTML escapada em dobro. O texto de "0 erros" não aparece.

⚠ **O que o PNG não mostra:** os 7 cards ficam abaixo dos 1600 px. O `full_page=True` do script não rola o contêiner
interno do Streamlit, então a imagem para no relatório. As checagens "origem no card" e "cards == N" vêm do **texto** da
página (7 "Ver detalhes" = 7 do cabeçalho), não da imagem. E, como a CONTEXTO já registra para a T9, "cards == N" conta
**depois** do dedup: não enxerga a fusão fuzzy (🔴 D-C17).

⚠ **Diferença de texto em relação à spec §5 V11:** a spec pede o aviso "Nenhuma fonte catalogada respondeu". Desde a S-N1
(`624bed5`, bloqueador da revisão final), esse aviso só aparece quando **todas** as catalogadas morreram. Hoje o TCU
responde em parte, então a tela diz "Cobertura incompleta…", que é o texto honesto. O script do V11 checa "indisponível (",
que está presente. Não é falha do critério: é a correção de uma afirmação falsa.

## 6. Auditoria de documentação (os 2 comandos da Global Constraint)

### ⚠ A faixa do plano, `dc99d73..HEAD`, dá vazio por construção

```
$ git ls-tree -r --name-only dc99d73 | grep '\.py$'          # (nada)
$ git diff -U0 dc99d73..HEAD -- '*.py' | grep '^-' | grep -v '^---' | wc -l
0
```

Em `dc99d73` o repo não tinha nenhum `.py`: o código de A só chegou no merge `4f36080`. Todo `.py` aparece como arquivo
novo, sem linha removida. Esse zero não prova nada (lição nova no `LESSONS.md`, 23/09). A auditoria de verdade foi feita
nas faixas que têm código dos dois lados:
- `git diff -U0 4f36080..1c063ea -- '*.py' | grep '^-'` → 3 linhas, o `MODEL_NAME` antigo e os 2 comentários dele (`18ad975`,
  antes da frente 2). O porquê está no commit e no `LESSONS.md` de 22/09 ("modelo aposentado").
- **`git diff -U0 1c063ea..HEAD -- '*.py' | grep '^-' | grep -v '^---'` → 555 linhas, lidas inteiras** (18 arquivos,
  +3.773/−555).

### Comando 1: linhas removidas em `1c063ea..HEAD`, por arquivo

Para cada explicação removida, o lugar onde ela está agora (conferido com `git grep` na HEAD):

| Arquivo | O que saiu | Onde a explicação está agora |
|---|---|---|
| `app.py` | `_render_search_diagnostics` antigo (4 listas, rótulo "N OK, N erros", captions); bloco "LLM enrichment" condicionado a `llm_available()`; "Busca concluida" sempre verde; `html.escape` dentro de `st.markdown` | docstring nova do relatório (`app.py:947-957`, R2-B6/R3/UX1); "Isso NÃO significa que não existem normativos" mantido (`:524`, `:1117` e a caption do relatório); "buscadas com sucesso" mantida no ramo sem parcial; pontuação sempre (`:613-614`), categorização só com LLM (`:632-633`); comentários de XSS mantidos (`:1247`, `:1274`); `_resumo_da_busca` (S-N9) |
| `deduplicator.py` | "relevancia: keep the higher score" (docstring e comentário) | estendidos com a origem (`:105`, `:146`) |
| `excel_export.py` | "a single sheet named 'Normativos'"; assinaturas antigas | "two sheets" (`:445`); `generate_excel(…, diagnostico=None, quando=None)` (`:437`) |
| `llm/__init__.py` | docstring do módulo | estendida (`:3`) |
| `llm/gemini_client.py` | `score_relevance` como função principal; "List of float scores in [0.0, 1.0], same length"; logs | wrapper (`:458-464`) + `score_relevance_com_origem` (`:358`), "Notas em [0.0, 1.0]; mesmo tamanho que results" (`:379`), docstring do módulo (`:11`), log (`:390`) |
| `models.py` | docstrings de `situacao`, `status`, `retried` | estendidas (`:143`, `:204-206`, `:211`) |
| `searchers/google_searcher.py` | `_search_urls -> (list, str)`; os dois laços duplicados (passe + retry); mensagens 429/403; SSRF de um lookup só | docstring nova (`:137-143`); mensagens do CSE **literais** em `FonteIndisponivel` (`:192`, `:194`); "Use title/snippet…" e "If search results didn't include metadata…" em `_coletar` (`:441`, `:445`); SSRF (`:484`, `:522`) |
| `searchers/lexml_searcher.py` | comentário dos URLs de fallback; docstrings de `_fetch_sru`, `_search_keyword_safe` e `_parse_sru_response`; "raise so caller can distinguish from found 0"; "Mark remaining as retried-but-failed without calling API" | comentário estendido (`:25-29`); `_fetch_sru` com o cache em `self._sru_url` (`:400-410`); contrato novo de `_search_keyword_safe` ("nunca sem resultado", `:288-296`); `resposta_ilegivel` (`:566`); o retry pulado **deixou de marcar** `retried` de propósito (R2-H2, comentário `:231` e docstring `:133-136`) |
| `searchers/tcu_searcher.py` | "ementa field"; `_fetch_all_pages(_safe)` com retorno antigo; "return what we have"; log do 503 "Tente novamente mais tarde"; "Parse date from dataAta or dataSessao" | `sumario + titulo` (`:56`, `:239`); contrato `(itens, erro, parcial)` (`:251-256`, `:323-325`); "return what we have" citado na docstring (`:266`); janela 20h-21h e o conselho no detalhe (`:344`, `:373`, F-MT503 recuperou a perda parcial que a revisão final achou); precedência invertida de propósito (`:449`) |
| `test_comprehensive.py` | docstrings de 3 testes com o contrato antigo (`([], 0)` em XML malformado, CQL com rede, keywords vazias) | adaptadas (`:363`, `:510`); CQL dublado (F-T1) |
| `test_phase4.py` | "10 columns" | "all 11 expected columns" (`:421`) |
| `tools/golden_master.py` | docstrings de `_sha_planilha` e da função pública | estendidas (`:20`, `:74-78`, `:96`; as 2 frases que o plano derrubava foram restauradas na T8) |
| `tools/run_all_tests.py` | "Uma e pytest"; "Nasce com UMA suite pytest"; BASELINE antigo | generalizado (`:8-12`); "Nasceu com UMA suite pytest (emenda B2)" (`:39-41`) |

**Explicação removida sem destino: nenhuma.** A única perda parcial que a revisão de manutenção tinha achado, o conselho do
503, foi recuperada na F-MT503. **Comentários que continuam falsos** (não são perda, já estão em P3 via
`revisoes/final-manutencao.md`):
- `tcu_searcher.py:385` `# 2s, 4s, 8s` (com 3 tentativas são 2 s e 4 s);
- o nome `test_header_row_has_10_columns` (`test_phase4.py:426`), que afirma 11 colunas.

### Comando 2: `git grep` dos símbolos (188 linhas, lidas inteiras)

Contagem por arquivo:
- `app.py` 8, `excel_export.py` 3, `llm/__init__.py` 6, `llm/gemini_client.py` 5, `models.py` 4;
- `google_searcher.py` 3, `lexml_searcher.py` 10, `tcu_searcher.py` 12;
- `tools/golden_master.py` 4, `tools/split_frente2.py` 12 (texto do plano);
- testes 121 (`test_phase4` 50, `test_comprehensive` 37, `test_llm_phase3` 26, `tests/test_fontes_indisponiveis` 8).

Todo ponto de chamada de produção usa a assinatura atual:
- `app.py:623` chama `score_relevance_com_origem`. `score_relevance(` só aparece no wrapper, no `__init__` e nos testes.
- `generate_excel(…, diagnostico=, quando=)` em `app.py:1403-1406` e em `golden_master.py:102`.
- `_render_search_diagnostics(kw_statuses)` com um argumento nos dois pontos de chamada (`app.py:1129`, `:1142`).
- `_fetch_all_pages_safe` desempacota 3 valores (`tcu:88`, `:95`).
- As docstrings que citam `rotulo_status` / `e_indisponivel` (`models.py:85`, `:94`; `app.py:953`) dizem a verdade depois
  da FIX-SAÍDA.
- `golden_master.py:91` ("o hash depende de `models.redigir`") continua certo: `redigir` roda em `KeywordStatus.__setattr__`
  sobre `detalhe`/`error_message` do diagnóstico fixo, embora `excel_export` não o importe mais.

## 7. Duráveis

Todos editados no lugar, sem apagar conteúdo que ainda vale. 📝 marca o que é proposta minha.
- `_TODO.md`:
  - cabeçalho: frente 2 fechada, próxima é a frente 5;
  - frente 2 → ✅, com o resumo e o ponteiro para `execucao/`; frente 5 → "▶ próxima";
  - F9: nota ✅ nos 2 achados que viraram código (`relevancia_origem`; pontuação sempre + heurística sem acento);
  - os 4 P3 do plano reconciliados na linha das "Sobras das rodadas adversariais": fórmula ✅ S-SEC, CQL ✅ F-T1, agrupar o
    TCU e runner/`st.secrets` abertos, o segundo apontando para o insumo (c) da frente 5, sem duplicar;
  - nas sobras da execução: T2 11b ✅, T2 M2 ✅, `e_indisponivel` ✅ (parcial);
  - linha nova: fixture do SRU sem nota de procedência.
- `log.md`: entrada nova no topo, com o texto substituído no `SESSION-ONBOARD` arquivado **verbatim** dentro de
  `<details>`. Prova de sobrevivência por script: 37 linhas não vazias substituídas, 0 ausentes do `log.md`.
- `SESSION-ONBOARD-buscador.md`:
  - §2: frente 2 fechada;
  - §6: próxima é a frente 5; ⛔ `deploy` mantido ("o fim da frente 2 não é autorização"); 🔴 D-C17 visível, com as opções;
  - o arquivo baixou de 174 para 164 linhas.
- `BLOCKED-ON-RODRIGO.md` B-04: o texto do plano e o que foi medido:
  - janela do TCU de ~500 acórdãos, ≈ 2 semanas (08/09 a 22/09, de novo no V11 de hoje);
  - 327/500 = 65% sem sumário;
  - atos em 500;
  - LexML em WAF;
  - D-C17.
- `_DECISOES-PENDENTES.md` D-C17: continua 🔴. Ganhou uma linha dizendo que a frente fechou com ela aberta e onde entra o
  conserto (`deduplicator.py:256-280`, "Strategy 3"). A linha antiga `:251-270` foi anotada com a posição de hoje.
- `LESSONS.md`: 7 entradas novas no topo. A primeira é a faixa de auditoria vazia (achada nesta task). As outras vêm do
  INSIGHTS:
  - a revisão do estado inteiro;
  - identidade testada contra o volume real;
  - teste de proteção demonstrado falhando;
  - dar nome à procedência revela lixo;
  - golden recongelado provado por reconstrução;
  - as 3 lições do plano: (1) e (2) já estavam desde 22/09 e ganharam só um ponteiro (SSOT); a (3), captura do SRU,
    ficou pendente.

  As lições de máquina **não** foram repetidas: o bloco "Ponteiros" já lista as 5 do `~/.claude/ENVIRONMENT.md`.
- `00-overview.md`: nota de fechamento, com o total observado 336 contra os 283 do plano. `execucao/TODOS.md`: T10 ✅ **só
  a parte do coder**. A limpeza dos worktrees virou uma linha própria, desmarcada, e o `/checkpoint` fase 5 continua
  desmarcado.

## 8. Achados desta task (nenhum bloqueia a §7)

1. **A faixa de auditoria do plano é vazia por construção** (§6). Registrada como lição.
2. **`tests/fixtures/lexml_sru_valido.xml` não tem a nota "📝 escrita à mão, sem captura"** no cabeçalho, que a regra de
   22/09 do `LESSONS.md` exige. A procedência só aparece no plano. Não corrigi porque é dado de teste e esta task é só de
   docs. Foi para o `_TODO.md` P3, junto com a captura real, que continua pendente.
3. **O PNG do V11 não mostra os cards** (§5). 📝 Sugestão minha: rolar o contêiner do Streamlit antes do screenshot, ou
   tirar um segundo print. É P3 do `tools/dirigir_app.py`, que a revisão de manutenção já listou por outro motivo ("roda no
   import").
4. Runner rodado em background com `timeout 900`, e não em foreground, por causa do limite de 600 s da ferramenta (§3).
