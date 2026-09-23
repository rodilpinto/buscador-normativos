# FIX-SAÍDA — vereditos (worktree `../bn-fix-saida`, branch `frente2/fix-saida`, commit `624bed5`)

## Implementação (coder A) — `624bed5` (23/09)
S-SEC (`_forcar_texto`: `data_type="s"` em toda célula de texto, nas duas abas; XML com `inlineStr`, sem `<f>`); S-N1
(`todas_mortas`); S-UX1+N3 (`rotulo_status` → "Parcial" para `error`+`parcial`; seção laranja "Fontes parciais" + métrica;
parcial sem match → `st.warning`, sem "com sucesso"); S-N8 (keyword/source literais; só `ILLEGAL_CHARACTERS_RE`); S-N9
(`_resumo_da_busca` verde/amarelo/vermelho); S-MT2 (docstring). test_phase4 90 (+14), runner 310, **golden sha inalterado**.
Desvios 📝: `models.e_indisponivel(s)`; amarelo no Passo 3 para indisponível/parcial misto; "Parcial" só em `error`+`parcial`.

## Testador (coder B) — ✅ APROVADO, sem defeito no escopo (23/09)
- Runner 310, golden OK (sha `c7a5dd57…`), CRLF.
- **S-SEC:** 7 payloads (`=cmd|…`, `=HYPERLINK(…)`, `+`, `-`, `@`, tab+`=`) em todo campo de texto + keyword/source/tópico →
  `data_type 's'`, valor idêntico, sem `'`; **0 `<f>` nas duas `sheet*.xml`** (82 + 65 `inlineStr`). Não aberto em Excel/
  LibreOffice (LibreOffice não instalado).
- 18/18 cenários AppTest além dos do coder (N1 com controle; Parcial na tela e na aba; N3; Passo 3 nas 4 combinações; N8).
- **Pré-existente, médio (📝 severidade do testador):** caractere de controle (``, quebra manual do Word — plausível no
  `sumario` do TCU) em `ementa`/`nome` faz a **exportação inteira falhar** com "Erro ao gerar Excel" (`app.py:1409-1411`
  captura; nada corrompe).
- E2E: V11 OK 7/7 (LGPD) e, na cópia com "turismo + licitacao", **33 cards == 33** com a origem no card. ⚠ A 1ª execução
  do V11 **chamou o Gemini de verdade**: as chaves de LLM estão definidas no ambiente da máquina → `ENVIRONMENT.md`; a cópia
  rodou com as chaves limpas (0 chamadas). Caveat D-C17 registrado.

## Reviewer — (pendente)
