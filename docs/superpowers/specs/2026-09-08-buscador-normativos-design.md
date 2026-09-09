# Buscador de Base Normativa — Design

**Data:** 2026-09-08 · **Origem:** brainstorm da área `ai-com-ia` (projeto "Auditoria Interna
apoiada por IA", Secin/Nuati) · **Repo:** `~/Documents/solucoes/buscador-normativos/`

## 1. Problema

Montar o acervo de critério de uma ação de controle é hoje um processo **conversacional**: um
humano pede a um LLM que pesquise um tema, o LLM devolve uma lista, e alguém baixa e organiza os
arquivos à mão. O único código que sobrou desse processo é um **formatador** —
`referencias/_apendices-e-scripts/gerar_planilha_normativos.py`, que renderiza em `.xlsx` uma lista
de ~30 normativos **escrita à mão dentro do próprio fonte**. Não há busca, download nem
organização automatizados (verificado por leitura em 2026-09-08: nenhuma chamada de rede nos
scripts).

**A dor concreta, relatada pelo usuário:** a primeira busca do levantamento LGPD trouxe **mais de
100 normativos**, quantidade "inviável de usar por um humano", exigindo uma "super filtragem"
posterior e manual.

O problema não é buscar. É **triar**.

## 2. Princípio de desenho

> Reduzir o **número de decisões** do humano, não embelezar cada decisão.

Cem checkboxes continuam sendo cem decisões. Quatro mecanismos atacam a contagem:

| # | Mecanismo | Efeito |
|---|---|---|
| M1 | Selo **já tenho** (acervo + wiki) | tira do caminho o que é redundante |
| M2 | Decisão **por grupo**, com desce-ao-item só quando o grupo é misto | 21 itens → 1 decisão |
| M3 | Eixo **"Vinculação para a CD"** (obrigatório / aplicável / contexto) | "contexto" nasce desmarcado |
| M4 | **Pré-marcação com justificativa**, humano confirma ou diverge | varredura, não julgamento item a item |

⚠ **M4 carrega risco de ancoragem** — ver §7.

## 3. Escopo

**Entra:** tema → palavras-chave → busca híbrida → normalização → dedup e selo já-tenho →
pré-marcação → triagem humana na web → download → organização por tema → planilha-registro.

**Não entra (YAGNI):** indexação semântica, chat sobre o acervo, extração de dispositivos,
geração de checklist. As duas últimas já existem (`/analise-normativa`); as duas primeiras são
o `wiki-chat`, projeto distinto — ele **consome** acervo, este **constrói**.

## 4. Decisões tomadas no brainstorm

| Código | Decisão | Escolha |
|---|---|---|
| B1 | Fontes | **Híbrido**: catalogadas primeiro, web aberta como rede de segurança, procedência marcada por resultado |
| B2 | Arquitetura | **App web local** (FastAPI + SQLite), não CLI-only nem Streamlit |
| B3 | LLM | **Híbrido**: funciona 100% sem LLM; quando configurado, enriquece palavras-chave e ementas |
| B4 | Organização | **Por tema/ação de controle** (uma pasta por busca) |
| B5 | Já-tenho | **Mostrar todos**, com selo; nada é ocultado |

**Tensões registradas, aceitas pelo usuário:**

- **B4 recria a duplicação de arquivos** que a consolidação de 2026-08-05 desfez (as três pastas
  `referencias-levantamento-*`). **Mitigação obrigatória:** dedup por `sha256` com detecção e
  relatório de duplicata entre temas — nunca duplicação silenciosa.
- **B5 infla a contagem de decisões**, contra o princípio da §2. **Mitigação obrigatória:** ações
  de grupo, entre elas "desmarcar todos os já-tenho" em um clique.

## 5. Arquitetura

```
tema ──► palavras_chave ──► fontes/* ──► busca ──► [SQLite]
                                                      │
                              acervo (índice sha256) ─┤
                                                      ▼
                                              premarcacao
                                                      │
                                                      ▼
                                        web: página de triagem
                                          (grupos, ações em massa)
                                                      │
                                            decisões gravadas
                                                      ▼
                                    download ──► organização por tema
                                                      │
                                                      ▼
                                              planilha-registro
```

Cada etapa é **retomável**: o estado vive no banco, não em memória de processo. Uma busca
interrompida no download é retomada sem refazer busca nem triagem.

## 6. Rastreabilidade (requisito de essência, não de conveniência)

Toda linha do resultado carrega, obrigatoriamente:

1. **Fonte** — qual adaptador a produziu (`planalto`, `legin-camara`, `tcu`, `anpd`, `web-aberta`)
2. **Procedência** — `catalogada` ou `web-aberta`; a segunda nasce marcada "a conferir"
3. **URL original**, preservada literalmente
4. **sha256** do arquivo baixado, quando houver download
5. **Data da coleta**
6. **Decisão humana** (`fica` / `sai`), com autor implícito e timestamp
7. **Motivo da pré-marcação**, preservado mesmo quando o humano diverge

Ementa e título são **copiados literalmente da fonte**. Quando o LLM opcional gerar um resumo,
ele vai para campo **separado**, marcado como derivado, jamais sobrescrevendo o texto da fonte.
Nenhum texto normativo é parafraseado em campo algum.

## 7. Riscos

| Risco | Mitigação |
|---|---|
| **Ancoragem** pela pré-marcação (M4) | motivo sempre visível; contador de "divergi da sugestão" na tela; a pré-marcação nunca desmarca item `obrigatório` |
| Duplicação de arquivo entre temas (B4) | dedup sha256 + relatório de duplicata |
| Web aberta traz fonte ruim | procedência marcada; web aberta nunca é pré-marcada `fica` |
| Fonte muda de HTML e o adaptador quebra em silêncio | cada adaptador tem fixture salva e teste de contrato; falha é ruidosa |
| Caminho > 260 chars no Windows | nomes de pasta curtos + prefixo `\\?\`; teste dedicado |

## 8. Critérios de sucesso

1. Uma busca de tema real devolve resultados com procedência, **sem intervenção manual**.
2. Uma lista de 100+ resultados é triável em **menos de 15 decisões humanas** graças a M1-M4.
3. O download organiza por tema e **detecta** arquivo já baixado em outro tema.
4. A planilha final reproduz as colunas da planilha atual do projeto (Nº, Categoria, Normativo,
   Tipo, Ano, Ementa, Vinculação, Dimensão TCU, Status, Observações, URL) **mais** as colunas de
   rastreabilidade da §6.
5. O sistema roda **inteiro sem LLM configurado**.
