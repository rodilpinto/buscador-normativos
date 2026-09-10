# Log — Buscador de Base Normativa

<!-- entradas mais recentes no topo · formato: ## [data] operação | título -->

## [2026-09-10] split | 16 tasks extraídas em arquivos, agrupadas em 5 ondas e 7 trilhas

Fase `split` do `/go`. O plano tem **2641 linhas**: um agente de build que o lesse inteiro a
cada task gastaria em leitura o contexto de que precisa para implementar. As 16 tasks foram
cortadas **verbatim** (não reescritas) para `spec/buscador/tasks/NN-nome.md`, de 122 a 255
linhas cada, e o material transversal (Global Constraints + File Structure + Tech Stack) foi
para `spec/buscador/reference/global-constraints.md`, citado pelos headers.

**O plano segue fonte de verdade do conteúdo.** Divergência entre plano e cópia: o plano ganha.
Status por task continua só no `_TODO.md`; ordenamento em `spec/buscador/00-overview.md`.

**Ondas e trilhas.** 5 ondas. A onda 2 tem 4 trilhas paralelas (A dados, B fontes, C llm,
D triagem-core) com **interseção de arquivos vazia**, verificada listando os arquivos tocados
por trilha e comparando, não por julgamento. A T3 foi puxada para o gate junto com a T1 porque
`Resultado` e `normalizar_titulo` são consumidos por 3 das 4 trilhas.

**Duas colisões reais encontradas, ambas serializadas:**
- `buscador/web/app.py`: T14 cria, T15 modifica. Mesma trilha, nesta ordem, nunca em paralelo.
- `README.md`: T1 e T16 listam as duas como "Create". Ondas distintas, mas a T16 sobrescreve.
  **Ambiguidade do plano, não resolvida** (registrada no overview e no `_TODO.md` P3).

**Verificação da extração** (feita por quem não extraiu): cobertura contígua das linhas
53-2641 do plano sem buraco nem sobreposição, cercas de código pares em todos os 16 arquivos,
nenhum truncamento, nenhum acento corrompido.

**Lição de ambiente:** `python` nu não resolve nesta máquina (o alias do Microsoft Store
intercepta e imprime instrução de instalação). Usar o caminho completo do plano,
`C:\Users\P_8106\AppData\Local\Programs\Python\Python313\python.exe`, ou Bash puro.

Nenhuma linha de código de produção foi escrita nesta fase.

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
