# LESSONS — Buscador de Base Normativa

<!-- Append-only. Entradas mais recentes no topo. Formato: Problema / Causa-raiz / Conserto / Regra.
     Lição de MÁQUINA (vale em qualquer projeto) vai para ~/.claude/ENVIRONMENT.md, e aqui fica só
     um ponteiro de uma linha. Lição de ÁREA fica no runbook da área. Aqui: as transversais. -->

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

**Conserto.** ⛔ **Nenhum ainda** — achado desta sessão, registrado antes de qualquer mudança de
código (a Fase 1 não começou; o golden-master ainda não existe). Entra como insumo obrigatório do
**B-04** (medir a lacuna de cobertura) e como candidato a task da Fase 2.

**Regra.** **Degradação graciosa sem sinalização é perda de informação, não robustez.** Toda fonte
que falha por bloqueio, 5xx ou resposta não-parseável tem de aparecer na UI como **fonte
indisponível**, distinta de **fonte sem resultado**. E antes de aceitar "a busca não achou nada",
bater no endpoint com `curl` e olhar o `content-type`: HTTP 200 **não** significa que veio o que
se pediu.

**Cobertura.** ✅ Medido em 2026-09-22 contra LexML (3 URLs) e TCU (2 endpoints), por `curl` e
pelos searchers reais. ⚠ **Google/DuckDuckGo não foram medidos** nesta sessão — a via da web
aberta (D-B1) segue não verificada, e é justamente ela que deveria compensar a lacuna.

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
- Bloqueios que dependem do humano: `BLOCKED-ON-RODRIGO.md`.
- Decisões: `_DECISOES-PENDENTES.md` e `decisions/DECISIONS-LOG.md`.
