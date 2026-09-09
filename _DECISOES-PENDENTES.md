---
title: "Decisões abertas — Buscador de Base Normativa"
maintained_by: sessões do Claude Code; só o Rodrigo resolve
last_updated: 2026-09-09
related: [_TODO.md, SESSION-ONBOARD-buscador.md, log.md]
---

# Decisões — o que espera o humano

> Status: 🔴 ABERTA · 🟡 EM ANÁLISE · 🟢 DECIDIDA.
> Sugestões aqui são propostas, não fatos validados — marcadas com 📝.

---

## 🔴 D-B1 — Qual provedor de busca para a web aberta?

- **Onde aparece:** Task 7 do plano (`buscador/fontes/web_aberta.py`)

**A questão.** A fonte de web aberta recebe a função de busca **por injeção**, justamente
para não travar o desenvolvimento. Mas para rodar contra a web de verdade é preciso escolher
um provedor.

**Opções e trade-offs** (📝 análise do assistente, sem medição):

| Opção | Ganha | Perde / risco |
|---|---|---|
| API de busca paga (Brave, Serper, Tavily) | resultado limpo, estável, sem scraping | custo por consulta; chave a gerenciar |
| Scraping de motor público | sem custo | frágil, bloqueio por robô, terreno cinzento |
| Só fontes catalogadas (sem web aberta) | simplicidade; procedência sempre forte | perde a rede de segurança que a decisão B1 escolheu |

**Recomendação (📝 sugestão):** API paga, se houver orçamento — é a única que não vira
manutenção recorrente. Se não houver, adiar a web aberta e rodar só com as catalogadas: o
desenho já suporta, e nada quebra.

**Trava:** nada do desenvolvimento (a injeção resolve). Trava **rodar contra a web real**.

**Decisão tomada:** _(pendente)_

---

## 🔴 D-B2 — Confirmar as rotas e seletores das fontes catalogadas

- **Onde aparece:** Tasks 5, 6 do plano

**A questão.** As rotas (`/busca?q=`, `/legin/busca?termo=`) e os seletores CSS
(`div.resultado`, `ul.lista-resultados li`, `div.item-resultado`) são **suposição do plano**.
As fixtures são sintéticas, então os testes passam mesmo se estiverem errados para os sites
reais.

**Não é bem uma escolha, é uma verificação** — mas precisa de alguém com acesso à web e
5 minutos por site. Enquanto não for feita, `extrair()` está verificado e `buscar()` **não**.

**Trava:** a confiabilidade das Tasks 5 e 6. O desenvolvimento pode seguir; o uso real, não.

**Decisão tomada:** _(pendente)_

---

## 🟢 Decididas no brainstorm de 2026-09-08

Detalhe completo na spec §4 (`docs/superpowers/specs/2026-09-08-buscador-normativos-design.md`).

- **B1 · Fontes:** híbrido — catalogadas primeiro, web aberta como rede de segurança, com
  procedência marcada por resultado.
- **B2 · Arquitetura:** app web local (FastAPI + SQLite). Descartados CLI-only e Streamlit.
- **B3 · LLM:** híbrido — o sistema roda **inteiro sem LLM**; quando configurado, ele
  enriquece palavras-chave e ementas. Adaptador OpenAI-compatível serve nuvem e LLM local.
- **B4 · Organização:** por tema/ação de controle, uma pasta por busca.
  ⚠ **Tensão registrada e aceita:** recria a duplicação de arquivos que a consolidação de
  2026-08-05 desfez no `referencias/`. **Mitigação obrigatória:** dedup por sha256 com
  detecção e relatório — nunca duplicação silenciosa (Task 12).
- **B5 · Já-tenho:** mostrar todos os resultados com selo, nada é ocultado.
  ⚠ **Tensão registrada e aceita:** infla a contagem de decisões, contra o princípio da
  spec §2. **Mitigação obrigatória:** ação de grupo "desmarcar todos os já-tenho" (Task 14).
- **Escopo do repo:** projeto novo em `~/Documents/solucoes/`, não dentro do
  `checklist-conformidade` nem do `projetos-nuati`.

## ⚠ Decisão do repo-pai que este projeto reverte

**D-AI-01** (`projetos-nuati/projeto-AI-com-IA/decisions/`) dizia "nesta rodada não se
constrói nada". Construir o buscador **reverte isso** — decisão do Rodrigo em 08/09, já
registrada no `DECISIONS-LOG.md` daquela área.
