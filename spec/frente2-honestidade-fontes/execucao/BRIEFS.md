---
title: Frente 2 — briefs dos agentes (modelos reutilizáveis do orquestrador)
related: [CONTEXTO.md, TODOS.md]
---

# Briefs dos agentes

> Modelos que o orquestrador preenche (`{TASK}` número, `{ARQ}` arquivo da task, `{NN}`/`{slug}` = prefixo e nome
> desse arquivo, `{DIR}`, `{BRANCH}`, `{PORTA}`) ao despachar.
> Existem para sobreviver à compactação e para as trilhas receberem as mesmas regras.

## Regras comuns (vão em todo brief)

- Ler `spec/frente2-honestidade-fontes/reference/global-constraints.md`, depois `tasks/{ARQ}`, depois `CLAUDE.md`.
  O plano `docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md` é a fonte de verdade.
- Python via Bash (Git Bash), nunca PowerShell; `PYTHONIOENCODING=utf-8`; UTF-8 em todo `open()`.
- Nunca criar `levantamento-normativos/.streamlit/secrets.toml`; nenhum LLM de verdade; teste novo sem rede.
- Nunca tocar a branch `deploy`; não editar `spec/frente2-honestidade-fontes/execucao/*` nem `_TODO.md`.
- Trabalhar **só** em `{DIR}` (branch `{BRANCH}`). Não fazer push (o orquestrador faz).
- Contagem divergente do plano → parar e contar `def test_` do bloco antes de suspeitar do código; nunca ajustar BASELINE ao observado.
- ⚠ **Trilhas paralelas:** o total do runner soma as duas trilhas; vale o número **da suíte** que a task mexe.

## 1 · Coder A — implementar (`coder`)

Seguir os steps da task **literalmente e em ordem**, TDD como escrito (teste que falha → ver falhar → implementar →
ver passar). Blocos de código colados como estão; âncora = texto citado. Gates: runner TUDO VERDE (~9 min em 22/09, ~5 min em 23/09; rodar
em background e esperar), golden `comparar` OK (T8 recongela), os **2 comandos de auditoria** lidos inteiros.
Commit com a mensagem da task + `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
Reporta: SHA, saída de falha e de sucesso, resumo do runner, golden, auditoria, desvios. Guardar contexto: volta
com feedback de teste/review e para documentar.

## 2 · Coder B — testar (`coder`)

Não implementa a feature; testa o que o Coder A entregou em `{DIR}`:
1. Critérios de aceite do header da task, um por um, com comando + saída.
2. Suítes da task + runner inteiro + golden (independentes do que o Coder A relatou).
   Runner em **foreground** com `timeout 900 python -u tools/run_all_tests.py` (o runner leva ~9,5 min: 590s é curto demais) (em background travou uma vez, 23/09);
   não rodar o runner e o e2e ao mesmo tempo.
3. **E2E com Playwright** (Python, `p.chromium.launch(channel="chrome")` — navegadores do Playwright não estão
   baixados). Subir o app: em `{DIR}/levantamento-normativos/`, `env -u GEMINI_API_KEY -u GOOGLE_API_KEY -u OPENAI_API_KEY python -m streamlit run app.py
   --server.headless true --server.port {PORTA}` em background (⚠ as chaves de LLM estão DEFINIDAS no ambiente desta
   máquina — sem o `env -u` o app chama o Gemini de verdade; `~/.claude/ENVIRONMENT.md`, 23/09); dirigir: "Inserir palavras-chave manualmente" → keywords → "Proximo >>" →
   "Iniciar Busca" → esperar "Passo 4 - " → screenshot em `{DIR}/tests/evidencia/` (não versionar) e **olhar**.
   Afirmar: o app sobe, a busca chega ao Passo 4 sem traceback, e o comportamento observável da task (o que a task
   muda e for visível na tela/planilha exportada/log). Derrubar o app no fim.
4. Pode escrever scripts de teste descartáveis fora do repo (scratchpad); **não** commitar testes novos além dos do plano.
Veredito: APROVADO / REPROVADO, com evidência; defeito = arquivo:linha + reprodução.

## 3 · Code reviewer (`code-reviewer`)

Revisar o diff da task (`git -C {DIR} show <sha>` / `diff <base>..HEAD`) contra o arquivo da task, a spec
(`docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md`) e as Global Constraints. Checar: fidelidade
ao plano (nada pulado, nada "simplificado"), texto normativo nunca parafraseado, segredos redigidos, contratos e
call sites (`git grep` dos símbolos), documentação preservada (docstrings/comentários removidos têm destino),
testes afirmam o que dizem. **Não editar.** Saída: lista priorizada (bloqueador / importante / menor) com arquivo:linha
e a correção sugerida; "nada a corrigir" se for o caso.

## 4 · Coder A — aplicar review e documentar (SendMessage ao mesmo Coder A)

⚠ **Se o Coder A não existe mais** (sessão nova): despachar um coder novo com este brief + o arquivo
`execucao/revisoes/T{TASK}.md` (o orquestrador grava lá o veredito do testador e do reviewer assim que chegam).

Aplicar os achados aceitos (bloqueadores e importantes; menores com julgamento, justificando os rejeitados);
re-rodar suítes da task + golden (+ runner se tocou código); commit `fix(frente2): review da T{TASK} — ...`.
Depois documentar em `spec/frente2-honestidade-fontes/implementacao/{NN}-{slug}.md`: o que foi feito (arquivos,
símbolos), desvios do plano e por quê, comandos + saídas dos gates, achados de teste/review e o destino de cada
um, evidência e2e. Commit `docs(frente2): implementacao da T{TASK}`.
