# LESSONS — Buscador de Base Normativa

<!-- Append-only. Entradas mais recentes no topo. Formato: Problema / Causa-raiz / Conserto / Regra.
     Lição de MÁQUINA (vale em qualquer projeto) vai para ~/.claude/ENVIRONMENT.md, e aqui fica só
     um ponteiro de uma linha. Lição de ÁREA fica no runbook da área. Aqui: as transversais. -->

## 2026-10-06 · Porta 443 aberta não quer dizer que o HTTPS passa (servidor com whitelist)

**Problema.** No servidor do Nuati, a web aberta falhava (`ddgs`: 10054 e 10051), mas o `Test-NetConnection <host> -Port 443`
dava `True` para o DuckDuckGo, e o WinHTTP dizia "sem proxy". Parecia rede livre.
**Causa-raiz.** O srv-nuati02 filtra a saída por destino (whitelist, Rodrigo, 06/10): a conexão TCP abre e o filtro age depois,
no TLS (Python: conexão derrubada no handshake) ou na resposta (PowerShell: 403). Os 10051 vinham de outra coisa: o servidor
não tem IPv6, e o `ddgs` tenta IPv6 em alguns buscadores.
**Conserto.** Nenhum no app; decisão D-C32 e pedido à infra (B-13).
**Regra.** Para saber se um app sai para um destino, teste **o mesmo cliente que o app usa** (o Python do `.venv`, com
`requests.get(url)`), não só a porta. Antes de levar um app ao servidor, liste os destinos externos dele e teste cada um.
Cobertura: medido só no buscador; o checklist (porta 8401) não usa web aberta. Pedido 10 ao framework.

## 2026-10-06 · Editar Markdown por script Python: `\a` e `\b` em caminho do Windows viram caracteres de controle

**Problema.** Em edições feitas por `py - <<'EOF'` com o texto dentro de string Python, `E:\apps\buscador` virou
`E:<BEL>pps<BS>uscador` e `servidor_nuati\atualizar` perdeu o `\a`: invisível na leitura, quebra a cópia do comando.
**Causa-raiz.** Dentro de uma string Python comum, `\a` e `\b` são escapes (BEL, BS).
**Conserto.** Varredura de controle (`re.finditer(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', texto)`) nos `.md`; 6 trocados de volta
em 06/10 (state file, BLOCKED, log).
**Regra.** Texto com caminho do Windows vai por edição exata (ferramenta de edição) ou em string `r"..."`; depois de editar
por script, rode a varredura de caracteres de controle. Cobertura: só os `.md` da raiz e o comando de onboard foram varridos.

## 2026-10-01 · No servidor, o `secrets.toml` gravado pelo Notepad tinha BOM e o app subiu "sem LLM", sem avisar

**Problema.** Passe do servidor do Nuati: `instalar_tarefa.ps1` deu tudo `[OK]` (inclusive "configuracao encontrada"), mas a
barra lateral dizia "IA: nenhum provedor configurado". `tomllib` no `.venv` do servidor: `Invalid statement (at line 1,
column 1)`. Primeiros bytes: `EF BB BF`.
**Causa-raiz.** O Notepad daquele Windows grava "UTF-8 com BOM"; o TOML com BOM não é lido, e o `llm_cadeia` engole o erro do
`st.secrets` (de propósito: nunca levanta) e segue sem LLM. Editar de novo no Notepad devolveu o BOM. Faltava também o
`LLM_MODEL` (sem ele não há provedor `local`).
**Conserto.** Regravar sem BOM pelo .NET (`[IO.File]::ReadAllText(...).TrimStart([char]0xFEFF)` →
`WriteAllText(..., UTF8Encoding $false)`), validar com o Python do `.venv` (lista só os **nomes** preenchidos) e então
`atualizar.ps1`. ⚠ No PowerShell, `[IO.File]` resolve caminho relativo a partir de `system32`: use caminho absoluto.
**Regra.** Depois de criar ou editar a configuração no servidor, valide o TOML **antes** de reiniciar e confira a barra
lateral. Pedido ao framework: os scripts validarem o TOML.

## 2026-10-01 · O runner "sem LLM" chamava o LLM de verdade no PC do trabalho (e a linha de base parecia regressão)

**Problema.** Linha de base do passe por app (`master` @ `e22822e`, PC do trabalho): runner vermelho, cerca de 20 min.
`test_llm_phase3.py` 60/3 numa rodada e 59/4 na seguinte (`(0.5, 'modelo')` onde o teste esperava `heuristica`), levando
12-14 min; `test_phase4.py` 91 de 94 e `test_fontes_indisponiveis.py` 58/8.

**Causa-raiz.** Duas, sem relação com o código: (1) o `st.secrets` lê o `~/.streamlit/secrets.toml` **global** mesmo fora
do `streamlit run`, e vence a variável vazia que o runner passava: as suítes "sem LLM" chamavam o Gemma local e o Gemini;
(2) o Python deste PC não tinha `ddgs` (do `requirements.txt`) nem `markdown-it-py` (os 3 testes do Markdown são
`importorskip`, então "passam" pulando e o runner acusa só o encolhimento).

**Conserto.** (1) runner passa `LLM_SOMENTE=nenhum` (llm_cadeia 1.1.0; nenhum `secrets.toml` define esse nome, então o
ambiente vale e a cadeia nasce vazia): 65/65 em 3 s; runner inteiro em 6 min. (2) `py -m pip install ddgs markdown-it-py`.

**Regra.** Antes de chamar uma linha de base de "regressão", rode a suíte vermelha sozinha e leia a falha. Teste de "sem
LLM" se garante pelo ambiente que o código lê **primeiro**, não pela variável vazia. Contagem que varia entre rodadas = teste
dependendo de rede ou de LLM.

## 2026-10-01 · `git branch -d` recusa branch "não totalmente integrada" comparando com a HEAD, não com o remoto

**Problema.** Na limpeza, `git branch -d master llm-cadeia-1.0.1` recusou as duas, com a HEAD em `main` (= v1.0.1).
**Causa-raiz.** O `-d` confere contra a branch atual (e o upstream dela); as duas estavam dentro de `homologacao`, não de `main`.
**Regra.** Conferir antes com `git merge-base --is-ancestor <branch> <destino>` contra o destino certo e só então usar `-D`;
deixar uma tag nas pontas (aqui, `pre-framework-2026-10-01-*`).

## 2026-10-01 · O Gemma local devolve resposta vazia na categorização (raciocínio ligado)

**Problema.** Busca real no app local da `homologacao` (PC do trabalho, cadeia começando no `local`): palavras-chave e notas
de relevância vieram do `local (google/gemma-4)`, mas a categorização voltou **vazia** nos lotes 0 e 1 (log:
`Gemini returned empty response for categorize batch 0/1`, cerca de 5 min e 2 min). Pelo desenho do `llm_cadeia`, resposta
vazia **não** passa para o próximo provedor; a categoria cai no padrão do app.
**Causa-raiz.** 📝 Provável: o modelo gasta a saída raciocinando (mesma família da lição de 28/09); não isolado.
**Regra.** No servidor do Nuati, testar `LLM_DISABLE_THINKING=1` (medido 27,1 s → 3,8 s no framework em 29/09) antes de
dar o `local` como primeiro da cadeia. Pedido 2 ao framework.

## 2026-09-28 · Modelo que "pensa" devolve resposta VAZIA com orçamento de tokens pequeno — e o diagnóstico só viu porque chamou de verdade

**Problema.** O primeiro `python -m llm_cadeia` (1 chamada por modelo, `max_tokens=16`) mostrou `gemini-2.5-flash` e
`gemma-4-31b-it` com **resposta vazia**, sem erro. Os lotes de nota do buscador usam `max_tokens=512`: com esses modelos na
cadeia, a nota viraria `fallback_erro` em silêncio.

**Causa-raiz.** Modelos de raciocínio gastam o orçamento de saída pensando antes de escrever; com orçamento curto, o texto
final sai vazio. Medido em 28/09: `gemma-4-31b-it` com 16 tokens → `None`; com 512 e 4096 → `"ok"`.

**Conserto.** Piso de 4096 tokens também no transporte Gemini (`nucleo._gerar_gemini`), igual ao que o OpenAI-compatível já
tinha; teste que afirma o piso. Depois do piso, o mesmo diagnóstico deu `ok` nesses modelos.

**Regra.** Todo diagnóstico de modelo faz uma chamada **real** por modelo e trata "vazio" como achado, não como sucesso.
`max_tokens` é teto de custo, não tamanho da resposta: nunca abaixe para "economizar" em modelo que pensa.

**Cobertura.** ✅ `llm_cadeia` (os dois transportes). ⚠ As cópias do módulo em outros apps herdam o conserto só a partir da
1.0.0 que já o contém; app que chame LLM **fora** do módulo não está coberto.

## 2026-09-28 · Barra lateral do Streamlit roda antes do LLM: "Última resposta" ficava um passo atrasada

**Problema.** Adotando o `llm_cadeia` no `scopediagram`, a linha "Última resposta" de `painel_llm()` não aparecia depois
da geração: só na interação seguinte.

**Causa-raiz.** O Streamlit executa o script de cima para baixo; a barra lateral é desenhada antes do `gerar()`, então
lê o `ultimo` da execução anterior.

**Conserto.** `painel_llm()` desenha a linha num `st.empty()` e instala no contexto da sessão o gancho `ao_responder`,
que o `gerar` chama após cada resposta (erro no gancho é engolido: `gerar` nunca levanta).

**Regra.** Status que depende de algo calculado mais abaixo no script: placeholder + atualização, não `st.rerun()`.

**Cobertura.** ✅ `test_ao_responder_avisa_quem_respondeu_e_nunca_quebra_o_gerar`; ✅ ao vivo no app do scopediagram (28/09).

## 2026-09-25 · Estado de LLM em variável de módulo vaza entre usuários do Streamlit; cota do Gemini é por projeto E por modelo

**Problema.** Ao pôr um campo "use sua própria chave" no app, o caminho óbvio (acrescentar o provedor à lista global da
cadeia) faria a chave de um usuário servir **todos** os usuários do app: o Streamlit roda todas as sessões no mesmo
processo, e variável de módulo é compartilhada. O mesmo vale para "última resposta veio de X".

**Causa-raiz.** Módulo Python = singleton do processo; `st.session_state` = por sessão. O primeiro é para configuração
do app (Secrets), o segundo para o que o usuário digita.

**Conserto.** `llm/cadeia.py`: a chave do usuário vive no `st.session_state` e é instalada a cada execução via
`ContextVar` (`usar_contexto`); teste `test_chave_do_usuario_vai_na_frente_so_na_sessao_dela` prova que outro contexto
não a vê. Junto: a cota do Gemini é `PerProjectPerModel` (quotaId do 429; docs de rate-limits, 25/09) — rodar entre
modelos do mesmo projeto dá cota nova; segunda chave só soma cota se for **outro projeto**.

**Regra.** Em Streamlit, nada que o usuário digite vai para variável de módulo. E cota de API: conferir na doc/no 429
**qual é a unidade** (chave, projeto, modelo, organização) antes de desenhar o fallback.

**Cobertura.** ✅ `tests/test_cadeia_llm.py` (14). ⚠ Groq/Cerebras/OpenRouter não testados com chave real.

## 2026-09-23 · A faixa de auditoria do plano (`dc99d73..HEAD`) tem base sem nenhum `.py` — o comando de remoções dá vazio e "passa"

**Problema.** Na T10 da frente 2, o critério §7 manda rodar a auditoria de documentação sobre `dc99d73..HEAD`.
`git diff -U0 dc99d73..HEAD -- '*.py' | grep '^-' | grep -v '^---'` devolveu **0 linhas**. Parecia "nenhuma explicação
removida". Era vazio por construção: em `dc99d73` o repo **não tinha nenhum `.py`**, porque o código de A só chegou depois,
pelo merge `4f36080`. Todo `.py` da faixa aparece como arquivo novo, e arquivo novo não tem linha removida.

**Causa-raiz.** A faixa foi escolhida pela história dos **docs** (o commit das decisões de 22/09), não pela do código. Um
diff de dois pontos mede árvore contra árvore. Se a base não tem os arquivos, o gate não tem como reprovar.

**Conserto.** Rodei os dois comandos sobre a faixa que tem código dos dois lados: `1c063ea..HEAD`, o início da frente 2
(555 linhas removidas, lidas por arquivo, cada explicação com destino; ver `implementacao/10-fechar-frente.md`). Conferi
também `4f36080..1c063ea`: só as 3 linhas do `MODEL_NAME` antigo (`18ad975`), que têm destino.

**Regra.** Antes de acreditar num diff de auditoria vazio, confira que a **base** contém os arquivos auditados:
`git ls-tree -r --name-only <base> | grep '\.py$'`. É a mesma família da entrada de 22/09 sobre o gate rodado depois do
`git add`: um gate que compara contra o vazio dá verde.

**Cobertura.** ✅ Faixa refeita na T10 (`1c063ea..HEAD`, 555 linhas lidas). ⚠ Os gates de diff da frente 1 e das
tasks da frente 2 (`HEAD~1`) não foram reconferidos quanto à base — lá a base sempre tinha os `.py`, mas ninguém
checou com `git ls-tree`.

## 2026-09-23 · Revisão por task olha o diff da task; só a revisão do ESTADO INTEIRO vê o que as tasks juntas afirmam

**Problema.** Na frente 2, cada uma das 9 tasks passou por testador (com e2e) e por code-reviewer. Mesmo assim, as 5 revisões
finais sobre o estado combinado (`d4cab80`) acharam coisas que nenhuma revisão por task tinha visto:
- **(crítico de segurança)** a aba principal da planilha gravava texto de página web cru, e o texto virava fórmula;
- **(bloqueador)** o aviso "nenhuma fonte catalogada entregou" aparecia com o TCU entregando;
- o TCU parcial aparecia como "indisponível";
- a legenda do 0% era falsa por causa de acento;
- a janela de ~2 semanas do TCU não era dita em lugar nenhum.

**Causa-raiz.** Cada revisor lê o diff da sua task e confere contra o texto da task. Ninguém lê o que a tela e a planilha
**afirmam ao usuário** quando todas as tasks estão juntas. O gate visual V11 também não ajudava: ele pressupõe um cenário
fixo (TCU parcial de 22/09) e nunca exercita "LexML morto + TCU saudável".

**Conserto.** Revisão final com 5 lentes (spec, segurança, testes com mutação, manutenção com auditoria de docs, UX do app
real com Playwright) e triagem explícita: entra o que é segurança ou afirmação falsa (`execucao/revisoes/final-triagem.md`).
Os achados viraram duas trilhas de conserto (FIX-FONTES, FIX-SAÍDA), cada uma com o ciclo completo.

**Regra.** Nenhuma frente fecha só com revisões por task. Antes do fechamento, rode uma revisão do estado combinado, em
várias lentes, que inclua **o app real rodado por quem o usa** e uma pergunta direta: *"o que a tela e a planilha afirmam, e
é verdade?"*. Item deixado "fora do escopo" num plano (a fórmula na planilha estava assim) deve ser relido nessa revisão.

**Cobertura.** ✅ Aplicado na frente 2: 5 revisões finais + triagem + 2 trilhas de conserto antes da T10. ⚠ A revisão
final foi sobre `d4cab80`; o estado depois das trilhas de conserto (`51883f6`) teve só o ciclo das trilhas (teste +
review de cada uma) e o V11 da T10, não uma nova rodada de 5 lentes.

## 2026-09-23 · Identidade de registro se testa contra o VOLUME real, não contra a fixture

**Problema.** A T4 da frente 2 passou a montar o `id` do acórdão como `tipo|numero|data`. Os testes estavam verdes, e a
janela de 500 acórdãos que eles usavam tinha **0 colisões**. O testador buscou 3.200 acórdãos ao vivo e achou **212
colisões**: a 1ª e a 2ª Câmara têm séries de numeração próprias e fazem sessão no mesmo dia. O segundo acórdão
**sumia em silêncio**, e o dedup (`tipo_numero`) fundiria os dois também.

**Causa-raiz.** Unicidade é uma afirmação sobre **toda** a população. Duas fixtures reais e uma janela pequena mostram que
existem registros diferentes, mas não mostram que dois registros nunca terão o mesmo `id`.

**Conserto.** `bdd89a1`: o `numero` passou a seguir a forma de citação do TCU, com o colegiado literal. Resultado: 3.200 keys
= 3.200 ids = 3.200 depois do dedup. Efeito colateral honesto: a ementa real expôs a fusão fuzzy (🔴 D-C17).

**Regra.** Toda chave de identidade nova (id, chave de dedup, hash) é conferida contra uma amostra real **grande**, contando
`len(set(chaves)) == len(registros)`, antes de a task fechar. Fixture prova forma, não unicidade.

**Cobertura.** ✅ `id` do TCU (3.200 acórdãos ao vivo, T4). ⚠ `id` do LexML **sem** volume real: a fonte está atrás do
WAF (B-05); o do Google/DDG (URL normalizada) também não foi medido em volume.

## 2026-09-23 · Teste de "não vaza segredo" (e de qualquer proteção) só vale se for DEMONSTRADO falhando sem a proteção

**Problema.** Na T5 da frente 2, o teste "a chave do CSE não aparece no log" passava, mas não podia falhar. O ramo `conexao`
truncava a mensagem em 120 caracteres, e o segredo nunca chegava ao detalhe. Um mutante (`redigir` = identidade) também
passava.

**Causa-raiz.** O teste afirmava a **ausência** do segredo sem garantir que o segredo **chegaria** até ali sem a proteção.
Esse tipo de verde é vazio.

**Conserto.** `e70d9f6`: teste reescrito e provado com o mutante. O padrão virou prática da execução: o F-T1 da FIX-FONTES
foi provado por mutante, a revisão final matou 15/15 mutações da lógica de honestidade, e a revisão da FIX-SAÍDA conferiu
que 11 de 14 testes novos falham no código antigo (os 3 que passam são guardas declarados).

**Regra.** Todo teste de proteção (redação de segredo, escape, SSRF, fórmula) é rodado **uma vez contra a proteção
desligada** e tem de ficar vermelho. O registro da task diz qual mutante foi usado. Corolário das previsões do plano: um
teste-guarda, que protege comportamento que já existe, **passa** no "ver falhar". O plano deve prevê-lo como passed (T2:
15 failed + 1 passed, não 16 failed). É a mesma família da entrada de 22/09 (gate depois do `git add`: todo gate
precisa ser capaz de reprovar), aplicada a testes.

**Cobertura.** ✅ T5 (log do CSE), F-T1 (CQL), revisão final (15/15 mutações), FIX-SAÍDA (11/14). ⚠ Os testes
anteriores à frente 2 (`test_comprehensive`, `test_searchers`) não passaram por mutação.

## 2026-09-23 · Dar nome à procedência revela lixo que antes era só um número

**Problema.** A T6 da frente 2 passou a rotular de onde vem cada nota. Com isso apareceu um defeito antigo: `NaN`,
`Infinity` e `true` devolvidos pelo modelo saíam como nota **do modelo**, e `NaN` virava 1,0, a nota máxima. Na mesma
família: a legenda "0% = nenhuma palavra-chave na ementa" só se mostrou falsa (por causa de acento) quando a origem
"heurística" passou a aparecer na tela. E na T3 o "ok (N itens)" do TCU mostrava um N inflado, porque a API devolve 40
itens por página de 20.

**Causa-raiz.** Um número sem rótulo não afirma nada que se possa conferir. Quando ele ganha um rótulo ("veio do modelo",
"heurística", "500 itens"), vira uma afirmação testável, e a afirmação errada aparece.

**Conserto.** `6594cd8` (`fallback_erro` para não-número/`bool`/não-finito); `66b7145` (heurística sem acento, com a
normalização do filtro); `e8d59a4` (dedup por `key` na contagem).

**Regra.** Rotular a procedência é também uma auditoria. Ao dar nome à origem de um valor, teste o rótulo contra entradas
**hostis** (NaN, bool, acento, repetição) e não só contra o caso feliz.

**Cobertura.** ✅ `relevancia_origem` (T6, NaN/bool), heurística (F-UX2, acento), contagem do TCU (T3, repetição).
⚠ O rótulo "padrão da fonte" não foi testado contra entrada hostil (é constante do searcher).

## 2026-09-23 · Golden recongelado se prova RECONSTRUINDO o hash antigo a partir da saída nova

**Problema.** A T8 da frente 2 mudou a planilha, então o golden-master precisava ser recongelado. Conferir que o dedup não
mudou não prova que o recongelamento não escondeu uma regressão no resto da planilha.

**Causa-raiz.** O hash compara o todo, então recongelar aceita **qualquer** diferença — a esperada e as outras
juntas. Só a reconstrução separa uma da outra.

**Conserto.** O testador tirou a coluna nova da aba `Normativos` gerada pelo código novo e recalculou o hash. Deu **o sha
pré-T8 exato**. Assim a única diferença é a coluna declarada (`revisoes/T8.md`).

**Regra.** Todo recongelamento de golden vem com a prova de reconstrução: remova da saída nova o que a mudança acrescentou e
mostre que o hash antigo volta. Se não voltar, o recongelamento está escondendo alguma coisa.

**Cobertura.** ✅ T8 (`6178f9d`, sha pré-T8 reconstruído, `revisoes/T8.md`). A FIX-SAÍDA **não** recongelou: o sha
ficou inalterado (`c7a5dd57…`), conferido pelo testador e de novo na T10 (`golden_master.py comparar` OK).

## 2026-09-23 · As 3 lições que o plano da frente 2 mandou registrar na T10: onde estão

As lições (1) e (2) da Task 10 do plano **já estavam registradas desde 22/09**. Não as repito aqui (SSOT):
1. **"Fixture escrita à mão sobre esquema não capturado é falsa testemunha"**: está na entrada de 2026-09-22 abaixo. A
   execução confirmou: a fixture real do TCU sustentou a T4 inteira. O que ela não pegava (colisão de `id`), só o volume
   real pegou (entrada acima).
2. **"O pior achado foi um CRUZAMENTO de duas correções da rodada anterior"** (`redigir(300)` × cadeia agregada, R2-B1;
   `sem_texto` fora do try × `_texto_do_acordao` não-total, R3-B1; o plano só ficou executável na 4ª versão): está na
   entrada de 2026-09-22 abaixo.
3. **Falta a captura real de SRU do LexML**: continua aberta. `levantamento-normativos/tests/fixtures/lexml_sru_valido.xml`
   é 📝 escrita à mão, porque o LexML segue atrás do desafio de WAF do Senado (B-05; medido de novo no V11 da T10, 23/09).
   As pendências concretas (capturar; o cabeçalho do arquivo ainda sem a nota "escrita à mão") vivem só no `_TODO.md` P3
   (linha "(T10)" das sobras da execução).
   **Regra:** na primeira vez que o SRU responder XML (ou quando o B-05 der acesso), capture uma resposta real com o `curl`
   da entrada de 22/09, versione-a ao lado da escrita à mão e rode as suítes contra ela. Até lá, a fixture escrita à mão
   tem de dizer que é escrita à mão.

---

## 2026-09-22 · Modelo aposentado "só para usuários novos": o mesmo código funciona com chave velha e falha com chave nova

**Problema:** no app da nuvem, com chave Gemini nova (projeto `nuati.secin`), a IA não gerava nada; localmente, com a
chave antiga do ambiente, tudo "funcionava". **Causa raiz:** o Google retirou `gemini-2.5-flash-lite` **para usuários
novos** (404 `NOT_FOUND`), mantendo-o para os antigos. Mascarado por dois comportamentos do app: a chave é lida só no
import (primeiro sintoma: "IA nao disponivel" até o reboot) e `_generate` engole a exceção (segundo sintoma: "Nenhuma
palavra-chave gerada", sem motivo). **Conserto:** `MODEL_NAME = "gemini-3.5-flash-lite"` (sugerido pelo próprio 404,
provado com chamada real). Diagnóstico feito com script local que pede a chave via `getpass` e **tira
`GOOGLE_API_KEY`/`GEMINI_API_KEY` do ambiente** (esta máquina tem as duas globais; o SDK avisa e prefere
`GOOGLE_API_KEY`) — a chave nunca passou pelo chat nem por arquivo.
**Regra:** "funciona aqui" com credencial antiga não prova nada sobre credencial nova; testar com a credencial **do
ambiente de destino**. Erro de API engolido é a mesma doença que a frente 2 trata nas fontes.

## 2026-09-22 · Deploy em PaaS não deixa rastro no repo — "não existe deploy" exige olhar o painel

**Problema:** state file e D-C14 afirmavam "não existe deploy nenhum (sem Dockerfile/Procfile/streamlit.app)".
O Rodrigo achou `https://levantamento-normativos.streamlit.app/` rodando, privado.
**Causa raiz:** a verificação só procurou **arquivos** no repo. Streamlit Community Cloud (como Vercel, Render,
HF Spaces) só precisa de `requirements.txt` + `app.py`; o vínculo mora no painel do provedor, não no git.
**Conserto:** docs corrigidos com a prova (GET → `303` para o login do `share.streamlit.io`); B-06 item 4.
**Regra:** afirmar "não há deploy" exige checar a URL provável (`<nome-do-repo>.streamlit.app`) e/ou o painel,
não só o repo. Mesma família da lição de 16/09 (varredura que não cobre o lugar certo).

## 2026-09-22 · Duas rodadas seguidas: o pior achado foi um CRUZAMENTO de duas correções da rodada anterior

**Problema.** O plano da frente 2 passou por 3 rodadas adversariais (5 lentes, aplicando o plano num
worktree e rodando os testes que o próprio plano escreve). Na rodada 2, o bloqueador mais grave era o
cruzamento de **duas correções da rodada 1**: a H4 (`redigir(limite=300)` para não vazar chave de API)
cortava a cadeia agregada que a B2 acrescentou — o fato central da frente (LexML bloqueado por WAF)
**nunca chegaria à planilha**, e o teste passava porque o dublê usava URL de 16 chars. Na rodada 3, de
novo: a R2-H5 (contar acórdãos "sem texto") pôs a contagem **fora** do `try` que a H2 criou, e o
mapeamento não-total da T4 derrubava `search()` do TCU inteiro — com o próprio teste da T4. Nenhuma das
duas correções era errada sozinha.

**Causa-raiz.** Correções de uma rodada são escritas por lentes cegas entre si e dobradas no corpo
**sem que ninguém execute o plano inteiro** depois de dobrar. O cruzamento só aparece quando alguém
aplica tudo e roda. É a mesma lição de 16/09 ("uma emenda transforma em certeza o bug que a vizinha só
supunha"), agora **medida duas vezes mais** — e o plano só ficou executável na **4ª versão**.

**Conserto.** Rodada N+1 com a missão explícita de atacar as correções da rodada N, **aplicando o
plano literalmente num worktree e rodando os testes do plano**; parar quando os vereditos dizem
"executável" e sobram só achados localizados.

**Regra.** **Plano com código literal não está pronto enquanto uma rodada com contexto zero não o
aplicou e rodou.** Ler não pega cruzamento; só executar. E ao curar: cada correção nova é lida contra
**todas** as anteriores que tocam a mesma função — o custo é de minutos; o cruzamento custou uma rodada.

**Cobertura.** ✅ Aplicado ao plano da frente 2 (`02dc620`, v4). ⚠ **Não** reaplicado ao plano de 16/09
(Fase 1): as tasks T4/T7/T8 dele continuam com 3 seções de emendas não dobradas — e nenhuma rodada
aplicou aquele plano num worktree; é insumo da D-C9 quando a v2.0 começar.

---

## 2026-09-22 · Fixture escrita à mão sobre esquema não capturado é falsa testemunha — e escondeu um bug de produção

**Problema.** O plano v1 da frente 2 trazia uma fixture de acórdão do TCU com chaves `numeroAcordao`/
`anoAcordao`, escrita de memória. O código lia `numero`/`ano`/`ementa`. O teste de paginação falhava
(20 itens colapsavam num id) — e a investigação mostrou que **a API real** (`curl` em 22/09) tem
`numeroAcordao`, `anoAcordao`, `sumario`, `titulo` e **não tem** `ementa`/`numero`/`ano`. Ou seja: na v1.0
**todo acórdão real colapsa num único id e nunca casa palavra-chave**; o endpoint de atos em 500
escondia isso, e a fonte dizia "ok (500 itens)" entregando zero.

**Causa-raiz.** Fixture sem procedência: nem o teste nem o código tinham sido confrontados com uma
resposta real. Duas testemunhas falsas (código e fixture) que discordavam entre si — e foi a
discordância, não o acerto, que revelou o bug.

**Conserto.** Fixture **real** capturada e versionada (`levantamento-normativos/tests/fixtures/tcu_acordaos_real.json`,
2 itens); T4 do plano mapeia o esquema real; o detalhe conta "N sem sumário" porque a rodada 2 mediu
que acórdãos recentes chegam **sem** sumário (20/20 na sessão de 16/09).

**Regra.** **Fixture de API é captura, não redação.** Se a fonte está fora do ar e a captura é impossível
(caso do LexML hoje: `lexml_sru_valido.xml`, que a T2 do plano vai escrever à mão), a fixture leva `📝 escrita à mão, sem
captura` no cabeçalho, e capturar vira item pendente — não se apaga a nota quando o teste passa.

**Cobertura.** ✅ TCU: fixture real, capturada com
`curl "https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos?inicio=0&quantidade=2"`
(o HTML do desafio veio de `curl "https://www.lexml.gov.br/busca/SRU?operation=searchRetrieve&version=1.1&query=dc.title%3D%22licitacao%22&maximumRecords=2"`).
⚠ LexML: **sem captura real de SRU** (fonte bloqueada); registrado como pendência na T10 do plano → `_TODO` P3 (T10). Google/DDG: dublê de objeto, sem fixture — aceitável, a forma da
resposta é do pacote `ddgs`, não de uma API.

---

## 2026-09-22 · Um gate de auditoria rodado DEPOIS do `git add` compara contra o vazio e dá verde

**Problema.** Na T3, escrevi o `.gitignore` unido e rodei um script para provar que nenhuma
entrada de A ou de B tinha sumido. Ele imprimiu **"ausentes: NENHUMA"** — verde. Era falso: o
script lia os lados do conflito por `git show :2:` e `:3:`, e eu já tinha rodado `git add`, que
**apaga os estágios de conflito**. Os dois conjuntos vieram vazios, e `(vazio) - novo` é sempre
vazio. O gate não podia reprovar.

**Causa-raiz.** O script não checava o retorno do `git show`. Falha silenciosa virou prova.

**Conserto.** Reler os dois lados pelos **pais do merge** (`HEAD:.gitignore` e
`levantamento/main:.gitignore`), que existem antes e depois do `add`, e **afirmar** que a leitura
não voltou vazia (`assert rc == 0 and stdout.strip()`). Refeito, o gate achou o que o primeiro
escondeu: faltava `/*.xlsx`, entrada que as **três** rodadas adversariais não pegaram — a A18
repôs duas entradas e ninguém diffou a lista inteira.

**Regra.** **Todo gate de auditoria precisa ser capaz de reprovar — e isso tem de ser demonstrado,
não presumido.** Antes de acreditar num verde, pergunte de onde vieram os dois lados da
comparação e prove que não estão vazios. É a mesma família da emenda **A8** (o gate de docstrings
que casava 12 de 82 linhas e passava verde) e da **A19** (runner sem prova de que detecta falha).
Corolário prático: gate que lê estágio de conflito (`:2:`/`:3:`) roda **antes** do `git add`, ou
lê os pais.

---

## 2026-09-22 · As DUAS fontes catalogadas devolvem zero hoje — e a UI chama isso de "sem resultados", não de falha

**Problema.** Primeira execução do app v1.0 nesta sessão, dirigida ponta a ponta pelo navegador:
chegou ao Passo 4 em ~135s e mostrou *"Nenhum normativo encontrado"* com o relatório
**"0 OK, 0 erros, 4 sem resultados"**. Parecia consulta ruim. Não era: **as duas fontes
catalogadas estão quebradas hoje**, por motivos diferentes.

**Causa-raiz — medida, não inferida.**

1. **LexML está atrás de um desafio de WAF do Senado.** `GET` no SRU devolve **HTTP 200 com
   `content-type: text/html`** e `<title>Verificação de segurança — Senado Federal</title>`, não
   XML SRU. O parser cai em `LexML XML parse error: mismatched tag: line 50, column 2` — 29
   ocorrências no probe — e o searcher degrada para lista vazia.
   ⚠ **Os 3 URLs de fallback não ajudam:** `PRIMARY_SRU_URL` pega o desafio; `FALLBACK_SRU_URL`
   (`/sru/SRU`) e `FALLBACK_SRU_URL_2` (`/srw/SRU`) devolvem **404**. Os três estão no mesmo host
   `www.lexml.gov.br`, então uma proteção no host derruba a cadeia inteira.
2. **O endpoint de atos normativos do TCU devolve HTTP 500.** `atonormativo/recupera-atos-normativos`
   falha nas 3 tentativas com backoff. ⚠ Não é a API inteira: `acordao/recupera-acordaos` responde
   **200 `application/json` em 0,66s** na mesma bancada. É o recurso de *atos normativos* que está fora.
3. **Não é rede nem proxy daqui:** `curl` direto em `google.com` e no host do LexML volta 200 em
   ~0,35s.

**A parte que mais importa: o silêncio.** Erro de parse e 500 com 3 retries **não sobem para a
UI como erro**. O relatório diz "0 erros". Para uma ferramenta de pesquisa, **fonte bloqueada e
fonte sem nada a dizer viram a mesma tela** — e o usuário conclui que o tema não tem normativo.
É exatamente o risco que o requisito de cobertura do Rodrigo existe para impedir:
*"devemos conseguir pegar o máximo de coisas possível senão a ferramenta não será segura."*

**Conserto.** ⚠ *Retratado no mesmo dia, mais tarde:* virou a **frente 2 da v1.x** — spec + plano v4
(`docs/superpowers/{specs,plans}/2026-09-22-frente2-*`), ainda **não implementado**. A frente 1 (golden-master
+ runner) já existe. Continua insumo do **B-04**. ⚠ *retratado 23/09: implementada e fechada, T10 `074ed62`*.

**Regra.** **Degradação graciosa sem sinalização é perda de informação, não robustez.** Toda fonte
que falha por bloqueio, 5xx ou resposta não-parseável tem de aparecer na UI como **fonte
indisponível**, distinta de **fonte sem resultado**. E antes de aceitar "a busca não achou nada",
bater no endpoint com `curl` e olhar o `content-type`: HTTP 200 **não** significa que veio o que
se pediu.

**Cobertura.** ✅ Medido em 2026-09-22 contra LexML (3 URLs) e TCU (2 endpoints), por `curl` e
pelos searchers reais. ⚠ Google/DuckDuckGo: não medidos por mim; *retratado no mesmo dia:* o Rodrigo
rodou uma busca e a fonte "Google" (na prática DuckDuckGo — `GOOGLE_CSE_ID` vazio) **trouxe vários
normativos** — é a única via que entrega hoje. Achado posterior (rodada 1 do plano): a API real de
acórdãos do TCU não tem `ementa`/`numero`/`ano`, então o TCU estava cego **também** com o endpoint no ar.

---

## 2026-09-16 · Uma varredura que não cobre a pasta certa produz um "não existe" que custa um projeto inteiro

**Problema.** A spec de 08/09 declarou este projeto *greenfield*, afirmando que "o artefato
original não existe" e que o buscador "nunca foi código". Sobre essa base foram escritos uma
spec, um plano de 16 tasks e 19 emendas adversariais — **nenhuma linha de código**. O app existia
desde março de 2026, com 6.561 linhas e 205 testes verdes.

**Causa-raiz.** A varredura de 08/09 cobriu `solucoes/`, as skills e `projeto-AI-com-IA/`. Não
cobriu `~/Documents/projeto-nuati-normativos-levantamento/`. A conclusão foi registrada como
**fato** ("varredura esgotada"), não como "procurei em N lugares e não achei".

**Conserto.** Spec de consolidação de 16/09; correção com prova em `log.md`, na spec de 08/09 e no
state file; decisão B2 (FastAPI sobre Streamlit) revertida por ter nascido dessa premissa.

**Regra.** Afirmação **negativa** ("não existe", "nunca foi feito", "não há registro") é a mais
durável de todas, porque *procurar e não achar parece prova*. Ela **declara onde procurou** ou não
é escrita. Quando vier herdada de outro documento, **refazer a busca e citar o comando** — nunca
repetir por cópia.

**Cobertura.** ✅ **Medida em 2026-09-16, não estimada.** 20 arquivos superados carregam marcador
(`spec/buscador/**` = 18, mais a spec e o plano de 08/09), verificado por script que lista os
arquivos e confere marcador em cada um. As duas afirmações falsas dentro do `log.md` (append-only)
foram retratadas **inline**, ao lado de onde estão.
⚠ **Não varri** outros repos por afirmações negativas herdadas — não medido.

> ⚠ **Esta seção já esteve errada.** Na primeira redação ela dizia "✅ Aplicada aos 3 documentos" —
> e a spec de 08/09 **não tinha sido tocada**, seguindo a circular com a premissa falsa enquanto o
> onboard mandava lê-la. Pego pelo dogfood do próprio checkpoint. É a prova viva da regra da
> entrada seguinte: **escrever "verificado" exige rodar a verificação sobre o conjunto inteiro
> naquele momento, e citar o comando.**

---

## 2026-09-16 · O sha256 de um `.xlsx` não é determinístico: golden-master de planilha nasce morto

**Problema.** O golden-master da Fase 1 congelava `sha256(buffer.getvalue())` de um `.xlsx` gerado
por openpyxl. Duas execuções com **entrada idêntica** dão hashes diferentes — medido por três
revisores independentes, cada um com seu par de hashes.

**Causa-raiz.** `.xlsx` é um ZIP. O campo `date_time` de cada membro recebe o relógio do `save()`,
e `docProps/core.xml` embute `dcterms:created` e `dcterms:modified`.

**Conserto.** Hashear o **conteúdo**: `load_workbook(...)`, `iter_rows()`, `sha256(repr(linhas))`.
Verificado estável em 3 e em 2 execuções independentes.

**Regra.** Antes de usar hash de arquivo como prova de não-regressão, **rodar duas vezes e comparar**.
Formatos que embutem timestamp (`.xlsx`, `.docx`, `.zip`, `.pdf`) nunca servem crus. O risco pior
não é o falso vermelho: é o executor **apagar a prova** para destravar a task.

---

## 2026-09-16 · Uma emenda de revisão pode transformar em certeza o bug que a emenda vizinha só supunha

**Problema.** Na rodada 1 adversarial, a emenda **A5** consertou o runner que descartava exit code,
descrevendo como *hipótese*: "se essa linha levantar, a suíte sai ≠ 0 e o runner ainda imprime
TUDO VERDE". A emenda **A6**, da mesma rodada, mandava **trocar** a linha 14 do `test_llm_phase3.py`
— que é a única atribuição de `_original_key`, lida no fim do arquivo. Quatro revisores da rodada 2
executaram: `NameError`, exit 1, **depois** do resumo verde. A hipótese da A5 virou certeza.

**Causa-raiz.** Emendas de uma mesma rodada são escritas **em paralelo, por lentes cegas entre si**,
e a síntese as agrega sem simular a aplicação conjunta.

**Conserto.** B1: **acrescentar**, não substituir. Rodada 3 dirigida validou por execução.

**Regra.** **Rodada adversarial única é insuficiente quando as correções tocam código.** A rodada
seguinte tem como trabalho explícito atacar as correções da anterior. E preferir sempre
**acrescentar a substituir** ao editar linha de arquivo que não se leu inteiro.

**Cobertura.** ✅ As 3 emendas da rodada 2 que tocam código executável (B1, B2, B3) passaram por
rodada dirigida. ⚠ As emendas **só de texto** (B4-B12, C1-C5) **não** foram re-atacadas — julgado
desproporcional, e registrado aqui como limite conhecido.

---

## 2026-09-16 · Revisor não é juiz do próprio custo-benefício

**Problema.** Com trava de proporcionalidade explícita no prompt e campo obrigatório
`cost_benefit`, os revisores marcaram a esmagadora maioria dos próprios achados como "vale".

**Causa-raiz.** Quem encontra um bug raramente julga que consertá-lo não compensa. Pedir a
autoavaliação não cria o incentivo contrário.

**Conserto.** A filtragem real veio da **curadoria pelo orquestrador**: 39 → 21, 24 → 12, 6 → 5.

**Regra.** O campo de custo-benefício serve para **forçar o revisor a estimar o custo** — dado útil.
Não serve como filtro. O filtro é a curadoria, e ela não é opcional.

---

## 2026-09-16 · Um gate de preservação de documentação não vê arquivo que não foi tocado

**Problema.** O gate de auditoria usa `git diff <tag> HEAD -- '*.py' | grep '^-'`. A docstring de
`llm/__init__.py` — **ponto de entrada público do pacote** — passaria a mentir sem o arquivo ser
modificado, então **não apareceria no diff**.

**Causa-raiz.** Gate baseado em diff só enxerga o que mudou. Documentação que envelhece por mudança
**alheia** é invisível a ele por construção.

**Conserto.** `llm/__init__.py` entrou nos Files da Task 6; a limitação do gate ficou registrada na
emenda B7.

**Regra.** Todo gate baseado em diff **declara o que não consegue ver**. Doc que mente sem ser
tocada exige varredura própria, por vizinhança (o pacote, a pasta), não por diff.

---

## Ponteiros

- Lições de **máquina** (valem em qualquer projeto desta máquina): `~/.claude/ENVIRONMENT.md`.
  Registradas por este projeto: (1) o endpoint LLM `10.10.111.125:1234` só responde de dentro da
  rede da Câmara, com a regra do `timeout` em tupla; (2) criar repositório no GitHub exige o `gh`
  CLI — o token do Credential Manager que faz o `push` não autoriza a chamada de API.
  (3) `sed -i` do Git Bash em arquivo CRLF converte para LF e pode não aplicar a edição; (4) duração absurda de suíte ou
  de agente = a máquina suspendeu (`time.monotonic` avança na suspensão) — as duas registradas em 23/09.
  (5) as chaves `GEMINI_API_KEY`/`GOOGLE_API_KEY`/`OPENAI_API_KEY` estão DEFINIDAS no ambiente da máquina — app lançado
  à mão sem `env -u …` chama o Gemini de verdade (23/09).
  (6) `grep -F` do Git Bash dá falso negativo em padrão com emoji no locale UTF-8 — prova de sobrevivência de texto
  com `LC_ALL=C` ou Python (23/09, review da T10).
- Regra de adiamento dentro de uma frente executada por agentes: achado "adiado → Tn" entra na hora nos **itens
  carregados** (`spec/frente2-honestidade-fontes/execucao/CONTEXTO.md`, seção "Itens carregados entre tasks", e o
  brief em `execucao/BRIEFS.md`); adiado para fora da frente → `_TODO.md` P3 ou a frente-alvo.
- Bloqueios que dependem do humano: `BLOCKED-ON-RODRIGO.md`.
- Decisões: `_DECISOES-PENDENTES.md` e `decisions/DECISIONS-LOG.md`.
