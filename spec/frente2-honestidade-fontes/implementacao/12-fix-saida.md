# FIX-SAÍDA · Revisão final, trilha app/planilha/models: a planilha e a tela sem afirmação falsa — registro de implementação

> Escopo: a tabela **FIX-SAÍDA** de `../execucao/revisoes/final-triagem.md`. Os achados vêm de `final-spec.md` (N1, N3, N8,
> N9), `final-seguranca.md` (crítico), `final-ux.md` (1) e `final-manutencao.md` (2).
> Worktree `bn-fix-saida`, branch `frente2/fix-saida` (criada de master `e024ec3`), 23/09/2026. A trilha paralela FIX-FONTES
> (`bn-fix-fontes`) cuida de `searchers/*` e `llm/*`, que esta trilha não tocou.
> Commits: **`624bed5`** `fix(frente2): revisao final, trilha FIX-SAIDA — planilha e tela sem afirmacao falsa` ·
> **`f749360`** `fix(frente2): review da FIX-SAIDA — caractere de controle nao derruba a exportacao; rotulo_status usa e_indisponivel`.
> Teste independente: **APROVADO**. Revisão de código: **APROVADO**, sem bloqueador nem importante. 1 menor e 1 achado do testador
> (caractere de controle), aceito pelo orquestrador para correção nesta trilha; os dois foram aplicados no `f749360`.
> Vereditos completos: `../execucao/revisoes/fix-saida.md`.

## 1. O que foi feito, item por item (teste primeiro; falha → sucesso)

| id | arquivo · símbolo | o que mudou | falhou com → passou |
|---|---|---|---|
| **S-SEC** (crítico) | `excel_export._forcar_texto(cell)`, chamado no fim de cada volta de `_write_data_row` e em cada célula da aba de diagnóstico | `data_type = "s"` **depois** de atribuir o valor. O openpyxl grava `<c t="inlineStr">` com o texto **literal**: sem apóstrofo e sem troca de caractere. Cobre todas as colunas de texto: nome, tipo, número, data, órgão, ementa, link, categoria, situação e origem. | `AssertionError: ('nome', 'f')`; `<f>` presente em `sheet1.xml` → `TestSecFormulaNaAbaNormativos` (2) verde |
| **S-N1** (bloqueador) | `app.render_step4`: `todas_mortas = bool(mortas) and set(mortas) == set(por_fonte)` | "Nenhuma fonte catalogada entregou" só aparece quando todas morreram. Senão, "Cobertura incompleta" lista só as mortas e as parciais. | `'Nenhuma fonte catalogada' not in 'Nenhuma fon…'` → `TestAvisoPorFonte::test_lexml_morto_tcu_saudavel_…` verde |
| **S-UX1+N3** | `models.e_indisponivel(s)` 📝 (novo), `models.rotulo_status`, `app._render_search_diagnostics`, `app.render_step4` | **Planilha:** `error`+`parcial` → **"Parcial"**. **Tela:** seção laranja "Fontes parciais (parte da fonte respondeu, parte não pôde ser consultada)", métrica **"Parciais"** (agora são 6 colunas) e "· N parciais" no título do relatório. **Contagem:** `parciais_fonte` conta `parcial` mesmo sem erro; sem motivo, o aviso diz "coleta não terminou". **Parcial sem match:** `st.warning` no lugar de `st.info` "Tente ampliar…". Empty com parcial ganha a marca "(coleta parcial)" e uma legenda sem "com sucesso". | `'Indisponível' == 'Parcial'`; "Fontes indisponíveis" na tela; `st.error` "não puderam consultar" → `TestUX1ParcialNaoEIndisponivel` (5) verde |
| **S-N8** | `excel_export._write_diagnostico_tabela` | keyword e source vão **literais**: sem `redigir`, nem `token=***`, nem `'` na frente de `=`. A fórmula é neutralizada pelo tipo string. Saem só os caracteres de controle que o `.xlsx` não representa. | `'token=***' == 'token=abc'`; `("'=cmd", 's')` → `TestN8KeywordLiteralNoDiagnostico` (3) verde |
| **S-N9** | `app._resumo_da_busca(n, kw_statuses) -> (tipo, texto)`, usado no rótulo do `st.status` ao fim da busca e no topo do Passo 3 | **Vermelho** (`st.error`, `state="error"`) quando todas as buscas consultadas ficaram indisponíveis. **Amarelo** 📝 quando há indisponível ou parcial misturado. **Verde** só quando tudo respondeu. `nao_consultada` não conta como consultada nem como indisponível. | `assert not ElementList([Success()])`; `ImportError _resumo_da_busca` → `TestN9Passo3NaoDizConcluidaVerde` (3) verde |
| **S-MT2** | docstring de `models.rotulo_status` | Diz que é o único lugar do rótulo **da planilha** e que a tela agrupa por motivo, sem importá-lo. A explicação R2-B6 continua; a regra do Parcial foi acrescentada. | (texto) |
| review: caractere de controle | `excel_export._texto_xlsx(v) -> (str, n)`, `NOTA_CONTROLE`; `_write_data_row` passou a devolver um `int`; `_write_diagnostico_sheet(…, celulas_com_controle=0)` | `\x0b`/`\x0c` (quebra manual do Word / quebra de página) viram `\n`; os demais caracteres que o XML 1.0 não representa saem por `ILLEGAL_CHARACTERS_RE`. A troca vale para todo campo `str`, **antes** de `cell.value =`, e `_forcar_texto` continua sendo o último toque. A keyword e a source da aba de diagnóstico usam o mesmo contador. Com N > 0, o app grava **uma** linha abaixo da tabela de diagnóstico: "N célula(s) tinham caracteres de controle não representáveis em .xlsx: quebras manuais viraram quebra de linha, os demais foram removidos; o texto na fonte está no Link." A docstring explica por que isso **não** é paráfrase: nenhuma grafia desses caracteres cabe em XML 1.0, e nenhuma letra, dígito ou pontuação muda. | `IllegalCharacterError: xy / ab cannot be used in worksheets`; `ImportError _texto_xlsx` → `TestControleNaoDerrubaExportacao` (4) verde |
| review menor | `models.rotulo_status` | Chama `e_indisponivel(s)` em vez de repetir a regra. A tabela-verdade das 24 combinações (status × motivo × parcial) é idêntica à anterior (conferida por script). | (refatoração; golden inalterado) |

`test_phase4.py`: 76 → 90 (`624bed5`) → **94** (`f749360`). `BASELINE` foi atualizado no mesmo commit, com comentário.
**Golden: `planilha_sha256.txt` inalterado** (`c7a5dd57…`) e `dedup_esperado.json` intocado. A única linha do
`diagnostico_fixo.json` com `parcial` é `tcu ok+parcial`, que continua "OK". Nenhum valor da entrada fixa começa com `=` ou
tem caractere de controle, e nenhuma keyword do diagnóstico fixo tem cara de segredo. Por isso nenhuma célula hasheada mudou.

## 2. Desvios e decisões (📝 minhas, aceitas pelo reviewer)

1. 📝 **`models.e_indisponivel(s)`**: a regra "indisponível" (`error`, sem `nao_consultada`, sem `parcial`) fica num lugar só,
   usado pela planilha e pela tela. Isso antecipa uma parte de manut. 5, que a triagem tinha mandado para P3, porque o conserto
   UX1 mexia na regra em três lugares.
2. 📝 **Amarelo no Passo 3** para o caso misto. O brief só pedia que o caso "tudo indisponível" não ficasse verde.
3. 📝 **"Parcial" só para `error`+`parcial`**, como diz o brief. `ok`/`empty` parciais (paginação interrompida) continuam
   OK / Sem resultado, com "Sim" na coluna Parcial. Esse rótulo é fixado pelo golden.
4. 📝 Na seção vermelha, o `extra` "N resultado(s) do endpoint que respondeu" passou para a seção de parciais. Ali o
   resultado só aparece em `erro_interno` no meio do mapeamento, e por isso o texto agora diz "antes da falha".
5. O docstring `KeywordStatus.status` dizia que `error` significa "não pôde ser consultada". Foi corrigido para cobrir o
   `parcial` (regra verify-stale-docs).

## 3. Gates

### Implementador, `624bed5`
- **Ver falhar:** 11 failed, 3 passed. Os 3 que passaram são guardas: controle na keyword, empty sem parcial, busca saudável.
- **Depois:** `test_phase4.py` → `90 passed`.
- **Runner** (`timeout 900 python -u tools/run_all_tests.py`, foreground): 13 / 64 / 98 / **90** / 45 → **TUDO VERDE** (310).
- **Golden:** `golden-master OK`, sha inalterado.
- **Auditoria:** `git diff -U0 HEAD~1 -- '*.py' | grep '^-'`, lido inteiro. Cada explicação removida tem destino:
  - a docstring do relatório e o comentário R3 da keyword foram estendidos;
  - "(source/keyword sao redigidos…)" foi trocado pela afirmação corrigida;
  - a legenda "com sucesso" foi mantida no ramo sem parcial;
  - "do endpoint que respondeu" foi para a seção de parciais.

  `git grep` de `e_indisponivel` / `_resumo_da_busca` / `_forcar_texto`: todos os pontos de chamada conferem. `redigir`
  deixou de ser importado em `excel_export`, e ninguém o importava de lá.

### Implementador, `f749360`
- **Ver falhar:** 3 failed (`IllegalCharacterError` ×2, `ImportError _texto_xlsx`), 3 passed (guardas).
- **Depois:** `94 passed`; o doctest de `_texto_xlsx` passa.
- **Runner:** 13 / 64 / 98 / **94** / 45 → **TUDO VERDE** (314).
- **Golden:** `golden-master OK`, sha inalterado. Sem caractere de controle não há linha nova.
- **Auditoria:** as linhas removidas são as assinaturas que passaram a devolver `int`, o comentário "openpyxl recusa…"
  (estendido), a chamada do laço de linhas (agora `sum(...)`), o mapa de `rotulo_status` (agora via `e_indisponivel`) e o
  `BASELINE`.

### Testador (sobre `624bed5`), em `../execucao/revisoes/fix-saida.md`
- Runner 310, golden OK, CRLF.
- **S-SEC:** 7 payloads (`=cmd|…`, `=HYPERLINK(…)`, `+`, `-`, `@`, tab+`=`) em todo campo de texto, na keyword, na source e no
  tópico → `data_type 's'`, valor idêntico, sem `'`. **0 `<f>`** nas duas `sheet*.xml`. Não foi aberto em Excel nem em
  LibreOffice (não instalado).
- 18/18 cenários AppTest além dos meus.

### Gate visual V11 (`tools/dirigir_app.py`, porta 8501)
- **Implementador (`624bed5`):** 5 dos 6 checks obrigatórios passaram. **"origem no card" e "cards == N do cabeçalho"
  falharam por causa do dado ao vivo do dia**, não do código: a busca "LGPD / protecao de dados pessoais" trouxe **0
  normativos**. O LexML deu `bloqueio_waf`; os acórdãos do TCU vieram 200 (500 itens, 327 sem sumário), sem match; os atos
  do TCU deram 500; o Google veio vazio. Não há card para contar. A tela nova apareceu certa no screenshot:
  - aviso amarelo "Cobertura incompleta … lexml indisponível (bloqueio_waf); tcu respondeu parcialmente (0 resultado(s); http_5xx)";
  - erro vermelho só pelo LexML;
  - métrica Parciais = 2, com o TCU na seção laranja.
- **Testador:** V11 **7/7** (LGPD). Numa cópia com "turismo + licitacao", **33 cards == 33**, com a origem no card.
- ⚠ **Nota do Gemini:** as chaves de LLM (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `GEMINI_PAID_API_KEY`) estão **definidas
  no ambiente desta máquina**. A 1ª execução do V11 do testador **chamou o Gemini de verdade**. O implementador subiu o app
  com as variáveis vazias (`GEMINI_API_KEY= GOOGLE_API_KEY= OPENAI_API_KEY= GEMINI_PAID_API_KEY=`). A regra daqui em diante é
  subir todo app com `env -u GEMINI_API_KEY -u GOOGLE_API_KEY -u OPENAI_API_KEY …`. Registro de máquina: `~/.claude/ENVIRONMENT.md`.

## 4. Achados de teste e de review, e o destino de cada um

| achado | origem | destino |
|---|---|---|
| Caractere de controle (`\x0b`) em ementa/nome derrubava a exportação inteira (pré-existente) | testador (médio) + reviewer | **aplicado** em `f749360` (`_texto_xlsx` + `NOTA_CONTROLE`) |
| Docstring de `e_indisponivel` dizia que `rotulo_status` a usava, mas ela repetia a regra | reviewer (menor) | **aplicado** em `f749360` |
| Mutação: 11 dos 14 testes novos falham no código antigo; os 3 restantes são guardas | reviewer | registro (sem ação) |
| Os 3 desvios 📝 | reviewer | **aceitos** |
| S-SEC não foi aberto em Excel nem em LibreOffice reais | testador / reviewer | fica aberto: pela ECMA-376, célula `inlineStr` é texto; conferir quando houver Excel à mão |
| Tópico (título das duas abas) com caractere de controle ainda levantaria `IllegalCharacterError` | implementador (📝 observação) | fora do escopo; o tópico vem do campo do usuário, e um caractere de controle ali é improvável. Candidato a P3 |
| D-C17 (`_merge` troca o `nome`) | testador (caveat) | continua com o Rodrigo (🔴) |
