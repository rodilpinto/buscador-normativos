# Buscador de Base Normativa — Implementation Plan

> # ⛔ PLANO SUPERADO — NÃO EXECUTE
>
> Este plano de 16 tasks foi **superado em 2026-09-16** pela consolidação. Ele nasceu da premissa
> falsa de que o projeto era greenfield (ver a retratação na spec de 08/09).
>
> 👉 **Plano vigente:** `2026-09-16-consolidacao-fase1.md`.
>
> Fica no repo como histórico e porque suas emendas R1-xx continuam citadas pelo plano vigente.
> ⚠ **Atenção ao namespace:** os identificadores `R1-01`…`R1-19` **deste** arquivo são as emendas
> de 2026-09-11 e **não** têm relação com os achados brutos numerados na revisão de 16/09.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir um app web local que, a partir de um tema, pesquisa normativos em fontes catalogadas e na web aberta, e entrega uma lista **triável em poucas decisões humanas**, baixando e organizando só o que sobrevive à triagem.

**Architecture:** Pipeline de 6 etapas com estado em SQLite, o que torna cada etapa retomável. Adaptadores de fonte isolados atrás de um protocolo comum, cada um com fixture HTML salva e teste de contrato. O LLM é opcional atrás de um protocolo: com `NullLLM` o sistema roda inteiro. A interface web é FastAPI + Jinja2 + JS puro, sem framework de frontend.

**Tech Stack:** Python 3.13 · FastAPI · Jinja2 · sqlite3 (stdlib) · httpx · selectolax · openpyxl · pytest

**Spec:** `docs/superpowers/specs/2026-09-08-buscador-normativos-design.md`

## Emendas da Rodada 1 (revisão adversarial) — VINCULANTES, prevalecem sobre o corpo

> **Data:** 2026-09-11 · **Método:** 5 revisores independentes e cegos entre si (contrato entre
> tasks · dados/API · risco de domínio · construtibilidade · determinismo e teste).
> **Regra de precedência:** onde uma emenda contradiz o texto original de uma task, **a emenda
> vence**. Nenhuma task pode ser marcada como feita sem cumprir a emenda que a cita.
>
> **Procedência dos achados:** ✅ = comportamento verificado por leitura do texto do plano, por
> execução de comando ou por consulta à página real. 📝 = recomendação de desenho, não verificada.
> ⚠ **Os números de linha citados nas emendas referem-se ao plano ANTES desta inserção.**
> Esta seção acrescentou ~300 linhas ao topo do arquivo: para localizar qualquer trecho citado,
> use `grep -n` pelo identificador (nome de função, string do teste), não o número literal.
>
> Os itens marcados **[confirmado na síntese]** foram re-verificados pelo orquestrador, não só
> pelo revisor que os levantou. **[convergente]** = levantado por 2 ou mais revisores cegos.

---

### BLOQUEADORES (nenhuma linha de código antes de resolver)

**R1-01 · O grafo de ondas está errado: T12 e T13 dependem da T11.** ✅ [confirmado na síntese] [convergente: lentes 1 e 4]
`tests/test_download.py` (linha 1719) e `tests/test_planilha.py` (linha 1927) fazem
`from buscador.busca import executar_busca`, que é a T11. A T13 estava agendada na **onda 2**
e a T12 declarada **paralela à T11** na onda 3. As duas falhariam em `ModuleNotFoundError` no
slot agendado. A checagem de colisão do `00-overview.md` comparou **arquivos tocados** e não
**imports**, então não podia ver isso.
**Emenda vinculante:** a onda 3 passa a ser **T11 sozinha**; T12 e T13 vêm **depois** da T11.
A afirmação "T11 ∥ T12" fica **revogada**. O `00-overview.md` e o `_TODO.md` devem ser
corrigidos antes de qualquer build.
📝 Alternativa que restauraria o paralelismo, se o implementador preferir: reescrever as duas
fixtures para semear o banco por SQL cru (como `tests/test_db.py` já faz) em vez de chamar o
orquestrador. Tem a vantagem de fazer cada teste testar a própria unidade. Não é obrigatória.
**Regra nova, permanente:** toda checagem de colisão de trilha passa a comparar **arquivos
tocados E imports entre tasks**.

**R1-02 · Nenhuma task do plano instala nada.** ✅ [confirmado na síntese]
`pip install` aparece uma única vez em 2641 linhas, na **linha 2554**, dentro do *texto* do
README que a T16 grava em disco. Nunca é executado. As ~32 instruções `py -m pytest` das 16
tasks rodam contra o Python global. Verificado ao vivo pelo revisor: repetindo os Steps 1-3 da
T1 nesta máquina, o comando falha com `No module named pytest`, **não** com o
`ModuleNotFoundError: No module named 'buscador.config'` que o plano promete. A primeira
instrução executável do plano já falha pelo motivo errado, o que quebra o ciclo TDD logo no
primeiro passo: o agente vê vermelho, mas não o vermelho que deveria ver.
**Emenda vinculante:** a T1 ganha um **Step 0** que cria o venv e instala:
`python -m venv .venv` e `.venv/Scripts/python -m pip install -e ".[dev]"`. Toda instrução
`Run:` das 16 tasks passa a usar `.venv/Scripts/python -m pytest`.
📝 Recomendado junto: declarar `[build-system]` no `pyproject.toml`. O revisor verificou que
`pip install -e .` funciona sem ele (setuptools implícito), então não é bloqueador.

**R1-03 · `normalizar_url` falha o próprio teste da T3.** ✅ [confirmado na síntese]
Teste (linha 373): `normalizar_url("https://X.gov.br/Lei.htm?a=1#topo") == "https://x.gov.br/lei.htm"`.
Implementação (linhas 412-415): minusculiza `p.scheme` e `p.netloc`, **nunca o path**. Devolve
`https://x.gov.br/Lei.htm`. A T3 está no **gate da onda 1** e três das quatro trilhas da onda 2
dependem dela.
**Emenda vinculante:** minusculizar o path em `normalizar_url`.
**Trava de rastreabilidade, obrigatória junto:** a URL normalizada serve **apenas** para
`chave_dedup`. O campo `Resultado.url` guarda a URL original, literal, sem nenhuma
transformação (spec §6, item 3). Acrescentar teste que prove que `url` não é sobrescrita pela
forma normalizada.

**R1-04 · `chave_dedup` descarta a query string e perde normativo em silêncio.** ✅ [lente 2]
`normalizar_url` passa `""` como query em `urlunsplit`. Legin e TCU identificam documentos
distintos por id na query (`?idAto=152` vs `?idAto=153`). Dois normativos **diferentes**
colapsam na mesma chave, e `unicos.setdefault(r.chave_dedup, r)` (linha ~1662) mantém só o
primeiro, **sem aviso, sem log, sem relatório**. É perda silenciosa de acervo, o inverso exato
da mitigação "nunca duplicação silenciosa" da B4.
**Emenda vinculante:** (a) preservar a query string na chave quando o path sozinho não
discrimina, descartando apenas parâmetros sabidamente de ruído (sessão, rastreamento); e
(b) **todo colapso de dedup vira registro**: o que foi fundido com o quê, visível ao humano.
Dedup silencioso é proibido nas duas direções.

**R1-05 · As duas travas anti-ancoragem colidem e a ordem escolhida viola a constraint do plano.** ✅ [confirmado na síntese] [lente 5]
Em `premarcacao.py` o `if r.vinculacao == "obrigatorio"` retorna **antes** do teste de
`procedencia == "web-aberta"`. Logo um item `obrigatorio` vindo da **web aberta** nasce `fica`,
contra a **linha 21** deste plano ("Web aberta nunca é pré-marcada `fica`"). A docstring da
task diz "A ordem das regras É a especificação", isto é, o plano eleva a especificação uma
ordem que contradiz sua própria constraint. Hoje o caso é inalcançável só porque
`FonteWebAberta` fixa `vinculacao_padrao="contexto"`: é **acidente de implementação, não
garantia**. Nenhum teste cobre a combinação.
**Emenda vinculante:** escrever a precedência de forma explícita e testada. A regra é:
**procedência vence vinculação**. Nada de web aberta nasce `fica`, qualquer que seja a
vinculação; `obrigatorio` de fonte catalogada nunca nasce `sai`. Acrescentar
`test_obrigatorio_de_web_aberta_nao_nasce_fica` e uma invariante de dados que impeça a
construção de um `Resultado` com `procedencia="web-aberta"` e `vinculacao="obrigatorio"` sem
passar por revisão humana.

**R1-06 · As ações de grupo furam a trava anti-ancoragem, e o servidor não a reafirma.** ✅ [confirmado na síntese] [lente 3]
O template nem renderiza `data-vinculacao` (linha 2235 traz só `data-ja-tenho` e
`data-procedencia`). `desmarcar-todos` (linha 2264) desmarca tudo sem olhar vinculação;
`desmarcar-ja-tenho` (linha 2265), que é **a mitigação obrigatória da B5**, desmarca qualquer
item com selo, inclusive um `obrigatorio`. A rota `gravar` (linha 2172) faz
`UPDATE resultados SET decisao='sai'` na busca inteira e reaplica `fica` só ao que veio no POST,
**sem nenhuma validação**. Resultado: uma norma juridicamente obrigatória sai do acervo de
critério com um clique, sem aviso e sem registro de divergência. A trava da spec §7 existe só
em `premarcacao.py` e não sobrevive à camada de interação.
**Emenda vinculante:** (a) renderizar `data-vinculacao` em cada item; (b) toda ação de grupo
**pula** itens `obrigatorio` e mostra quantos poupou; (c) a rota `gravar` **valida no servidor**:
mudar um `obrigatorio` para `sai` exige confirmação explícita e separada, e grava o motivo da
divergência; (d) teste de contrato para cada uma das quatro ações de grupo provando que o item
`obrigatorio` sobrevive.

**R1-07 · O relatório de duplicata da B4 é calculado e jogado fora.** ✅ [lente 3]
`baixar_selecionados` devolve `RelatorioDownload(baixados, duplicatas, erros)`, e a rota
`aplicar` (linha 2391) **descarta o retorno**. Não grava, não loga, não renderiza. `COLUNAS`
da planilha (linha 1986) não tem coluna de duplicata nem de caminho do arquivo, e a consulta
traz `a.sha256` mas nunca `a.caminho`. A **detecção** existe; o **relatório**, que é a peça
textualmente exigida pela decisão B4 como mitigação obrigatória, nunca chega ao humano.
**Emenda vinculante:** persistir o `RelatorioDownload`, renderizá-lo após o "aplicar", e
acrescentar à planilha as colunas "Duplicata de outro tema" e "Caminho do arquivo".

**R1-08 · O selo já-tenho (M1) casa por título, não por sha256, e a File Structure promete sha256.** ✅ [lente 5]
A linha 42 da File Structure diz "Índice **sha256** do acervo existente". `indexar()` mapeia
`normalizar_titulo(stem do arquivo) -> caminho` e `marcar_ja_tenho` compara títulos
normalizados. `sha256_arquivo` é implementado e testado, mas **nunca chamado** nesse caminho.
Consequência traçada com nomenclatura real: acervo tem `LGPD.pdf` (chave `lgpd`), resultado vem
como "LEI Nº 13.709, DE 14 DE AGOSTO DE 2018" (chave `lei n 13 709 de 14 de agosto de 2018`).
**Não casa.** O M1, que é o mecanismo central de redução de decisões, não dispara justamente na
variação de nomenclatura mais comum do direito brasileiro. No sentido inverso, dois normativos
homônimos de anos ou órgãos diferentes ("Instrução Normativa nº 1") colapsam na mesma chave e
produzem um "já tenho" **falso**, que pré-marca `sai` um documento que o órgão não tem.
**Emenda vinculante:** (a) casar por sha256 onde houver arquivo; (b) o casamento por título
vira **sinal fraco**, exibido ao humano como "possível duplicata, não confirmada", e **nunca**
dirige sozinho uma pré-marcação `sai`; (c) testes com as três formas reais: "Lei nº 13.709, de
14 de agosto de 2018", "Lei 13.709/2018", "LGPD".

**R1-09 · O dedup por sha256 não cobre o acervo que já existia.** ✅ [lente 5] [convergente com R1-07]
`baixar_selecionados` compara o sha256 novo contra a tabela `arquivos`, que só é populada por
downloads feitos **pela própria ferramenta**. Os arquivos que o órgão já tinha, colocados à mão,
nunca entram lá. Ou seja: a mitigação obrigatória da B4 não cobre exatamente a população de
arquivos que motivou o projeto.
**Emenda vinculante:** antes do primeiro download, popular `arquivos` com o sha256 de todo
arquivo sob `acervo_raizes`, usando o `sha256_arquivo` que hoje é código morto. Teste: semear um
arquivo num acervo fora de `raiz_dados`, baixar bytes idênticos e provar que é reportado como
duplicata.

**R1-10 · Duas das três rotas catalogadas retornam 404 hoje, e a do TCU pode ser SPA.** ✅ [lente 2, verificado contra a web]
`www2.camara.leg.br/legin/busca?termo=` → **404**. `portal.tcu.gov.br/busca?q=` → **404**.
A busca real do TCU fica em `pesquisa.apps.tcu.gov.br/#/pesquisa/integrada`, com roteamento por
hash, assinatura de aplicação renderizada em JavaScript. **Se confirmado, `httpx` + `selectolax`
não conseguem raspar aquilo, e isso é mudança de arquitetura, não ajuste de seletor.** O TCU
publica API de dados abertos (`dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos`) que
o plano não menciona. A rota do Planalto **não foi confirmada** (erro de conexão no teste): é
lacuna real, não aprovação.
**Emenda vinculante:** antes de escrever T5 e T6, baixar a página real de cada fonte, confirmar
rota e seletor, e **substituir a fixture sintética pela página real**. Para o TCU, decidir entre
API de dados abertos e scraping **antes** de implementar. Isto resolve a **D-B2**, que sai de
"suposição" para "duas rotas comprovadamente erradas".

**R1-11 · Falta a coluna "Dimensão TCU", exigida pelo critério de sucesso nº 4 da spec.** ✅ [confirmado na síntese] [lente 2]
A spec (§8, critério 4, linha 120) lista 11 colunas do projeto, entre elas **Dimensão TCU**.
`COLUNAS` da T13 tem 17 entradas, mas nenhuma é essa, e não existe campo correspondente no
schema da T2 nem no `Resultado` da T3. O plano entrega 10 das 11 colunas originais e acrescenta
uma "Pré-marcação" não pedida, fechando 17 por coincidência aritmética.
**Emenda vinculante:** acrescentar `dimensao_tcu` ao schema (T2), ao `Resultado` (T3), ao
adaptador que consegue preenchê-la (no mínimo `FonteTCU`) e a `COLUNAS` (T13).

---

### ALTOS (corrigir antes da task correspondente, não antes de tudo)

**R1-12 · `caminho_longo()` é chamado em um único lugar, contra a constraint do próprio plano.** ✅ [confirmado na síntese] [convergente: lentes 3 e 5]
A linha 17 afirma: "**toda** operação de arquivo usa o helper". Ele é definido na linha 1818 e
usado **só** na linha 1877, no `open()` do download. Ficam desprotegidos: `indexar()` e
`sha256_arquivo()` da T9 (varrem o acervo, que mora sob `~/Documents/projetos-nuati/...`, prefixo
já longo) e o `mkdir`/`save` de `gerar_planilha` na T13. Acima de 260 chars a falha é
**silenciosa**: arquivo do acervo some do índice sem erro, planilha não é gravada e a rota
`aplicar` ainda responde 303.
Erro de documentação junto: a linha 17 diz que o helper é "da Task 13"; ele é da **Task 12**.
**Emenda vinculante:** mover `caminho_longo()` para um módulo compartilhado (T1 ou T2) e
aplicá-lo em **toda** leitura e escrita que toque `raiz_dados` ou `acervo_raizes`. Teste com
caminho real acima de 260 chars para T9 e T13.

**R1-13 · Nenhum rate limit, nenhum User-Agent, nenhum backoff.** ✅ [convergente: lentes 2 e 3]
Busca por `user-agent|rate.limit|backoff|sleep|throttle|robots` nas 2641 linhas: **zero
ocorrências**. Os três adaptadores fazem `httpx.Client(...).get(...)` em laço por termo. O
usuário é servidor público operando da rede do órgão; dezenas de requisições por busca contra
`planalto.gov.br`, `camara.leg.br` e `tcu.gov.br` é caminho concreto para **bloqueio do IP
institucional**. Sites .gov.br atrás de WAF também costumam devolver 403 ou página de desafio
para cliente sem User-Agent, e aí `extrair()` devolve lista vazia em vez de erro.
Este risco **não está na spec §7**.
**Emenda vinculante:** User-Agent identificável e honesto, intervalo mínimo entre requisições e
tratamento de 429/503 com backoff, nos três adaptadores, **antes** de qualquer execução contra a
web real. Acrescentar o risco à spec §7.

**R1-14 · Toda rota FastAPI vaza uma conexão sqlite.** ✅ [convergente: lentes 2 e 4]
O helper `conn()` (linha 2151) abre conexão nova a cada requisição e nunca fecha: sem
`close()`, sem `try/finally`, sem dependência com `yield`. São 6 rotas. Num app que a spec
descreve como servidor local de vida longa, é vazamento de handle por requisição. No Windows,
handle aberto também trava o teardown de `tmp_path` do pytest.
**Emenda vinculante:** trocar por dependência FastAPI com `yield` que fecha no `finally`, e
fechar a conexão em todo helper de teste que abre uma.

**R1-15 · Re-execução: o "aplicar" rebaixa tudo, e a decisão pós-download não reconcilia com o arquivo.** ✅ [lente 3]
(a) A seleção pega todas as linhas `decisao='fica'` sem checar se já existe `resultado_arquivo`.
Um segundo clique em "aplicar" **rebate na rede** tudo que já foi baixado, e como o sha256 é
idêntico, cada item já baixado é contado como "duplicata", poluindo justamente o relatório da
B4 com um sentido que não é o dele.
(b) Se o humano voltar à triagem e desmarcar um item **já baixado**, `gravar` o marca `sai` e
nada remove o arquivo nem o vínculo. A planilha passa a mostrar sha256 preenchido numa linha
com decisão `sai`: contradição direta dentro do documento de rastreabilidade.
**Emenda vinculante:** (a) pular o que já tem `resultado_arquivo`, sem tocar a rede e sem contar
como duplicata; contar duplicata só quando o mesmo sha256 aparece em `resultado_id` de **outro
tema**; (b) mudar decisão depois do download exige confirmação e grava override rastreável; a
planilha nunca mostra sha256 em linha `sai` sem marcar o histórico.

**R1-16 · O critério de sucesso nº 2 da spec não tem teste em nenhuma das 16 tasks.** ✅ [lente 5]
A spec §8 promete "100+ resultados triáveis em menos de **15 decisões humanas**". Nenhum teste
constrói um conjunto de 100+ resultados nem conta decisões. As 16 tasks podem ficar verdes e o
produto falhar no único número que o justifica.
**Emenda vinculante:** teste que monta 100+ resultados sintéticos com mistura realista de
`vinculacao`/`procedencia`/`ja_tenho`, roda `premarcar_todos` mais o agrupamento, e afirma um
teto de decisões necessárias abaixo de 15, usando as ações de grupo ao máximo.

**R1-17 · `pasta_do_tema` trunca em 32 chars sem desambiguador.** ✅ [lente 2]
Dois temas com os mesmos 32 primeiros caracteres normalizados caem na **mesma pasta**, sem
detecção. "Levantamento sobre Governança de Dados" e "Levantamento sobre Governança de Acesso"
colidem. É a falha que a B4 queria evitar, chegando por outro caminho.
**Emenda vinculante:** sufixar com `busca_id` ou hash curto do tema completo, mantendo o teto de
32 chars por causa do limite de 260.

**R1-18 · Fixture sintética não é gate de nada.** ✅ [convergente: lentes 2 e 5]
Nas T5 e T6 o mesmo autor escreve o seletor CSS **e** o HTML que o alimenta. Todo teste verde
dessas tasks prova só que o autor é coerente consigo mesmo. O plano admite isso, mas a admissão
mora numa **nota de risco em prosa no fim do documento**, não presa a nenhum checkbox. Um agente
que segue task a task com "N passed" como critério entrega os três adaptadores verdes e
estruturalmente não testados.
**Emenda vinculante:** vira **Step com checkbox** dentro das T5 e T6: a fixture real precisa
estar commitada antes da task poder ser marcada como feita. Enquanto não estiver, `buscar()` é
declarado **não verificado** no README e no `_TODO.md`.

**R1-19 · Seletor errado devolve lista vazia em silêncio, contra a mitigação da spec §7.** ✅ [convergente: lentes 2 e 4]
A spec §7 promete "falha é ruidosa" para adaptador que quebra. Isso só vale para o teste de
`extrair()` com fixture. No caminho real, se o HTML não casar o seletor, `css()` devolve lista
vazia, `extrair()` devolve `[]` e **nenhuma exceção sobe**. O `try/except` do orquestrador nunca
dispara; a fonte contribui zero resultado sem alarme.
**Emenda vinculante:** resposta HTTP 200 não vazia que produz **zero** extrações vira aviso
explícito, distinto de "a busca não achou nada". O orquestrador registra por fonte.

---

### MÉDIOS e BAIXOS (não bloqueiam, mas entram na task correspondente)

- **R1-20 · `CATALOGO`/`registrar` são código morto.** ✅ [confirmado na síntese] [convergente: lentes 1 e 4]
  Só aparecem no próprio arquivo da T4 e no teste dela (linhas 489, 496, 516-517, 550-554).
  `fontes_padrao` da T16 monta `[FontePlanalto(), FonteLegin(), FonteTCU()]` na mão. A promessa
  implícita de "fonte nova sem tocar o núcleo" **não é entregue**: acrescentar a ANPD ainda exige
  editar `cli.py`. **Emenda:** ou ligar `fontes_padrao` ao `CATALOGO`, ou remover o mecanismo da
  T4 e documentar que fonte nova custa uma linha no `cli.py`. Não deixar como está.
- **R1-21 · `ementa_llm` nunca é escrito.** ✅ [lente 1] O campo existe no dataclass e no schema,
  a decisão B3 promete "enriquece ementas", e **nenhuma task escreve nele**: o `INSERT` da T11
  nem o inclui. **Emenda:** implementar, ou corrigir a B3 na spec para não prometer o que o plano
  não entrega. 📝 Recomendação da síntese: corrigir a spec, é menos escopo e o LLM continua
  opcional.
- **R1-22 · A T12 declara consumir `sha256_arquivo` e não consome.** ✅ [lente 1] A seção
  `Interfaces` lista a função da T9; o código calcula `hashlib.sha256(conteudo)` inline sobre os
  bytes em memória. **Emenda:** corrigir a declaração, ou reusar de fato (ver R1-09, que quer o
  reuso por outro motivo).
- **R1-23 · `README.md` criado duas vezes** (T1 e T16, ambas como "Create"). ✅ [todas as lentes
  confirmaram] **Emenda:** a T16 passa a ser "Modify"; a T1 grava um esqueleto mínimo.
- **R1-24 · `openpyxl` levanta `IllegalCharacterError`** com caractere de controle vindo do HTML,
  abortando a planilha inteira por causa de uma linha. 📝 [lente 2] **Emenda:** limpar apenas os
  caracteres **ilegais em XML** antes de gravar a célula. ⚠ Cuidado: isso **não pode** virar
  normalização de texto, que seria paráfrase proibida pela spec §6.
- **R1-25 · O teste do `caminho_longo` é tautológico.** ✅ [lente 2] `assert caminho_longo(tmp_path
  / "x").endswith("x")` nunca falharia, mesmo com o helper inteiramente removido. **Emenda:**
  construir caminho real acima de 260 chars e afirmar o prefixo de caminho estendido do Windows.
- **R1-26 · `indexar()` depende da ordem do `rglob`.** ✅ [lente 5] `setdefault` guarda o primeiro,
  e a ordem do sistema de arquivos não é garantida: o "já tenho" pode apontar para arquivo
  diferente entre execuções. **Emenda:** `sorted()` e regra de desempate documentada.
- **R1-27 · Os três extratores catalogados não têm guarda de título vazio.** ✅ [lente 5] Âncora com
  href e texto vazio entra com `titulo=''`, passa no `NOT NULL`, e várias linhas malformadas
  colapsam na mesma `chave_dedup`. **Emenda:** replicar o `if not titulo or not url: continue` que
  a `FonteWebAberta` já tem.
- **R1-28 · `pytest-asyncio` é peso morto.** ✅ [lente 4] Está nas deps, não há `asyncio_mode`
  configurado e **nenhum** teste assíncrono no plano. **Emenda:** remover da dev extras.
- **R1-29 · `py` vs o interpretador explícito.** ✅ [lente 4] As ~32 instruções usam o atalho `py`,
  enquanto o `global-constraints.md` manda usar o caminho completo. Hoje funciona nesta máquina.
  **Emenda:** normalizar para o caminho do venv depois da R1-02.
- **R1-30 · `coletado_em` é calculado por linha** dentro da list comprehension, em vez de uma vez
  por busca. 📝 [lente 5] Inconsistência latente para qualquer agrupamento futuro por data de
  coleta.
- **R1-31 · Nada impede `raiz_dados` apontar para dentro de `acervo_raizes`.** 📝 [lente 3] Erro de
  configuração faria a ferramenta **escrever dentro do acervo só-leitura**. **Emenda sugerida:**
  validar em `carregar_config` que nenhuma raiz de acervo é ancestral da raiz de dados.
- **R1-32 · Decisões humanas não são reaproveitadas entre buscas do mesmo tema.** 📝 [lente 3]
  Rodar "LGPD" de novo meses depois recria tudo como não decidido, inclusive o que já foi
  triado. É o cenário mais provável em auditoria contínua e o plano não o trata nem documenta.
- **R1-33 · O dedup por sha256 assume determinismo de bytes que pode não existir.** 📝 [lente 2]
  PDF de acórdão gerado sob demanda costuma trazer timestamp de impressão ou marca por
  requisição: dois downloads do **mesmo** acórdão podem ter hash diferente. **Emenda:** registrar
  como limitação conhecida no README e na spec, em vez de apresentar o dedup sha256 como
  mitigação completa.

---

### O que a rodada 1 declarou SÃO (não mexer)

Verificado pelos revisores e não contestado: o schema SQLite em si (tipos, `CHECK`, `PRAGMA
foreign_keys` ligado, nenhum adaptador de data depreciado do Python 3.12+); a estrutura de
campos do `Resultado` e a passagem de `app.py` entre T14 e T15 (sem descasamento de nome ou
aridade); `selectolax` tem wheel `cp313-win_amd64` no PyPI, então não há risco de compilação;
`pip install -e .` funciona sem `[build-system]`; `python -m pytest` resolve `import buscador`
sem instalar o pacote; e `Form(default=[])` tipado `list[int]` funciona no FastAPI atual.

## Global Constraints

- **Python:** `C:\Users\P_8106\AppData\Local\Programs\Python\Python313\python.exe`. Rodar via **Bash**, não PowerShell — caminhos acentuados quebram no PowerShell 5.1.
- **Encoding:** todo arquivo `.py` é UTF-8. Todo `open()` passa `encoding="utf-8"` explicitamente.
- **Windows, limite de 260 caracteres:** nomes de pasta de tema no máximo **32 caracteres**; toda operação de arquivo usa o helper `caminho_longo()` da Task 13. Acima de 260 o Python falha **em silêncio** (`isfile` devolve `False`).
- **Texto normativo nunca é parafraseado.** Título e ementa são copiados literalmente da fonte. Texto derivado de LLM vai para campo separado (`ementa_llm`), nunca sobrescreve `ementa`.
- **Procedência obrigatória** em todo resultado: `catalogada` ou `web-aberta`.
- **O sistema roda inteiro sem LLM.** Nenhum caminho de código pode exigir chave de API.
- **Web aberta nunca é pré-marcada `fica`** (mitigação de risco da spec §7).
- **Item `obrigatorio` nunca é pré-marcado `sai`** (mitigação de ancoragem, spec §7).
- Commits frequentes, um por task no mínimo.

---

## File Structure

| Arquivo | Responsabilidade |
|---|---|
| `buscador/config.py` | Configuração, caminhos, catálogo de fontes |
| `buscador/db.py` | Schema SQLite, conexão, migração |
| `buscador/modelos.py` | Dataclasses do domínio |
| `buscador/normalizar.py` | Normalização de URL/título, chave de dedup |
| `buscador/llm.py` | Protocolo LLM + `NullLLM` + adaptador OpenAI-compatível |
| `buscador/palavras_chave.py` | Expansão de tema em termos de busca |
| `buscador/fontes/base.py` | Protocolo `Fonte` e `ResultadoBruto` |
| `buscador/fontes/planalto.py` | Adaptador do Planalto |
| `buscador/fontes/legin_camara.py` | Adaptador do Legin (Câmara) |
| `buscador/fontes/tcu.py` | Adaptador do portal do TCU |
| `buscador/fontes/web_aberta.py` | Busca genérica, rede de segurança |
| `buscador/acervo.py` | Índice sha256 do acervo existente, selo já-tenho |
| `buscador/premarcacao.py` | Regras de pré-marcação com justificativa |
| `buscador/busca.py` | Orquestrador da busca |
| `buscador/download.py` | Download, sha256, organização por tema, duplicatas |
| `buscador/planilha.py` | Planilha-registro openpyxl |
| `buscador/web/app.py` | FastAPI: rotas |
| `buscador/web/templates/` | Jinja2 |
| `buscador/cli.py` | CLI |

---

## Task 1: Fundação do repositório

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `README.md`, `buscador/__init__.py`, `buscador/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nada
- Produces: `Config` (dataclass com `raiz_dados: Path`, `banco: Path`, `acervo_raizes: list[Path]`, `llm_base_url: str | None`, `llm_modelo: str | None`), `carregar_config(env: dict[str,str] | None = None) -> Config`

- [ ] **Step 1: Criar o esqueleto do repo e o pyproject**

```bash
mkdir -p ~/Documents/solucoes/buscador-normativos/{buscador/fontes,buscador/web/templates,tests/fixtures}
cd ~/Documents/solucoes/buscador-normativos
touch buscador/__init__.py buscador/fontes/__init__.py buscador/web/__init__.py
```

`pyproject.toml`:

```toml
[project]
name = "buscador-normativos"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115",
    "uvicorn>=0.32",
    "jinja2>=3.1",
    "httpx>=0.27",
    "selectolax>=0.3.21",
    "openpyxl>=3.1",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = ["pytest>=8.3", "pytest-asyncio>=0.24"]

[project.scripts]
buscador = "buscador.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

`.gitignore`:

```
__pycache__/
*.pyc
.venv/
dados/
*.db
.env
```

- [ ] **Step 2: Escrever o teste que falha**

`tests/test_config.py`:

```python
from pathlib import Path
from buscador.config import carregar_config


def test_config_usa_padroes_quando_env_vazio():
    cfg = carregar_config(env={})
    assert cfg.raiz_dados == Path("dados")
    assert cfg.banco == Path("dados/buscador.db")
    assert cfg.llm_base_url is None


def test_config_le_llm_do_env():
    cfg = carregar_config(env={"BUSCADOR_LLM_URL": "http://localhost:8000/v1",
                               "BUSCADOR_LLM_MODELO": "qwen"})
    assert cfg.llm_base_url == "http://localhost:8000/v1"
    assert cfg.llm_modelo == "qwen"


def test_config_le_acervo_como_lista_separada_por_ponto_e_virgula():
    cfg = carregar_config(env={"BUSCADOR_ACERVO": "C:/a;C:/b"})
    assert cfg.acervo_raizes == [Path("C:/a"), Path("C:/b")]
```

- [ ] **Step 3: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_config.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'buscador.config'`

- [ ] **Step 4: Implementar**

`buscador/config.py`:

```python
"""Configuracao do buscador. Tudo vem de variaveis de ambiente, com padroes seguros."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    raiz_dados: Path
    banco: Path
    acervo_raizes: list[Path] = field(default_factory=list)
    llm_base_url: str | None = None
    llm_modelo: str | None = None
    llm_chave: str | None = None


def carregar_config(env: dict[str, str] | None = None) -> Config:
    e = os.environ if env is None else env
    raiz = Path(e.get("BUSCADOR_DADOS", "dados"))
    acervo_bruto = e.get("BUSCADOR_ACERVO", "").strip()
    acervo = [Path(p) for p in acervo_bruto.split(";") if p.strip()]
    return Config(
        raiz_dados=raiz,
        banco=raiz / "buscador.db",
        acervo_raizes=acervo,
        llm_base_url=e.get("BUSCADOR_LLM_URL") or None,
        llm_modelo=e.get("BUSCADOR_LLM_MODELO") or None,
        llm_chave=e.get("BUSCADOR_LLM_CHAVE") or None,
    )
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_config.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git init
git add -A
git commit -m "feat: fundacao do repo (pyproject, config, gitignore)"
```

---

## Task 2: Banco SQLite

**Files:**
- Create: `buscador/db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Consumes: `Config` da Task 1
- Produces: `conectar(caminho: Path) -> sqlite3.Connection`, `criar_schema(conn) -> None`

Tabelas: `buscas`, `resultados`, `arquivos`, `resultado_arquivo`.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_db.py`:

```python
import sqlite3
from buscador.db import conectar, criar_schema


def test_criar_schema_cria_as_quatro_tabelas(tmp_path):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    nomes = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"buscas", "resultados", "arquivos", "resultado_arquivo"} <= nomes


def test_criar_schema_e_idempotente(tmp_path):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    criar_schema(conn)  # nao pode levantar


def test_resultado_exige_procedencia_valida(tmp_path):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    conn.execute("INSERT INTO buscas (tema, criado_em) VALUES ('x', '2026-01-01')")
    import pytest
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO resultados (busca_id, titulo, url, fonte, procedencia, "
            "vinculacao, chave_dedup) VALUES (1, 't', 'u', 'f', 'INVALIDA', "
            "'contexto', 'k')")


def test_chave_dedup_e_unica_por_busca(tmp_path):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    conn.execute("INSERT INTO buscas (tema, criado_em) VALUES ('x', '2026-01-01')")
    ins = ("INSERT INTO resultados (busca_id, titulo, url, fonte, procedencia, "
           "vinculacao, chave_dedup) VALUES (1, 't', 'u', 'f', 'catalogada', "
           "'contexto', 'k')")
    conn.execute(ins)
    import pytest
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(ins)
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_db.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'buscador.db'`

- [ ] **Step 3: Implementar**

`buscador/db.py`:

```python
"""Estado do pipeline. Cada etapa grava aqui, por isso toda etapa e retomavel."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS buscas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tema        TEXT NOT NULL,
    pasta       TEXT,
    termos      TEXT,
    criado_em   TEXT NOT NULL,
    triado_em   TEXT,
    baixado_em  TEXT
);

CREATE TABLE IF NOT EXISTS resultados (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    busca_id      INTEGER NOT NULL REFERENCES buscas(id) ON DELETE CASCADE,
    titulo        TEXT NOT NULL,
    tipo          TEXT,
    ano           INTEGER,
    ementa        TEXT,
    ementa_llm    TEXT,
    url           TEXT NOT NULL,
    fonte         TEXT NOT NULL,
    procedencia   TEXT NOT NULL CHECK (procedencia IN ('catalogada','web-aberta')),
    vinculacao    TEXT NOT NULL CHECK (vinculacao IN ('obrigatorio','aplicavel','contexto')),
    categoria     TEXT,
    chave_dedup   TEXT NOT NULL,
    ja_tenho      INTEGER NOT NULL DEFAULT 0,
    ja_tenho_onde TEXT,
    pre_marca     TEXT CHECK (pre_marca IN ('fica','sai')),
    pre_motivo    TEXT,
    decisao       TEXT CHECK (decisao IN ('fica','sai')),
    decidido_em   TEXT,
    coletado_em   TEXT,
    UNIQUE (busca_id, chave_dedup)
);

CREATE TABLE IF NOT EXISTS arquivos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sha256     TEXT NOT NULL UNIQUE,
    caminho    TEXT NOT NULL,
    tamanho    INTEGER NOT NULL,
    baixado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resultado_arquivo (
    resultado_id INTEGER NOT NULL REFERENCES resultados(id) ON DELETE CASCADE,
    arquivo_id   INTEGER NOT NULL REFERENCES arquivos(id) ON DELETE CASCADE,
    duplicata    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (resultado_id, arquivo_id)
);

CREATE INDEX IF NOT EXISTS ix_res_busca ON resultados(busca_id);
CREATE INDEX IF NOT EXISTS ix_res_cat ON resultados(busca_id, categoria);
"""


def conectar(caminho: Path) -> sqlite3.Connection:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(caminho, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def criar_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_db.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/db.py tests/test_db.py
git commit -m "feat: schema sqlite com constraints de procedencia e dedup"
```

---

## Task 3: Modelos e normalização

**Files:**
- Create: `buscador/modelos.py`, `buscador/normalizar.py`
- Test: `tests/test_normalizar.py`

**Interfaces:**
- Consumes: nada
- Produces: `Resultado` (dataclass), `normalizar_url(url: str) -> str`, `normalizar_titulo(t: str) -> str`, `chave_dedup(url: str, titulo: str) -> str`

A chave de dedup é o que impede o mesmo normativo de aparecer duas vezes vindo de fontes diferentes.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_normalizar.py`:

```python
from buscador.normalizar import normalizar_url, normalizar_titulo, chave_dedup


def test_normalizar_url_remove_query_e_fragmento_e_barra_final():
    assert normalizar_url("https://X.gov.br/Lei.htm?a=1#topo") == "https://x.gov.br/lei.htm"
    assert normalizar_url("https://x.gov.br/pasta/") == "https://x.gov.br/pasta"


def test_normalizar_titulo_remove_acento_pontuacao_e_caixa():
    assert normalizar_titulo("Lei nº 13.709/2018 (LGPD)") == "lei n 13 709 2018 lgpd"


def test_chave_dedup_igual_para_mesma_url_com_ruido():
    a = chave_dedup("https://x.gov.br/L1.htm?x=1", "Lei nº 1")
    b = chave_dedup("https://X.gov.br/L1.htm", "Lei n. 1")
    assert a == b


def test_chave_dedup_diferente_para_normativos_diferentes():
    a = chave_dedup("https://x.gov.br/L1.htm", "Lei nº 1")
    b = chave_dedup("https://x.gov.br/L2.htm", "Lei nº 2")
    assert a != b
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_normalizar.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/normalizar.py`:

```python
"""Normalizacao usada para deduplicar resultados vindos de fontes diferentes."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit


def normalizar_url(url: str) -> str:
    p = urlsplit(url.strip())
    caminho = p.path.rstrip("/") or "/"
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), caminho, "", "")).rstrip("/")


def normalizar_titulo(titulo: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", titulo)
        if unicodedata.category(c) != "Mn"
    )
    limpo = re.sub(r"[^0-9a-zA-Z]+", " ", sem_acento.lower())
    return re.sub(r"\s+", " ", limpo).strip()


def chave_dedup(url: str, titulo: str) -> str:
    """A URL manda. O titulo entra so quando a URL nao e informativa."""
    base = normalizar_url(url)
    if not base or base.count("/") <= 2:
        base = normalizar_titulo(titulo)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]
```

`buscador/modelos.py`:

```python
"""Dataclasses do dominio. Espelham as colunas de `resultados`."""
from __future__ import annotations

from dataclasses import dataclass

Procedencia = str  # 'catalogada' | 'web-aberta'
Vinculacao = str   # 'obrigatorio' | 'aplicavel' | 'contexto'


@dataclass
class Resultado:
    titulo: str
    url: str
    fonte: str
    procedencia: Procedencia
    vinculacao: Vinculacao
    chave_dedup: str
    tipo: str | None = None
    ano: int | None = None
    ementa: str | None = None
    ementa_llm: str | None = None
    categoria: str | None = None
    ja_tenho: bool = False
    ja_tenho_onde: str | None = None
    pre_marca: str | None = None
    pre_motivo: str | None = None
    id: int | None = None
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_normalizar.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/modelos.py buscador/normalizar.py tests/test_normalizar.py
git commit -m "feat: modelos e chave de deduplicacao"
```

---

## Task 4: Protocolo `Fonte` e catálogo

**Files:**
- Create: `buscador/fontes/base.py`
- Test: `tests/test_fontes_base.py`

**Interfaces:**
- Consumes: `Resultado` da Task 3
- Produces: `Fonte` (Protocol com `nome: str`, `procedencia: str`, `vinculacao_padrao: str`, `categoria: str`, `buscar(termos: list[str]) -> list[Resultado]`), `FonteFake` (para testes), `CATALOGO: dict[str, Fonte]`, `registrar(fonte)`

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_fontes_base.py`:

```python
from buscador.fontes.base import Fonte, FonteFake, CATALOGO, registrar
from buscador.modelos import Resultado


def test_fonte_fake_devolve_resultados_com_procedencia_e_chave():
    f = FonteFake(nome="fake", itens=[("Lei nº 1", "https://x.gov.br/l1.htm")])
    out = f.buscar(["lgpd"])
    assert len(out) == 1
    assert isinstance(out[0], Resultado)
    assert out[0].procedencia == "catalogada"
    assert out[0].fonte == "fake"
    assert out[0].chave_dedup


def test_fonte_fake_satisfaz_o_protocolo():
    assert isinstance(FonteFake(nome="f", itens=[]), Fonte)


def test_registrar_adiciona_ao_catalogo():
    f = FonteFake(nome="registrada", itens=[])
    registrar(f)
    assert CATALOGO["registrada"] is f
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_fontes_base.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/fontes/base.py`:

```python
"""Protocolo comum das fontes. Cada adaptador e trocavel e testavel isolado."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from buscador.modelos import Resultado
from buscador.normalizar import chave_dedup


@runtime_checkable
class Fonte(Protocol):
    nome: str
    procedencia: str
    vinculacao_padrao: str
    categoria: str

    def buscar(self, termos: list[str]) -> list[Resultado]: ...


CATALOGO: dict[str, Fonte] = {}


def registrar(fonte: Fonte) -> None:
    CATALOGO[fonte.nome] = fonte


@dataclass
class FonteFake:
    """Fonte deterministica para teste. Nunca toca a rede."""
    nome: str
    itens: list[tuple[str, str]]
    procedencia: str = "catalogada"
    vinculacao_padrao: str = "aplicavel"
    categoria: str = "fake"
    chamadas: list[list[str]] = field(default_factory=list)

    def buscar(self, termos: list[str]) -> list[Resultado]:
        self.chamadas.append(list(termos))
        return [
            Resultado(
                titulo=t,
                url=u,
                fonte=self.nome,
                procedencia=self.procedencia,
                vinculacao=self.vinculacao_padrao,
                categoria=self.categoria,
                chave_dedup=chave_dedup(u, t),
            )
            for t, u in self.itens
        ]
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_fontes_base.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/fontes/base.py tests/test_fontes_base.py
git commit -m "feat: protocolo Fonte, catalogo e FonteFake"
```

---

## Task 5: Adaptador do Planalto

**Files:**
- Create: `buscador/fontes/planalto.py`, `tests/fixtures/planalto_busca.html`
- Test: `tests/test_fonte_planalto.py`

**Interfaces:**
- Consumes: `Fonte`, `Resultado`
- Produces: `FontePlanalto(cliente: httpx.Client | None = None)` com `.buscar(termos) -> list[Resultado]` e `.extrair(html: str) -> list[Resultado]`

`extrair` é separado de `buscar` **de propósito**: o teste roda sobre a fixture, sem rede.

- [ ] **Step 1: Salvar a fixture**

Baixe uma página de resultado real uma única vez e salve. Se não houver rede, crie o arquivo à mão com esta estrutura mínima:

`tests/fixtures/planalto_busca.html`:

```html
<html><body>
<div class="resultado">
  <a href="/ccivil_03/_ato2015-2018/2018/lei/L13709compilado.htm">LEI Nº 13.709, DE 14 DE AGOSTO DE 2018</a>
  <p class="ementa">Lei Geral de Proteção de Dados Pessoais (LGPD).</p>
</div>
<div class="resultado">
  <a href="/ccivil_03/_ato2019-2022/2019/lei/l13853.htm">LEI Nº 13.853, DE 8 DE JULHO DE 2019</a>
  <p class="ementa">Altera a Lei nº 13.709, de 14 de agosto de 2018.</p>
</div>
</body></html>
```

- [ ] **Step 2: Escrever o teste que falha**

`tests/test_fonte_planalto.py`:

```python
from pathlib import Path
from buscador.fontes.planalto import FontePlanalto

FIXTURE = Path(__file__).parent / "fixtures" / "planalto_busca.html"


def test_extrai_titulo_url_absoluta_e_ementa_literais():
    html = FIXTURE.read_text(encoding="utf-8")
    out = FontePlanalto().extrair(html)
    assert len(out) == 2
    assert out[0].titulo == "LEI Nº 13.709, DE 14 DE AGOSTO DE 2018"
    assert out[0].url.startswith("https://www.planalto.gov.br/ccivil_03/")
    assert out[0].ementa == "Lei Geral de Proteção de Dados Pessoais (LGPD)."


def test_extrai_o_ano_do_titulo():
    out = FontePlanalto().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert out[0].ano == 2018
    assert out[1].ano == 2019


def test_planalto_e_catalogada_e_obrigatoria():
    out = FontePlanalto().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert out[0].procedencia == "catalogada"
    assert out[0].vinculacao == "obrigatorio"
    assert out[0].categoria == "legislacao-federal"


def test_html_vazio_devolve_lista_vazia_sem_levantar():
    assert FontePlanalto().extrair("<html></html>") == []
```

- [ ] **Step 3: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_fonte_planalto.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 4: Implementar**

`buscador/fontes/planalto.py`:

```python
"""Adaptador do Planalto (legislacao federal)."""
from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from buscador.modelos import Resultado
from buscador.normalizar import chave_dedup

BASE = "https://www.planalto.gov.br"
ANO = re.compile(r"\b(19|20)\d{2}\b")


class FontePlanalto:
    nome = "planalto"
    procedencia = "catalogada"
    vinculacao_padrao = "obrigatorio"
    categoria = "legislacao-federal"

    def __init__(self, cliente: httpx.Client | None = None) -> None:
        self._cliente = cliente

    def extrair(self, html: str) -> list[Resultado]:
        doc = HTMLParser(html)
        out: list[Resultado] = []
        for bloco in doc.css("div.resultado"):
            link = bloco.css_first("a")
            if link is None or not link.attributes.get("href"):
                continue
            titulo = link.text(strip=True)
            url = urljoin(BASE, link.attributes["href"])
            ementa_no = bloco.css_first("p.ementa")
            ementa = ementa_no.text(strip=True) if ementa_no else None
            m = ANO.search(titulo)
            out.append(Resultado(
                titulo=titulo,
                url=url,
                fonte=self.nome,
                procedencia=self.procedencia,
                vinculacao=self.vinculacao_padrao,
                categoria=self.categoria,
                ementa=ementa,
                ano=int(m.group(0)) if m else None,
                chave_dedup=chave_dedup(url, titulo),
            ))
        return out

    def buscar(self, termos: list[str]) -> list[Resultado]:
        cliente = self._cliente or httpx.Client(timeout=20.0, follow_redirects=True)
        vistos: set[str] = set()
        out: list[Resultado] = []
        for termo in termos:
            r = cliente.get(f"{BASE}/busca", params={"q": termo})
            r.raise_for_status()
            for res in self.extrair(r.text):
                if res.chave_dedup not in vistos:
                    vistos.add(res.chave_dedup)
                    out.append(res)
        return out
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_fonte_planalto.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add buscador/fontes/planalto.py tests/test_fonte_planalto.py tests/fixtures/planalto_busca.html
git commit -m "feat: adaptador do Planalto com fixture e teste de contrato"
```

---

## Task 6: Adaptadores Legin (Câmara) e TCU

**Files:**
- Create: `buscador/fontes/legin_camara.py`, `buscador/fontes/tcu.py`, `tests/fixtures/legin_busca.html`, `tests/fixtures/tcu_busca.html`
- Test: `tests/test_fonte_legin.py`, `tests/test_fonte_tcu.py`

**Interfaces:**
- Consumes: mesmo padrão da Task 5
- Produces: `FonteLegin` (categoria `normativos-camara`, vinculação `obrigatorio`), `FonteTCU` (categoria `acordaos-tcu`, vinculação `aplicavel`)

- [ ] **Step 1: Criar as fixtures**

`tests/fixtures/legin_busca.html`:

```html
<html><body>
<ul class="lista-resultados">
  <li><a href="/legin/int/atomes/2020/atodamesa-152-16-dezembro-2020.html">ATO DA MESA Nº 152, DE 16 DE DEZEMBRO DE 2020</a>
      <span class="ementa">Dispõe sobre a proteção de dados pessoais no âmbito da Câmara dos Deputados.</span></li>
</ul>
</body></html>
```

`tests/fixtures/tcu_busca.html`:

```html
<html><body>
<div class="item-resultado">
  <a class="titulo" href="/data/files/acordao-1372-2025.pdf">Acórdão 1372/2025 - Plenário</a>
  <div class="resumo">Levantamento sobre a adequação de organizações federais à LGPD.</div>
</div>
</body></html>
```

- [ ] **Step 2: Escrever os testes que falham**

`tests/test_fonte_legin.py`:

```python
from pathlib import Path
from buscador.fontes.legin_camara import FonteLegin

FIXTURE = Path(__file__).parent / "fixtures" / "legin_busca.html"


def test_extrai_ato_da_mesa_com_ementa_literal():
    out = FonteLegin().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert len(out) == 1
    assert out[0].titulo == "ATO DA MESA Nº 152, DE 16 DE DEZEMBRO DE 2020"
    assert out[0].ementa.startswith("Dispõe sobre a proteção de dados pessoais")
    assert out[0].url.startswith("https://www2.camara.leg.br/legin/")
    assert out[0].ano == 2020


def test_legin_e_normativo_interno_obrigatorio():
    out = FonteLegin().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert out[0].categoria == "normativos-camara"
    assert out[0].vinculacao == "obrigatorio"
    assert out[0].procedencia == "catalogada"


def test_html_vazio_devolve_lista_vazia():
    assert FonteLegin().extrair("<html></html>") == []
```

`tests/test_fonte_tcu.py`:

```python
from pathlib import Path
from buscador.fontes.tcu import FonteTCU

FIXTURE = Path(__file__).parent / "fixtures" / "tcu_busca.html"


def test_extrai_acordao_com_resumo():
    out = FonteTCU().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert len(out) == 1
    assert out[0].titulo == "Acórdão 1372/2025 - Plenário"
    assert out[0].ementa.startswith("Levantamento sobre a adequação")
    assert out[0].ano == 2025


def test_tcu_e_aplicavel_nao_obrigatorio():
    out = FonteTCU().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert out[0].vinculacao == "aplicavel"
    assert out[0].categoria == "acordaos-tcu"


def test_html_vazio_devolve_lista_vazia():
    assert FonteTCU().extrair("<html></html>") == []
```

- [ ] **Step 3: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_fonte_legin.py tests/test_fonte_tcu.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 4: Implementar**

`buscador/fontes/legin_camara.py`:

```python
"""Adaptador do Legin (normativos internos da Camara)."""
from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from buscador.modelos import Resultado
from buscador.normalizar import chave_dedup

BASE = "https://www2.camara.leg.br"
ANO = re.compile(r"\b(19|20)\d{2}\b")


class FonteLegin:
    nome = "legin-camara"
    procedencia = "catalogada"
    vinculacao_padrao = "obrigatorio"
    categoria = "normativos-camara"

    def __init__(self, cliente: httpx.Client | None = None) -> None:
        self._cliente = cliente

    def extrair(self, html: str) -> list[Resultado]:
        doc = HTMLParser(html)
        out: list[Resultado] = []
        for item in doc.css("ul.lista-resultados li"):
            link = item.css_first("a")
            if link is None or not link.attributes.get("href"):
                continue
            titulo = link.text(strip=True)
            url = urljoin(BASE, link.attributes["href"])
            no = item.css_first("span.ementa")
            m = ANO.search(titulo)
            out.append(Resultado(
                titulo=titulo,
                url=url,
                fonte=self.nome,
                procedencia=self.procedencia,
                vinculacao=self.vinculacao_padrao,
                categoria=self.categoria,
                ementa=no.text(strip=True) if no else None,
                ano=int(m.group(0)) if m else None,
                chave_dedup=chave_dedup(url, titulo),
            ))
        return out

    def buscar(self, termos: list[str]) -> list[Resultado]:
        cliente = self._cliente or httpx.Client(timeout=20.0, follow_redirects=True)
        vistos: set[str] = set()
        out: list[Resultado] = []
        for termo in termos:
            r = cliente.get(f"{BASE}/legin/busca", params={"termo": termo})
            r.raise_for_status()
            for res in self.extrair(r.text):
                if res.chave_dedup not in vistos:
                    vistos.add(res.chave_dedup)
                    out.append(res)
        return out
```

`buscador/fontes/tcu.py`:

```python
"""Adaptador do portal do TCU (acordaos e pecas)."""
from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from buscador.modelos import Resultado
from buscador.normalizar import chave_dedup

BASE = "https://portal.tcu.gov.br"
ANO = re.compile(r"\b(19|20)\d{2}\b")


class FonteTCU:
    nome = "tcu"
    procedencia = "catalogada"
    vinculacao_padrao = "aplicavel"
    categoria = "acordaos-tcu"

    def __init__(self, cliente: httpx.Client | None = None) -> None:
        self._cliente = cliente

    def extrair(self, html: str) -> list[Resultado]:
        doc = HTMLParser(html)
        out: list[Resultado] = []
        for item in doc.css("div.item-resultado"):
            link = item.css_first("a.titulo")
            if link is None or not link.attributes.get("href"):
                continue
            titulo = link.text(strip=True)
            url = urljoin(BASE, link.attributes["href"])
            no = item.css_first("div.resumo")
            m = ANO.search(titulo)
            out.append(Resultado(
                titulo=titulo,
                url=url,
                fonte=self.nome,
                procedencia=self.procedencia,
                vinculacao=self.vinculacao_padrao,
                categoria=self.categoria,
                ementa=no.text(strip=True) if no else None,
                ano=int(m.group(0)) if m else None,
                chave_dedup=chave_dedup(url, titulo),
            ))
        return out

    def buscar(self, termos: list[str]) -> list[Resultado]:
        cliente = self._cliente or httpx.Client(timeout=20.0, follow_redirects=True)
        vistos: set[str] = set()
        out: list[Resultado] = []
        for termo in termos:
            r = cliente.get(f"{BASE}/busca", params={"q": termo})
            r.raise_for_status()
            for res in self.extrair(r.text):
                if res.chave_dedup not in vistos:
                    vistos.add(res.chave_dedup)
                    out.append(res)
        return out
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_fonte_legin.py tests/test_fonte_tcu.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add buscador/fontes/legin_camara.py buscador/fontes/tcu.py tests/test_fonte_legin.py tests/test_fonte_tcu.py tests/fixtures/legin_busca.html tests/fixtures/tcu_busca.html
git commit -m "feat: adaptadores Legin e TCU"
```

---

## Task 7: Fonte de web aberta

**Files:**
- Create: `buscador/fontes/web_aberta.py`
- Test: `tests/test_fonte_web_aberta.py`

**Interfaces:**
- Consumes: `Resultado`
- Produces: `FonteWebAberta(buscador_fn: Callable[[str], list[dict]])` — recebe a função de busca por injeção, para o teste não tocar a rede. Todo resultado sai com `procedencia="web-aberta"`, `vinculacao="contexto"`.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_fonte_web_aberta.py`:

```python
from buscador.fontes.web_aberta import FonteWebAberta


def busca_falsa(termo):
    return [{"titulo": f"Resultado de {termo}", "url": f"https://exemplo.org/{termo}",
             "resumo": "resumo qualquer"}]


def test_web_aberta_marca_procedencia_e_vinculacao_de_contexto():
    out = FonteWebAberta(busca_falsa).buscar(["lgpd"])
    assert len(out) == 1
    assert out[0].procedencia == "web-aberta"
    assert out[0].vinculacao == "contexto"
    assert out[0].categoria == "a-triar"


def test_web_aberta_deduplica_entre_termos():
    def repetida(termo):
        return [{"titulo": "Mesmo", "url": "https://exemplo.org/igual", "resumo": ""}]
    out = FonteWebAberta(repetida).buscar(["a", "b", "c"])
    assert len(out) == 1


def test_web_aberta_sem_resultados_nao_levanta():
    assert FonteWebAberta(lambda t: []).buscar(["x"]) == []
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_fonte_web_aberta.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/fontes/web_aberta.py`:

```python
"""Rede de seguranca: busca generica. Tudo que sai daqui nasce 'a conferir'."""
from __future__ import annotations

from collections.abc import Callable

from buscador.modelos import Resultado
from buscador.normalizar import chave_dedup

BuscaFn = Callable[[str], list[dict]]


class FonteWebAberta:
    nome = "web-aberta"
    procedencia = "web-aberta"
    vinculacao_padrao = "contexto"
    categoria = "a-triar"

    def __init__(self, buscador_fn: BuscaFn) -> None:
        self._buscar_fn = buscador_fn

    def buscar(self, termos: list[str]) -> list[Resultado]:
        vistos: set[str] = set()
        out: list[Resultado] = []
        for termo in termos:
            for item in self._buscar_fn(termo):
                url = item.get("url", "")
                titulo = item.get("titulo", "")
                if not url or not titulo:
                    continue
                chave = chave_dedup(url, titulo)
                if chave in vistos:
                    continue
                vistos.add(chave)
                out.append(Resultado(
                    titulo=titulo,
                    url=url,
                    fonte=self.nome,
                    procedencia=self.procedencia,
                    vinculacao=self.vinculacao_padrao,
                    categoria=self.categoria,
                    ementa=item.get("resumo") or None,
                    chave_dedup=chave,
                ))
        return out
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_fonte_web_aberta.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/fontes/web_aberta.py tests/test_fonte_web_aberta.py
git commit -m "feat: fonte de web aberta com procedencia marcada"
```

---

## Task 8: Palavras-chave (regra + LLM opcional)

**Files:**
- Create: `buscador/llm.py`, `buscador/palavras_chave.py`
- Test: `tests/test_palavras_chave.py`

**Interfaces:**
- Consumes: `Config`
- Produces: `LLM` (Protocol com `completar(prompt: str) -> str`), `NullLLM`, `LLMOpenAICompat(base_url, modelo, chave)`, `expandir(tema: str, llm: LLM | None = None) -> list[str]`

**Requisito duro:** com `llm=None` a função devolve termos úteis. O LLM só acrescenta.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_palavras_chave.py`:

```python
from buscador.llm import NullLLM
from buscador.palavras_chave import expandir


def test_expandir_sem_llm_devolve_o_tema_e_sinonimos_conhecidos():
    termos = expandir("LGPD")
    assert "LGPD" in termos
    assert any("dados pessoais" in t.lower() for t in termos)


def test_expandir_sem_llm_nunca_devolve_lista_vazia():
    assert expandir("tema totalmente desconhecido xyz") != []


def test_expandir_com_null_llm_e_igual_a_sem_llm():
    assert expandir("LGPD", NullLLM()) == expandir("LGPD")


def test_expandir_com_llm_acrescenta_sem_perder_os_de_regra():
    class LLMFalso:
        def completar(self, prompt):
            return "termo extra 1\ntermo extra 2"
    termos = expandir("LGPD", LLMFalso())
    assert "LGPD" in termos
    assert "termo extra 1" in termos


def test_expandir_deduplica_e_preserva_ordem():
    class LLMRepetido:
        def completar(self, prompt):
            return "LGPD\nLGPD\nnovo"
    termos = expandir("LGPD", LLMRepetido())
    assert termos.count("LGPD") == 1
    assert termos[0] == "LGPD"


def test_expandir_tolera_llm_que_quebra():
    class LLMQuebrado:
        def completar(self, prompt):
            raise RuntimeError("sem rede")
    assert "LGPD" in expandir("LGPD", LLMQuebrado())
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_palavras_chave.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/llm.py`:

```python
"""LLM e OPCIONAL. Com NullLLM o sistema roda inteiro."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

import httpx


@runtime_checkable
class LLM(Protocol):
    def completar(self, prompt: str) -> str: ...


class NullLLM:
    """Nao chama nada. Existe para o resto do codigo nao precisar de `if llm`."""

    def completar(self, prompt: str) -> str:
        return ""


class LLMOpenAICompat:
    """Serve nuvem e LLM local: ambos falam a API OpenAI-compativel."""

    def __init__(self, base_url: str, modelo: str, chave: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.modelo = modelo
        self.chave = chave

    def completar(self, prompt: str) -> str:
        cabecalhos = {"Authorization": f"Bearer {self.chave}"} if self.chave else {}
        r = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=cabecalhos,
            json={"model": self.modelo,
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0},
            timeout=60.0,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
```

`buscador/palavras_chave.py`:

```python
"""Expansao do tema em termos de busca. Regra primeiro; LLM so acrescenta."""
from __future__ import annotations

import logging

from buscador.llm import LLM

log = logging.getLogger(__name__)

SINONIMOS: dict[str, list[str]] = {
    "lgpd": ["Lei 13.709", "proteção de dados pessoais", "tratamento de dados pessoais",
             "encarregado de dados pessoais", "ANPD"],
    "ia": ["inteligência artificial", "governança de IA", "sistema de IA"],
    "governanca": ["governança", "governança corporativa", "controle interno"],
    "auditoria": ["auditoria interna", "controle interno", "papel de trabalho"],
}

PROMPT = (
    "Liste de 5 a 8 termos de busca em portugues para encontrar normativos e "
    "documentos oficiais brasileiros sobre o tema abaixo. Um termo por linha, "
    "sem numeracao, sem explicacao.\n\nTema: {tema}"
)


def _por_regra(tema: str) -> list[str]:
    termos = [tema.strip()]
    chave = tema.strip().lower()
    for gatilho, extras in SINONIMOS.items():
        if gatilho in chave:
            termos.extend(extras)
    return termos


def expandir(tema: str, llm: LLM | None = None) -> list[str]:
    termos = _por_regra(tema)
    if llm is not None:
        try:
            bruto = llm.completar(PROMPT.format(tema=tema))
            termos.extend(l.strip() for l in bruto.splitlines() if l.strip())
        except Exception:
            log.warning("LLM falhou na expansao; seguindo so com regra", exc_info=True)
    vistos: set[str] = set()
    saida: list[str] = []
    for t in termos:
        if t.lower() not in vistos:
            vistos.add(t.lower())
            saida.append(t)
    return saida
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_palavras_chave.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/llm.py buscador/palavras_chave.py tests/test_palavras_chave.py
git commit -m "feat: palavras-chave por regra com LLM opcional e tolerante a falha"
```

---

## Task 9: Índice do acervo e selo "já tenho"

**Files:**
- Create: `buscador/acervo.py`
- Test: `tests/test_acervo.py`

**Interfaces:**
- Consumes: `Resultado`, `normalizar_titulo`
- Produces: `indexar(raizes: list[Path]) -> dict[str, str]` (título normalizado → caminho), `sha256_arquivo(p: Path) -> str`, `marcar_ja_tenho(resultados: list[Resultado], indice: dict[str,str]) -> list[Resultado]`

Este é o mecanismo **M1** da spec: tira do caminho o que já existe no acervo.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_acervo.py`:

```python
from pathlib import Path
from buscador.acervo import indexar, marcar_ja_tenho, sha256_arquivo
from buscador.modelos import Resultado


def _res(titulo, url="https://x/y"):
    return Resultado(titulo=titulo, url=url, fonte="f", procedencia="catalogada",
                     vinculacao="aplicavel", chave_dedup=titulo)


def test_indexar_encontra_arquivos_por_titulo_normalizado(tmp_path):
    (tmp_path / "ATO DA MESA Nº 152.docx").write_text("x", encoding="utf-8")
    indice = indexar([tmp_path])
    assert "ato da mesa n 152" in indice


def test_indexar_ignora_pasta_inexistente_sem_levantar(tmp_path):
    assert indexar([tmp_path / "nao-existe"]) == {}


def test_marcar_ja_tenho_aplica_selo_e_caminho(tmp_path):
    (tmp_path / "Lei nº 13.709.pdf").write_text("x", encoding="utf-8")
    indice = indexar([tmp_path])
    out = marcar_ja_tenho([_res("Lei nº 13.709")], indice)
    assert out[0].ja_tenho is True
    assert out[0].ja_tenho_onde.endswith("Lei nº 13.709.pdf")


def test_marcar_ja_tenho_deixa_intacto_o_que_nao_existe(tmp_path):
    out = marcar_ja_tenho([_res("Norma inedita")], indexar([tmp_path]))
    assert out[0].ja_tenho is False
    assert out[0].ja_tenho_onde is None


def test_sha256_arquivo_e_estavel(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes(b"conteudo")
    assert sha256_arquivo(p) == sha256_arquivo(p)
    assert len(sha256_arquivo(p)) == 64
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_acervo.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/acervo.py`:

```python
"""Indice do acervo que ja existe. Mecanismo M1: reduzir decisoes."""
from __future__ import annotations

import hashlib
from pathlib import Path

from buscador.modelos import Resultado
from buscador.normalizar import normalizar_titulo

EXTENSOES = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".htm", ".html", ".md", ".txt"}


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def indexar(raizes: list[Path]) -> dict[str, str]:
    """Titulo normalizado (sem extensao) -> caminho absoluto."""
    indice: dict[str, str] = {}
    for raiz in raizes:
        if not raiz.exists():
            continue
        for p in raiz.rglob("*"):
            if p.is_file() and p.suffix.lower() in EXTENSOES:
                indice.setdefault(normalizar_titulo(p.stem), str(p))
    return indice


def marcar_ja_tenho(resultados: list[Resultado],
                    indice: dict[str, str]) -> list[Resultado]:
    for r in resultados:
        caminho = indice.get(normalizar_titulo(r.titulo))
        if caminho:
            r.ja_tenho = True
            r.ja_tenho_onde = caminho
    return resultados
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_acervo.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/acervo.py tests/test_acervo.py
git commit -m "feat: indice do acervo e selo ja-tenho (M1)"
```

---

## Task 10: Pré-marcação com justificativa

**Files:**
- Create: `buscador/premarcacao.py`
- Test: `tests/test_premarcacao.py`

**Interfaces:**
- Consumes: `Resultado`
- Produces: `premarcar(r: Resultado) -> Resultado` (preenche `pre_marca` e `pre_motivo`), `premarcar_todos(rs: list[Resultado]) -> list[Resultado]`

Mecanismos **M3** e **M4**. As duas travas da spec §7 são regras aqui, e têm teste próprio.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_premarcacao.py`:

```python
from buscador.modelos import Resultado
from buscador.premarcacao import premarcar, premarcar_todos


def _res(**kw):
    base = dict(titulo="t", url="u", fonte="f", procedencia="catalogada",
                vinculacao="aplicavel", chave_dedup="k")
    base.update(kw)
    return Resultado(**base)


def test_obrigatorio_e_sempre_fica():
    r = premarcar(_res(vinculacao="obrigatorio"))
    assert r.pre_marca == "fica"
    assert "obrigat" in r.pre_motivo.lower()


def test_obrigatorio_nunca_vira_sai_mesmo_se_ja_tenho():
    r = premarcar(_res(vinculacao="obrigatorio", ja_tenho=True))
    assert r.pre_marca == "fica"


def test_web_aberta_nunca_e_premarcada_fica():
    r = premarcar(_res(procedencia="web-aberta", vinculacao="aplicavel"))
    assert r.pre_marca == "sai"
    assert "web aberta" in r.pre_motivo.lower()


def test_contexto_nasce_desmarcado():
    r = premarcar(_res(vinculacao="contexto"))
    assert r.pre_marca == "sai"


def test_ja_tenho_nao_obrigatorio_nasce_desmarcado():
    r = premarcar(_res(vinculacao="aplicavel", ja_tenho=True))
    assert r.pre_marca == "sai"
    assert "acervo" in r.pre_motivo.lower()


def test_aplicavel_novo_de_fonte_catalogada_fica():
    r = premarcar(_res(vinculacao="aplicavel"))
    assert r.pre_marca == "fica"


def test_todo_resultado_sai_com_motivo_preenchido():
    rs = premarcar_todos([_res(), _res(vinculacao="contexto"),
                          _res(procedencia="web-aberta", vinculacao="contexto")])
    assert all(r.pre_motivo for r in rs)
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_premarcacao.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/premarcacao.py`:

```python
"""Pre-marcacao com justificativa (M4). A ordem das regras E a especificacao."""
from __future__ import annotations

from buscador.modelos import Resultado


def premarcar(r: Resultado) -> Resultado:
    # Trava 1 (spec 7): obrigatorio nunca e desmarcado, aconteca o que acontecer.
    if r.vinculacao == "obrigatorio":
        r.pre_marca, r.pre_motivo = "fica", "Vinculacao obrigatoria para a CD"
        return r
    # Trava 2 (spec 7): web aberta nunca nasce marcada.
    if r.procedencia == "web-aberta":
        r.pre_marca, r.pre_motivo = "sai", "Veio da web aberta: procedencia a conferir"
        return r
    if r.ja_tenho:
        r.pre_marca, r.pre_motivo = "sai", "Ja existe no acervo"
        return r
    if r.vinculacao == "contexto":
        r.pre_marca, r.pre_motivo = "sai", "Material de contexto, sem vinculacao direta"
        return r
    r.pre_marca, r.pre_motivo = "fica", "Aplicavel, de fonte catalogada, ainda nao no acervo"
    return r


def premarcar_todos(resultados: list[Resultado]) -> list[Resultado]:
    return [premarcar(r) for r in resultados]
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_premarcacao.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/premarcacao.py tests/test_premarcacao.py
git commit -m "feat: pre-marcacao com justificativa e as duas travas anti-ancoragem"
```

---

## Task 11: Orquestrador da busca

**Files:**
- Create: `buscador/busca.py`
- Test: `tests/test_busca.py`

**Interfaces:**
- Consumes: `Fonte`, `expandir`, `indexar`/`marcar_ja_tenho`, `premarcar_todos`, `db`
- Produces: `executar_busca(conn, tema: str, fontes: list[Fonte], acervo_raizes: list[Path], llm=None) -> int` (devolve `busca_id`), `resultados_da_busca(conn, busca_id) -> list[sqlite3.Row]`

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_busca.py`:

```python
from buscador.db import conectar, criar_schema
from buscador.busca import executar_busca, resultados_da_busca
from buscador.fontes.base import FonteFake


def _conn(tmp_path):
    c = conectar(tmp_path / "t.db")
    criar_schema(c)
    return c


def test_executar_busca_grava_busca_e_resultados(tmp_path):
    conn = _conn(tmp_path)
    fonte = FonteFake(nome="f1", itens=[("Lei nº 1", "https://x.gov.br/l1.htm")])
    bid = executar_busca(conn, "LGPD", [fonte], [])
    linhas = resultados_da_busca(conn, bid)
    assert len(linhas) == 1
    assert linhas[0]["titulo"] == "Lei nº 1"
    assert linhas[0]["pre_marca"] in ("fica", "sai")
    assert linhas[0]["pre_motivo"]


def test_executar_busca_deduplica_entre_fontes(tmp_path):
    conn = _conn(tmp_path)
    a = FonteFake(nome="a", itens=[("Lei nº 1", "https://x.gov.br/l1.htm")])
    b = FonteFake(nome="b", itens=[("Lei n. 1", "https://X.gov.br/l1.htm?q=2")])
    bid = executar_busca(conn, "LGPD", [a, b], [])
    assert len(resultados_da_busca(conn, bid)) == 1


def test_executar_busca_repassa_os_termos_expandidos_as_fontes(tmp_path):
    conn = _conn(tmp_path)
    f = FonteFake(nome="f", itens=[])
    executar_busca(conn, "LGPD", [f], [])
    assert len(f.chamadas[0]) > 1  # expandiu alem do tema cru


def test_fonte_que_quebra_nao_derruba_a_busca(tmp_path):
    conn = _conn(tmp_path)

    class FonteQuebrada:
        nome, procedencia = "ruim", "catalogada"
        vinculacao_padrao, categoria = "aplicavel", "x"

        def buscar(self, termos):
            raise RuntimeError("site fora do ar")

    boa = FonteFake(nome="boa", itens=[("Lei nº 2", "https://x.gov.br/l2.htm")])
    bid = executar_busca(conn, "tema", [FonteQuebrada(), boa], [])
    assert len(resultados_da_busca(conn, bid)) == 1


def test_ja_tenho_e_aplicado_a_partir_do_acervo(tmp_path):
    conn = _conn(tmp_path)
    acervo = tmp_path / "acervo"
    acervo.mkdir()
    (acervo / "Lei nº 1.pdf").write_text("x", encoding="utf-8")
    f = FonteFake(nome="f", itens=[("Lei nº 1", "https://x.gov.br/l1.htm")])
    bid = executar_busca(conn, "LGPD", [f], [acervo])
    assert resultados_da_busca(conn, bid)[0]["ja_tenho"] == 1
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_busca.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/busca.py`:

```python
"""Orquestrador: junta fontes, deduplica, marca ja-tenho, pre-marca e grava."""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from buscador.acervo import indexar, marcar_ja_tenho
from buscador.fontes.base import Fonte
from buscador.llm import LLM
from buscador.modelos import Resultado
from buscador.palavras_chave import expandir
from buscador.premarcacao import premarcar_todos

log = logging.getLogger(__name__)


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def executar_busca(conn: sqlite3.Connection, tema: str, fontes: list[Fonte],
                   acervo_raizes: list[Path], llm: LLM | None = None) -> int:
    termos = expandir(tema, llm)
    cur = conn.execute(
        "INSERT INTO buscas (tema, termos, criado_em) VALUES (?, ?, ?)",
        (tema, json.dumps(termos, ensure_ascii=False), _agora()),
    )
    busca_id = int(cur.lastrowid)

    brutos: list[Resultado] = []
    for fonte in fontes:
        try:
            brutos.extend(fonte.buscar(termos))
        except Exception:
            log.warning("fonte %s falhou; seguindo com as demais", fonte.nome,
                        exc_info=True)

    unicos: dict[str, Resultado] = {}
    for r in brutos:
        unicos.setdefault(r.chave_dedup, r)

    resultados = premarcar_todos(
        marcar_ja_tenho(list(unicos.values()), indexar(acervo_raizes))
    )

    conn.executemany(
        "INSERT OR IGNORE INTO resultados (busca_id, titulo, tipo, ano, ementa, url,"
        " fonte, procedencia, vinculacao, categoria, chave_dedup, ja_tenho,"
        " ja_tenho_onde, pre_marca, pre_motivo, coletado_em)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(busca_id, r.titulo, r.tipo, r.ano, r.ementa, r.url, r.fonte, r.procedencia,
          r.vinculacao, r.categoria, r.chave_dedup, int(r.ja_tenho), r.ja_tenho_onde,
          r.pre_marca, r.pre_motivo, _agora()) for r in resultados],
    )
    return busca_id


def resultados_da_busca(conn: sqlite3.Connection, busca_id: int) -> list[sqlite3.Row]:
    return list(conn.execute(
        "SELECT * FROM resultados WHERE busca_id = ? ORDER BY categoria, titulo",
        (busca_id,)))
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_busca.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/busca.py tests/test_busca.py
git commit -m "feat: orquestrador de busca resiliente a fonte quebrada"
```

---

## Task 12: Download, organização por tema e duplicatas

**Files:**
- Create: `buscador/download.py`
- Test: `tests/test_download.py`

**Interfaces:**
- Consumes: `db`, `sha256_arquivo`
- Produces: `caminho_longo(p: Path) -> str`, `pasta_do_tema(tema: str) -> str`, `baixar_selecionados(conn, busca_id, raiz_dados: Path, baixar_fn) -> RelatorioDownload`, `RelatorioDownload` (dataclass: `baixados: int`, `duplicatas: int`, `erros: list[tuple[str,str]]`)

Aqui mora a **mitigação obrigatória da B4**: dedup por sha256 com relatório, nunca duplicação silenciosa. E a trava dos 260 caracteres do Windows.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_download.py`:

```python
from pathlib import Path
from buscador.db import conectar, criar_schema
from buscador.busca import executar_busca
from buscador.fontes.base import FonteFake
from buscador.download import (baixar_selecionados, pasta_do_tema, caminho_longo)


def _prep(tmp_path, itens, decisao="fica"):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    bid = executar_busca(conn, "LGPD 2026", [FonteFake(nome="f", itens=itens)], [])
    conn.execute("UPDATE resultados SET decisao = ? WHERE busca_id = ?", (decisao, bid))
    return conn, bid


def test_pasta_do_tema_e_curta_e_sem_acento():
    p = pasta_do_tema("Levantamento sobre Governança de IA na Câmara dos Deputados")
    assert len(p) <= 32
    assert p == p.lower()
    assert " " not in p


def test_caminho_longo_prefixa_no_windows(tmp_path):
    assert caminho_longo(tmp_path / "x").endswith("x")


def test_baixa_so_o_que_foi_decidido_fica(tmp_path):
    conn, bid = _prep(tmp_path, [("A", "https://x/a.pdf"), ("B", "https://x/b.pdf")])
    conn.execute("UPDATE resultados SET decisao='sai' WHERE titulo='B'")
    rel = baixar_selecionados(conn, bid, tmp_path / "dados",
                              lambda url: b"conteudo-" + url.encode())
    assert rel.baixados == 1
    assert rel.duplicatas == 0


def test_detecta_duplicata_por_sha256_e_nao_regrava(tmp_path):
    conn, bid = _prep(tmp_path, [("A", "https://x/a.pdf"), ("B", "https://x/b.pdf")])
    rel = baixar_selecionados(conn, bid, tmp_path / "dados", lambda url: b"identico")
    assert rel.baixados == 1
    assert rel.duplicatas == 1
    assert conn.execute("SELECT COUNT(*) FROM arquivos").fetchone()[0] == 1


def test_erro_de_download_nao_interrompe_os_demais(tmp_path):
    conn, bid = _prep(tmp_path, [("A", "https://x/a.pdf"), ("B", "https://x/b.pdf")])

    def falha_no_a(url):
        if url.endswith("a.pdf"):
            raise RuntimeError("404")
        return b"ok"

    rel = baixar_selecionados(conn, bid, tmp_path / "dados", falha_no_a)
    assert rel.baixados == 1
    assert len(rel.erros) == 1


def test_grava_dentro_da_pasta_do_tema(tmp_path):
    conn, bid = _prep(tmp_path, [("A", "https://x/a.pdf")])
    baixar_selecionados(conn, bid, tmp_path / "dados", lambda url: b"x")
    assert list((tmp_path / "dados" / pasta_do_tema("LGPD 2026")).iterdir())
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_download.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/download.py`:

```python
"""Download e organizacao por tema, com dedup sha256 (mitigacao da decisao B4)."""
from __future__ import annotations

import hashlib
import logging
import re
import sqlite3
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import httpx

log = logging.getLogger(__name__)
MAX_PASTA = 32

BaixarFn = Callable[[str], bytes]


@dataclass
class RelatorioDownload:
    baixados: int = 0
    duplicatas: int = 0
    erros: list[tuple[str, str]] = field(default_factory=list)


def caminho_longo(p: Path) -> str:
    """Acima de 260 chars o Windows falha EM SILENCIO. O prefixo evita isso."""
    bruto = str(p.resolve())
    if len(bruto) > 240 and not bruto.startswith("\\\\?\\"):
        return "\\\\?\\" + bruto
    return bruto


def pasta_do_tema(tema: str) -> str:
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", tema)
                         if unicodedata.category(c) != "Mn")
    limpo = re.sub(r"[^0-9a-zA-Z]+", "-", sem_acento.lower()).strip("-")
    return limpo[:MAX_PASTA].rstrip("-")


def _nome_do_arquivo(url: str, sha: str) -> str:
    base = Path(urlsplit(url).path).name or "arquivo"
    sufixo = Path(base).suffix or ".bin"
    caule = Path(base).stem[:60] or "arquivo"
    return f"{caule}-{sha[:8]}{sufixo}"


def _http_get(url: str) -> bytes:
    r = httpx.get(url, timeout=60.0, follow_redirects=True)
    r.raise_for_status()
    return r.content


def baixar_selecionados(conn: sqlite3.Connection, busca_id: int, raiz_dados: Path,
                        baixar_fn: BaixarFn | None = None) -> RelatorioDownload:
    baixar_fn = baixar_fn or _http_get
    tema = conn.execute("SELECT tema FROM buscas WHERE id = ?",
                        (busca_id,)).fetchone()["tema"]
    destino = raiz_dados / pasta_do_tema(tema)
    destino.mkdir(parents=True, exist_ok=True)

    rel = RelatorioDownload()
    linhas = conn.execute(
        "SELECT id, url, titulo FROM resultados WHERE busca_id = ? AND decisao = 'fica'",
        (busca_id,)).fetchall()

    for linha in linhas:
        try:
            conteudo = baixar_fn(linha["url"])
        except Exception as exc:
            log.warning("falha ao baixar %s", linha["url"], exc_info=True)
            rel.erros.append((linha["titulo"], str(exc)))
            continue

        sha = hashlib.sha256(conteudo).hexdigest()
        ja = conn.execute("SELECT id FROM arquivos WHERE sha256 = ?", (sha,)).fetchone()
        if ja is not None:
            conn.execute("INSERT OR IGNORE INTO resultado_arquivo "
                         "(resultado_id, arquivo_id, duplicata) VALUES (?,?,1)",
                         (linha["id"], ja["id"]))
            rel.duplicatas += 1
            continue

        alvo = destino / _nome_do_arquivo(linha["url"], sha)
        with open(caminho_longo(alvo), "wb") as fh:
            fh.write(conteudo)
        cur = conn.execute(
            "INSERT INTO arquivos (sha256, caminho, tamanho, baixado_em) VALUES (?,?,?,?)",
            (sha, str(alvo), len(conteudo),
             datetime.now(timezone.utc).isoformat(timespec="seconds")))
        conn.execute("INSERT OR IGNORE INTO resultado_arquivo "
                     "(resultado_id, arquivo_id, duplicata) VALUES (?,?,0)",
                     (linha["id"], int(cur.lastrowid)))
        rel.baixados += 1

    conn.execute("UPDATE buscas SET pasta = ?, baixado_em = ? WHERE id = ?",
                 (str(destino),
                  datetime.now(timezone.utc).isoformat(timespec="seconds"), busca_id))
    return rel
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_download.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/download.py tests/test_download.py
git commit -m "feat: download com dedup sha256, pasta por tema e trava de 260 chars"
```

---

## Task 13: Planilha-registro

**Files:**
- Create: `buscador/planilha.py`
- Test: `tests/test_planilha.py`

**Interfaces:**
- Consumes: `db`
- Produces: `COLUNAS: list[str]`, `gerar_planilha(conn, busca_id, saida: Path) -> Path`

As 11 colunas da planilha atual do projeto **mais** as 6 de rastreabilidade da spec §6.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_planilha.py`:

```python
from openpyxl import load_workbook
from buscador.db import conectar, criar_schema
from buscador.busca import executar_busca
from buscador.fontes.base import FonteFake
from buscador.planilha import gerar_planilha, COLUNAS


def _prep(tmp_path):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    bid = executar_busca(conn, "LGPD", [FonteFake(
        nome="f", itens=[("Lei nº 1", "https://x.gov.br/l1.htm")])], [])
    conn.execute("UPDATE resultados SET decisao='fica' WHERE busca_id=?", (bid,))
    return conn, bid


def test_planilha_tem_todas_as_colunas_na_ordem(tmp_path):
    conn, bid = _prep(tmp_path)
    ws = load_workbook(gerar_planilha(conn, bid, tmp_path / "p.xlsx")).active
    assert [c.value for c in ws[1]] == COLUNAS


def test_colunas_de_rastreabilidade_estao_presentes():
    for c in ["URL", "Fonte", "Procedência", "Decisão", "Motivo da pré-marcação",
              "sha256", "Coletado em"]:
        assert c in COLUNAS


def test_planilha_registra_todos_os_resultados_inclusive_os_descartados(tmp_path):
    conn, bid = _prep(tmp_path)
    conn.execute("UPDATE resultados SET decisao='sai' WHERE busca_id=?", (bid,))
    ws = load_workbook(gerar_planilha(conn, bid, tmp_path / "p.xlsx")).active
    assert ws.max_row == 2  # cabecalho + 1 descartado: o registro guarda o descarte


def test_planilha_usa_fonte_arial(tmp_path):
    conn, bid = _prep(tmp_path)
    ws = load_workbook(gerar_planilha(conn, bid, tmp_path / "p.xlsx")).active
    assert ws["A1"].font.name == "Arial"
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_planilha.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/planilha.py`:

```python
"""Planilha-registro: o que foi achado, o que foi decidido e por que."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

COLUNAS = [
    "Nº", "Categoria", "Normativo", "Tipo", "Ano", "Ementa / Descrição",
    "Vinculação para a CD", "Status na Pasta", "Observações", "URL",
    "Fonte", "Procedência", "Pré-marcação", "Motivo da pré-marcação",
    "Decisão", "sha256", "Coletado em",
]
LARGURAS = [5, 22, 45, 18, 7, 55, 22, 16, 40, 55, 16, 14, 13, 38, 10, 20, 20]

CONSULTA = """
SELECT r.*, a.sha256 AS sha
FROM resultados r
LEFT JOIN resultado_arquivo ra ON ra.resultado_id = r.id
LEFT JOIN arquivos a ON a.id = ra.arquivo_id
WHERE r.busca_id = ?
ORDER BY r.categoria, r.titulo
"""


def gerar_planilha(conn: sqlite3.Connection, busca_id: int, saida: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Normativos"

    for i, (nome, largura) in enumerate(zip(COLUNAS, LARGURAS), start=1):
        c = ws.cell(row=1, column=i, value=nome)
        c.font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2F5496")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = largura
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUNAS))}1"

    for n, r in enumerate(conn.execute(CONSULTA, (busca_id,)), start=1):
        valores = [
            n, r["categoria"], r["titulo"], r["tipo"], r["ano"], r["ementa"],
            r["vinculacao"], "Já no acervo" if r["ja_tenho"] else "Novo",
            r["ja_tenho_onde"], r["url"], r["fonte"], r["procedencia"],
            r["pre_marca"], r["pre_motivo"], r["decisao"], r["sha"], r["coletado_em"],
        ]
        for col, valor in enumerate(valores, start=1):
            c = ws.cell(row=n + 1, column=col, value=valor)
            c.font = Font(name="Arial", size=10)
            c.alignment = Alignment(vertical="top", wrap_text=True)

    saida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(saida)
    return saida
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_planilha.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/planilha.py tests/test_planilha.py
git commit -m "feat: planilha-registro com colunas de rastreabilidade"
```

---

## Task 14: Web — página de triagem e ações de grupo

**Files:**
- Create: `buscador/web/app.py`, `buscador/web/templates/base.html`, `buscador/web/templates/triagem.html`
- Test: `tests/test_web_triagem.py`

**Interfaces:**
- Consumes: tudo anterior
- Produces: `criar_app(cfg: Config) -> FastAPI` com rotas `GET /busca/{id}` (triagem) e `POST /busca/{id}/decisoes` (grava)

Esta é a tela que resolve a dor. Mecanismo **M2** (decisão por grupo) mora aqui, e a mitigação de **B5** é o botão "desmarcar todos os já-tenho".

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_web_triagem.py`:

```python
from fastapi.testclient import TestClient
from buscador.config import Config
from buscador.db import conectar, criar_schema
from buscador.busca import executar_busca
from buscador.fontes.base import FonteFake
from buscador.web.app import criar_app


def _app(tmp_path):
    cfg = Config(raiz_dados=tmp_path, banco=tmp_path / "t.db")
    conn = conectar(cfg.banco)
    criar_schema(conn)
    bid = executar_busca(conn, "LGPD", [FonteFake(nome="f", itens=[
        ("Lei nº 1", "https://x.gov.br/l1.htm"),
        ("Lei nº 2", "https://x.gov.br/l2.htm")])], [])
    conn.close()
    return TestClient(criar_app(cfg)), bid


def test_pagina_de_triagem_lista_os_resultados(tmp_path):
    cli, bid = _app(tmp_path)
    r = cli.get(f"/busca/{bid}")
    assert r.status_code == 200
    assert "Lei nº 1" in r.text
    assert "Lei nº 2" in r.text


def test_pagina_mostra_o_motivo_da_premarcacao(tmp_path):
    cli, bid = _app(tmp_path)
    assert "Aplicavel, de fonte catalogada" in cli.get(f"/busca/{bid}").text


def test_pagina_traz_o_botao_de_desmarcar_ja_tenho(tmp_path):
    cli, bid = _app(tmp_path)
    assert 'data-acao="desmarcar-ja-tenho"' in cli.get(f"/busca/{bid}").text


def test_post_de_decisoes_grava_e_redireciona(tmp_path):
    cli, bid = _app(tmp_path)
    r = cli.post(f"/busca/{bid}/decisoes", data={"fica": ["1"]},
                 follow_redirects=False)
    assert r.status_code == 303
    from buscador.db import conectar as c2
    conn = c2(tmp_path / "t.db")
    linhas = {x["id"]: x["decisao"] for x in
              conn.execute("SELECT id, decisao FROM resultados")}
    assert linhas[1] == "fica"
    assert linhas[2] == "sai"


def test_busca_inexistente_devolve_404(tmp_path):
    cli, _ = _app(tmp_path)
    assert cli.get("/busca/999").status_code == 404
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_web_triagem.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar o app**

`buscador/web/app.py`:

```python
"""App web local. Sem autenticacao: roda em localhost, uso individual."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from buscador.config import Config
from buscador.db import conectar, criar_schema

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def criar_app(cfg: Config) -> FastAPI:
    app = FastAPI(title="Buscador de Base Normativa")
    app.state.cfg = cfg

    def conn():
        c = conectar(cfg.banco)
        criar_schema(c)
        return c

    @app.get("/busca/{busca_id}")
    def triagem(request: Request, busca_id: int):
        c = conn()
        busca = c.execute("SELECT * FROM buscas WHERE id = ?", (busca_id,)).fetchone()
        if busca is None:
            raise HTTPException(status_code=404, detail="busca nao encontrada")
        linhas = c.execute(
            "SELECT * FROM resultados WHERE busca_id = ? ORDER BY categoria, titulo",
            (busca_id,)).fetchall()
        grupos: dict[str, list] = {}
        for linha in linhas:
            grupos.setdefault(linha["categoria"] or "sem-categoria", []).append(linha)
        return TEMPLATES.TemplateResponse(request, "triagem.html", {
            "busca": busca, "grupos": grupos, "total": len(linhas)})

    @app.post("/busca/{busca_id}/decisoes")
    def gravar(busca_id: int, fica: list[int] = Form(default=[])):
        c = conn()
        agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
        c.execute("UPDATE resultados SET decisao='sai', decidido_em=? "
                  "WHERE busca_id=?", (agora, busca_id))
        if fica:
            marcas = ",".join("?" * len(fica))
            c.execute(f"UPDATE resultados SET decisao='fica', decidido_em=? "
                      f"WHERE busca_id=? AND id IN ({marcas})",
                      (agora, busca_id, *fica))
        c.execute("UPDATE buscas SET triado_em=? WHERE id=?", (agora, busca_id))
        return RedirectResponse(f"/busca/{busca_id}", status_code=303)

    return app
```

- [ ] **Step 4: Implementar os templates**

`buscador/web/templates/base.html`:

```html
<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>{% block titulo %}Buscador{% endblock %}</title>
<style>
 body{font-family:system-ui,sans-serif;margin:0;padding:0 24px 120px;background:#0d1117;color:#f0f6fc}
 h1{font-size:24px} .grupo{border:1px solid #26303b;border-radius:10px;margin:18px 0;padding:12px}
 .grupo h2{font-size:16px;margin:0 0 8px} .item{padding:8px;border-top:1px solid #1a222c}
 .motivo{color:#9ba3ad;font-size:13px} .selo{font-size:11px;border-radius:4px;padding:1px 6px;margin-left:6px}
 .selo.tenho{background:#3b2f14;color:#e8b84b} .selo.web{background:#3b1f1d;color:#e5534b}
 .barra{position:fixed;left:0;right:0;bottom:0;background:#141a22;border-top:1px solid #26303b;padding:12px 24px}
 button{background:#e8b84b;color:#0d1117;border:0;border-radius:8px;padding:8px 16px;font-weight:700;cursor:pointer}
 .acao{background:#26303b;color:#f0f6fc;font-weight:400;font-size:12px;padding:4px 10px}
</style></head>
<body>{% block corpo %}{% endblock %}</body></html>
```

`buscador/web/templates/triagem.html`:

```html
{% extends "base.html" %}
{% block titulo %}Triagem — {{ busca.tema }}{% endblock %}
{% block corpo %}
<h1>Triagem: {{ busca.tema }}</h1>
<p class="motivo">{{ total }} resultados. Pré-marcação sugerida pelo sistema —
confira e diverja onde discordar.</p>
<form method="post" action="/busca/{{ busca.id }}/decisoes">
 <p>
  <button type="button" class="acao" data-acao="marcar-todos">marcar todos</button>
  <button type="button" class="acao" data-acao="desmarcar-todos">desmarcar todos</button>
  <button type="button" class="acao" data-acao="desmarcar-ja-tenho">desmarcar todos os já-tenho</button>
  <button type="button" class="acao" data-acao="desmarcar-web">desmarcar web aberta</button>
 </p>
 {% for categoria, itens in grupos.items() %}
 <div class="grupo" data-categoria="{{ categoria }}">
  <h2>{{ categoria }} ({{ itens|length }})
   <button type="button" class="acao" data-acao="grupo-marcar">marcar grupo</button>
   <button type="button" class="acao" data-acao="grupo-desmarcar">desmarcar grupo</button>
  </h2>
  {% for r in itens %}
  <div class="item">
   <label>
    <input type="checkbox" name="fica" value="{{ r.id }}"
           data-ja-tenho="{{ 1 if r.ja_tenho else 0 }}"
           data-procedencia="{{ r.procedencia }}"
           {% if r.pre_marca == 'fica' %}checked{% endif %}>
    <b>{{ r.titulo }}</b>
    {% if r.ja_tenho %}<span class="selo tenho">já tenho</span>{% endif %}
    {% if r.procedencia == 'web-aberta' %}<span class="selo web">web aberta</span>{% endif %}
   </label>
   <div class="motivo">{{ r.ementa or '' }}</div>
   <div class="motivo">↳ {{ r.pre_motivo }} · <a href="{{ r.url }}" target="_blank">fonte</a></div>
  </div>
  {% endfor %}
 </div>
 {% endfor %}
 <div class="barra">
  <span id="contador"></span>
  <button type="submit">Gravar decisões</button>
 </div>
</form>
<script>
 const caixas = () => [...document.querySelectorAll('input[name=fica]')];
 function contar(){
   const n = caixas().filter(c => c.checked).length;
   document.getElementById('contador').textContent = n + ' de ' + caixas().length + ' marcados — ';
 }
 document.addEventListener('click', e => {
   const acao = e.target.dataset.acao;
   if (!acao) return;
   const grupo = e.target.closest('.grupo');
   if (acao === 'marcar-todos') caixas().forEach(c => c.checked = true);
   if (acao === 'desmarcar-todos') caixas().forEach(c => c.checked = false);
   if (acao === 'desmarcar-ja-tenho') caixas().forEach(c => { if (c.dataset.jaTenho === '1') c.checked = false; });
   if (acao === 'desmarcar-web') caixas().forEach(c => { if (c.dataset.procedencia === 'web-aberta') c.checked = false; });
   if (acao === 'grupo-marcar') grupo.querySelectorAll('input[name=fica]').forEach(c => c.checked = true);
   if (acao === 'grupo-desmarcar') grupo.querySelectorAll('input[name=fica]').forEach(c => c.checked = false);
   contar();
 });
 document.addEventListener('change', contar);
 contar();
</script>
{% endblock %}
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_web_triagem.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add buscador/web tests/test_web_triagem.py
git commit -m "feat: pagina de triagem com acoes de grupo (M2) e desmarcar ja-tenho"
```

---

## Task 15: Web — nova busca e aplicação do download

**Files:**
- Modify: `buscador/web/app.py`
- Create: `buscador/web/templates/inicio.html`
- Test: `tests/test_web_fluxo.py`

**Interfaces:**
- Consumes: `executar_busca`, `baixar_selecionados`, `gerar_planilha`
- Produces: rotas `GET /`, `POST /buscas`, `POST /busca/{id}/aplicar`

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_web_fluxo.py`:

```python
from fastapi.testclient import TestClient
from buscador.config import Config
from buscador.web.app import criar_app


def _cli(tmp_path, fontes=None):
    cfg = Config(raiz_dados=tmp_path, banco=tmp_path / "t.db")
    app = criar_app(cfg)
    if fontes is not None:
        app.state.fontes = fontes
    return TestClient(app), cfg


def test_inicio_lista_buscas_e_tem_formulario(tmp_path):
    cli, _ = _cli(tmp_path)
    r = cli.get("/")
    assert r.status_code == 200
    assert 'name="tema"' in r.text


def test_post_buscas_cria_e_redireciona_para_triagem(tmp_path):
    from buscador.fontes.base import FonteFake
    cli, _ = _cli(tmp_path, [FonteFake(nome="f", itens=[("A", "https://x/a.pdf")])])
    r = cli.post("/buscas", data={"tema": "LGPD"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/busca/1"


def test_aplicar_baixa_e_gera_planilha(tmp_path):
    from buscador.fontes.base import FonteFake
    cli, cfg = _cli(tmp_path, [FonteFake(nome="f", itens=[("A", "https://x/a.pdf")])])
    cli.post("/buscas", data={"tema": "LGPD"})
    cli.post("/busca/1/decisoes", data={"fica": ["1"]})
    app = cli.app
    app.state.baixar_fn = lambda url: b"conteudo"
    r = cli.post("/busca/1/aplicar", follow_redirects=False)
    assert r.status_code == 303
    assert (tmp_path / "planilhas" / "busca-1.xlsx").exists()


def test_aplicar_sem_triagem_devolve_400(tmp_path):
    from buscador.fontes.base import FonteFake
    cli, _ = _cli(tmp_path, [FonteFake(nome="f", itens=[("A", "https://x/a.pdf")])])
    cli.post("/buscas", data={"tema": "LGPD"})
    assert cli.post("/busca/1/aplicar").status_code == 400
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_web_fluxo.py -v`
Expected: FAIL — rotas `/` e `/buscas` não existem (404)

- [ ] **Step 3: Implementar as rotas novas**

Em `buscador/web/app.py`, dentro de `criar_app`, **antes** do `return app`, acrescente:

```python
    from buscador.busca import executar_busca
    from buscador.download import baixar_selecionados
    from buscador.planilha import gerar_planilha

    app.state.fontes = []
    app.state.baixar_fn = None

    @app.get("/")
    def inicio(request: Request):
        c = conn()
        buscas = c.execute("SELECT * FROM buscas ORDER BY id DESC").fetchall()
        return TEMPLATES.TemplateResponse(request, "inicio.html", {"buscas": buscas})

    @app.post("/buscas")
    def nova_busca(tema: str = Form(...)):
        c = conn()
        bid = executar_busca(c, tema, app.state.fontes, cfg.acervo_raizes)
        return RedirectResponse(f"/busca/{bid}", status_code=303)

    @app.post("/busca/{busca_id}/aplicar")
    def aplicar(busca_id: int):
        c = conn()
        busca = c.execute("SELECT * FROM buscas WHERE id=?", (busca_id,)).fetchone()
        if busca is None:
            raise HTTPException(status_code=404, detail="busca nao encontrada")
        if busca["triado_em"] is None:
            raise HTTPException(status_code=400, detail="triagem ainda nao gravada")
        baixar_selecionados(c, busca_id, cfg.raiz_dados, app.state.baixar_fn)
        gerar_planilha(c, busca_id, cfg.raiz_dados / "planilhas" / f"busca-{busca_id}.xlsx")
        return RedirectResponse(f"/busca/{busca_id}", status_code=303)
```

E adicione ao fim de `triagem.html`, dentro do bloco `corpo`, fora do `<form>`:

```html
<form method="post" action="/busca/{{ busca.id }}/aplicar">
  <button type="submit">Baixar e organizar o que ficou</button>
</form>
```

- [ ] **Step 4: Criar o template de início**

`buscador/web/templates/inicio.html`:

```html
{% extends "base.html" %}
{% block titulo %}Buscador de Base Normativa{% endblock %}
{% block corpo %}
<h1>Buscador de Base Normativa</h1>
<form method="post" action="/buscas">
  <input name="tema" placeholder="Tema da ação de controle" size="50" required>
  <button type="submit">Buscar</button>
</form>
<h2>Buscas anteriores</h2>
<ul>
{% for b in buscas %}
  <li><a href="/busca/{{ b.id }}">{{ b.tema }}</a>
      <span class="motivo">{{ b.criado_em }}{% if b.triado_em %} · triada{% endif %}
      {% if b.baixado_em %} · baixada{% endif %}</span></li>
{% else %}
  <li class="motivo">nenhuma busca ainda</li>
{% endfor %}
</ul>
{% endblock %}
```

- [ ] **Step 5: Rodar a suíte inteira**

Run: `py -m pytest -v`
Expected: todos passam

- [ ] **Step 6: Commit**

```bash
git add buscador/web tests/test_web_fluxo.py
git commit -m "feat: fluxo web completo (nova busca, triagem, aplicar)"
```

---

## Task 16: CLI, registro das fontes e README

**Files:**
- Create: `buscador/cli.py`, `README.md`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: tudo
- Produces: `fontes_padrao(cfg) -> list[Fonte]`, `main(argv: list[str] | None = None) -> int`

Comandos: `buscador servir` (sobe o app com as fontes reais) e `buscador buscar "<tema>"` (headless, para script).

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_cli.py`:

```python
import pytest
from buscador.cli import main, fontes_padrao
from buscador.config import Config


def test_fontes_padrao_traz_as_tres_catalogadas(tmp_path):
    nomes = {f.nome for f in fontes_padrao(Config(raiz_dados=tmp_path,
                                                  banco=tmp_path / "t.db"))}
    assert {"planalto", "legin-camara", "tcu"} <= nomes


def test_main_sem_argumentos_devolve_2_e_mostra_uso(capsys):
    assert main([]) == 2
    assert "uso" in capsys.readouterr().out.lower()


def test_main_com_comando_desconhecido_devolve_2(capsys):
    assert main(["inventado"]) == 2
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_cli.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/cli.py`:

```python
"""CLI. `servir` sobe a interface; `buscar` roda headless para script."""
from __future__ import annotations

import argparse
import sys

from buscador.busca import executar_busca
from buscador.config import Config, carregar_config
from buscador.db import conectar, criar_schema
from buscador.fontes.base import Fonte
from buscador.fontes.legin_camara import FonteLegin
from buscador.fontes.planalto import FontePlanalto
from buscador.fontes.tcu import FonteTCU


def fontes_padrao(cfg: Config) -> list[Fonte]:
    return [FontePlanalto(), FonteLegin(), FonteTCU()]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    p = argparse.ArgumentParser(prog="buscador", add_help=True)
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("servir").add_argument("--porta", type=int, default=8077)
    sub.add_parser("buscar").add_argument("tema")

    if not argv:
        print("uso: buscador [servir|buscar] ...")
        return 2
    args = p.parse_args(argv)
    if args.cmd is None:
        print("uso: buscador [servir|buscar] ...")
        return 2

    cfg = carregar_config()
    if args.cmd == "servir":
        import uvicorn
        from buscador.web.app import criar_app
        app = criar_app(cfg)
        app.state.fontes = fontes_padrao(cfg)
        uvicorn.run(app, host="127.0.0.1", port=args.porta)
        return 0

    conn = conectar(cfg.banco)
    criar_schema(conn)
    bid = executar_busca(conn, args.tema, fontes_padrao(cfg), cfg.acervo_raizes)
    print(f"busca {bid} criada; abra http://127.0.0.1:8077/busca/{bid}")
    return 0
```

- [ ] **Step 4: Escrever o README**

`README.md`:

```markdown
# Buscador de Base Normativa

Monta o acervo de critério de uma ação de controle: pesquisa um tema em fontes
catalogadas e na web aberta, entrega uma lista **triável em poucas decisões**, e baixa
e organiza só o que sobreviveu à triagem.

## Instalação

    py -m venv .venv && .venv/Scripts/pip install -e ".[dev]"

## Uso

    buscador servir            # http://127.0.0.1:8077
    buscador buscar "LGPD"     # headless

## Configuração (variáveis de ambiente)

| Variável | Efeito |
|---|---|
| `BUSCADOR_DADOS` | raiz dos dados (padrão `dados`) |
| `BUSCADOR_ACERVO` | acervos existentes p/ o selo "já tenho", separados por `;` |
| `BUSCADOR_LLM_URL` | endpoint OpenAI-compatível; **sem isso o sistema roda igual** |
| `BUSCADOR_LLM_MODELO` | nome do modelo |
| `BUSCADOR_LLM_CHAVE` | chave, quando a API exigir |

## Como a triagem economiza decisões

1. **Já tenho** — cruza com o acervo existente e marca o que é redundante
2. **Grupo** — decide categoria inteira de uma vez
3. **Vinculação** — "contexto" nasce desmarcado
4. **Pré-marcação** — sugestão com motivo; você confirma ou diverge

⚠ A pré-marcação é **sugestão do sistema**, não julgamento validado. Duas travas
impedem que ela decida sozinha: item `obrigatorio` nunca nasce desmarcado, e nada vindo
da web aberta nasce marcado.

## Rastreabilidade

Toda linha guarda fonte, procedência, URL, sha256 do arquivo, data da coleta, a decisão
humana e o motivo da pré-marcação — inclusive quando você divergiu. Título e ementa são
copiados **literalmente** da fonte; texto de LLM vai para coluna separada.
```

- [ ] **Step 5: Rodar a suíte inteira**

Run: `py -m pytest -v`
Expected: todos passam

- [ ] **Step 6: Commit**

```bash
git add buscador/cli.py README.md tests/test_cli.py
git commit -m "feat: CLI, registro das fontes reais e README"
```

---

## Self-Review

**Cobertura da spec:**

| Requisito | Task |
|---|---|
| §2 M1 já-tenho | 9, 14 |
| §2 M2 grupo | 14 |
| §2 M3 vinculação | 10 |
| §2 M4 pré-marcação | 10 |
| §4 B1 híbrido de fontes | 5, 6, 7 |
| §4 B2 app web | 14, 15 |
| §4 B3 LLM opcional | 8 |
| §4 B4 pasta por tema | 12 |
| §4 B5 mostrar já-tenho | 14 |
| Mitigação B4 (dedup sha256) | 12 |
| Mitigação B5 (ação de grupo) | 14 |
| §6 rastreabilidade | 2, 13 |
| §7 travas anti-ancoragem | 10 |
| §7 260 chars | 12 |
| §8 roda sem LLM | 8 |

**Consistência de tipos:** `chave_dedup` (3) usada em 4-7, 11 · `Resultado` (3) produzido por todas as fontes · `conectar`/`criar_schema` (2) usados em 11-15 · `premarcar_todos` (10) chamado em 11 · `baixar_selecionados`/`gerar_planilha` (12, 13) chamados em 15 · `fontes_padrao` (16) alimenta `app.state.fontes` de 15.

**Sem placeholders:** todo passo traz código real; nenhum "similar à Task N".

---

## Riscos de execução conhecidos

1. **Os seletores CSS das Tasks 5-7 são suposição.** Planalto, Legin e TCU podem usar
   outra marcação. As fixtures deixam o teste verde mesmo se o seletor estiver errado
   **para o site real**. Ao implementar: baixe uma página real, confirme o seletor, e
   **substitua a fixture pela página real**. Se o seletor mudar, o teste de contrato
   quebra ruidosamente — que é o desenho.
2. **A rota de busca de cada fonte** (`/busca?q=`, `/legin/busca?termo=`) precisa ser
   confirmada contra o site. Só `extrair()` está coberto por teste; `buscar()` toca rede.
3. **A web aberta não tem provedor definido.** A Task 7 recebe a função por injeção de
   propósito: escolher o provedor é uma decisão sua, não deste plano.
