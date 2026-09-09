# Log — Buscador de Base Normativa

<!-- entradas mais recentes no topo · formato: ## [data] operação | título -->

## [2026-09-08] scaffold | Brainstorm, spec e plano de 16 tasks — projeto nasce

Sessão de origem: área `ai-com-ia` do `projetos-nuati`, durante a ingestão dos Relatórios de
Situação. O Rodrigo pediu "a aplicação completa" do buscador de base normativa citado de
memória em 23/08.

**Varredura que precedeu o desenho (e mudou o projeto).** Procurei o artefato original em
`solucoes/` (6 repos), nas skills e comandos do `projetos-nuati`, e na pasta do
`projeto-AI-com-IA`. **Não existe.** O candidato `/analise-normativa` foi lido por inteiro
(154 linhas) e **descartado**: é gerador/auditor de checklists (modos `extrair`, `verificar`,
`instanciar`), a montante do `checklist-conformidade`, sem nenhuma função de busca. O que
existe em `referencias/_apendices-e-scripts/` é só um **formatador**:
`gerar_planilha_normativos.py` tem uma lista de ~30 normativos escrita à mão dentro do fonte
e **nenhuma chamada de rede** (sem `requests`, `urllib`, `selenium`, `playwright`). Ou seja,
dos passos do processo — tema → palavras-chave → busca → planilha → download → pastas — só o
"planilha" era código. O resto era conversa com LLM.

**Um alerta meu que se mostrou errado, registrado por honestidade.** Levantei que o projeto
duplicaria o `wiki-chat` (que tem chunker, retriever e citações planejados). O Rodrigo
corrigiu: o wiki-chat **consome** acervo, este **constrói**. Alerta retirado.

**A dor que define o produto:** a primeira busca do levantamento LGPD trouxe **100+
normativos**, "inviável de usar por um humano". O problema não é buscar, é **triar** — daí o
princípio de reduzir o *número* de decisões, não embelezar cada uma (spec §2, mecanismos
M1-M4).

**Decisões B1-B5** tomadas no brainstorm (detalhe na spec §4 e no
`_DECISOES-PENDENTES.md`), com duas tensões explicitamente aceitas pelo Rodrigo e suas
mitigações obrigatórias: B4 (duplicação entre temas → dedup sha256) e B5 (inflação de
decisões → ações de grupo).

**Entregas:** spec de design + plano de implementação de 16 tasks com TDD passo a passo.
**Nenhuma linha de código.**

---
