# llm_cadeia — LLM com fallback entre provedores (pasta copiável)

> ⛔ **29/09/2026 — ORIGEM EM MUDANÇA:** a origem deste módulo passa para o repo privado `rodilpinto/nuati-framework`
> (decisões D-C23/D-C24 no `_DECISOES-PENDENTES.md` do buscador). Esta pasta fica **congelada** na 1.0.1: não edite aqui;
> quando o framework existir, pegue o módulo de lá. O texto abaixo descreve a 1.0.1 como estava.

**Versão 1.0.1** · **Origem (até 29/09):** `buscador-normativos/levantamento-normativos/llm_cadeia/` (repo
`github.com/rodilpinto/buscador-normativos`). Spec: `docs/superpowers/specs/2026-09-28-llm-cadeia-portatil-design.md`.

Um jeito só de chamar LLM em todas as soluções do Nuati. Tenta, em ordem, até alguém responder:

```
chave do usuário (digitada na tela, só na sessão dele)
  → local   (Gemma do servidor do Nuati, OpenAI-compatível)
  → gemini → gemini-2 → groq → groq-2 → cerebras → cerebras-2 → openrouter → openrouter-2
```

Cada provedor tem uma **lista de modelos**. Cota ou sobrecarga num modelo → tenta o próximo modelo do mesmo
provedor (a cota do Gemini é por projeto **e por modelo**). Chave inválida ou rede fora → pula o provedor.
Sem nenhum provedor configurado, `gerar` devolve `texto=None` e o app segue sem LLM. **Nunca levanta exceção.**

## Adotar num app (5 passos)

1. **Copie a pasta inteira** `llm_cadeia/` para a raiz do código do app (ao lado do `app.py`).
   No topo deste README da cópia, acrescente: `Copiado de buscador-normativos @ <commit> em <data>`.
2. **Dependências** no `requirements.txt`: `requests` e `google-genai` (sem este, os provedores Gemini somem).
3. **Segredos** em `.streamlit/secrets.toml` (local/servidor) ou em *Secrets* do Streamlit Cloud — tabela abaixo.
   Mudou Secrets na nuvem → **Reboot app** (são lidos no import).
4. **Troque a chamada ao LLM** por `gerar` (exemplos abaixo). Mantenha os prompts e a validação do app.
5. **Barra lateral** (opcional, recomendado): `painel_llm()` — ver abaixo. Rode `python -m llm_cadeia` e
   `python -m pytest llm_cadeia/test_llm_cadeia.py -q`.

## Usar

```python
from llm_cadeia import gerar

r = gerar(prompt, sistema="Você é um auditor...", json=True, temperatura=0.0, max_tokens=2048)
if r.texto is None:
    st.error("IA indisponível agora:\n" + "\n".join(r.tentativas))   # tentativas nunca contém chave
else:
    dados = MeuSchema.model_validate_json(r.texto)   # validar continua sendo do app
    st.caption(f"Gerado por {r.origem}")              # rastreabilidade: quem respondeu
```

| Parâmetro | Efeito |
|---|---|
| `sistema` | Gemini: `system_instruction`. Demais: mensagem `system`. |
| `json=True` | Gemini devolve JSON puro (`response_mime_type`). Demais: **peça JSON no prompt**; a cerca ```` ```json ```` é retirada. |
| `max_tokens` | Piso de 4096: modelos que "pensam" (gemini-2.5-flash, gemma-4, gpt-oss, qwen) devolvem **vazio** com orçamento pequeno. |

Resposta vazia **não** troca de modelo (volta `texto=None` com `origem` preenchida): trocar em silêncio misturaria modelos.

**Barra lateral** — tem de rodar **antes** de qualquer `gerar` (a barra lateral roda no topo do script):

```python
from llm_cadeia.painel_streamlit import painel_llm
with st.sidebar:
    painel_llm()          # campo "Usar minha própria chave de IA" + status da cadeia
```

A chave digitada pelo usuário fica só no `st.session_state` daquela sessão — nunca em disco, log, variável de
módulo nem para outros usuários — e vai na frente de todas.

"Última resposta: provedor (modelo)" é atualizada na **mesma** execução do script, logo depois do `gerar`
(o painel instala o gancho `ao_responder` no contexto da sessão); não precisa de `st.rerun()`.

**OpenAI paga:** não é segredo do app. O usuário escolhe "Outro (compatível com OpenAI)", URL base
`https://api.openai.com/v1`, modelo (ex.: `gpt-5-mini`) e a própria chave. Modelos de raciocínio da OpenAI
recusam `max_tokens` e `temperature` ≠ 1: o transporte repete a chamada uma vez com `max_completion_tokens` e
sem `temperature`. ⚠ Coberto por teste com dublê; não verificado ao vivo (sem chave OpenAI em 28/09).

## Segredos (iguais em todos os apps)

| Segredo | Provedor | Onde conseguir |
|---|---|---|
| `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` (opcional) | `local` | Gemma do Nuati: `http://10.10.111.125:1234/v1` — **só alcançável de dentro da rede da Câmara** |
| `GEMINI_API_KEY`, `GEMINI_API_KEY_2` | `gemini`, `gemini-2` | aistudio.google.com/apikey |
| `GROQ_API_KEY`, `GROQ_API_KEY_2` | `groq`, `groq-2` | console.groq.com/keys |
| `CEREBRAS_API_KEY`, `CEREBRAS_API_KEY_2` | `cerebras`, `cerebras-2` | cloud.cerebras.ai |
| `OPENROUTER_API_KEY`, `OPENROUTER_API_KEY_2` | `openrouter`, `openrouter-2` | openrouter.ai/keys |
| `GEMINI_MODELS`, `GROQ_MODELS`, … | troca a lista de modelos do serviço (vírgulas) | — |
| `LLM_ORDEM` | troca a ordem, ex. `"gemini-2,gemini,groq"` (omitidos vão para o fim) | — |

📝 Convenção sugerida: **sem sufixo = nuati.secin**, **`_2` = rodilpinto**. Segunda chave Gemini só soma cota se
for de **outro projeto** Google (a cota é por projeto, não por chave).

| Onde roda | Segredos |
|---|---|
| Servidor do Nuati | `LLM_BASE_URL` + `LLM_MODEL` + as chaves gratuitas (fallback) |
| Streamlit Cloud (portfólio) | só as chaves gratuitas — **sem** `LLM_BASE_URL` (a nuvem não alcança a intranet) |

Modelos padrão e limites gratuitos (conferidos nas docs em 25/09/2026): `PRESETS` e `GEMINI_MODELOS_PADRAO` em
`nucleo.py`.

## Diagnóstico

```bash
python -m llm_cadeia      # da pasta que contém llm_cadeia/
```

Uma chamada mínima por modelo de cada provedor configurado; imprime `provedor  modelo  ok|motivo`. Use ao
configurar um servidor novo — gasta 1 requisição por modelo.

## Esperas após falha

| Falha | Para | Por quanto tempo |
|---|---|---|
| 429 diário | o modelo | até a meia-noite do Pacífico (reset do Gemini) |
| 429 por minuto, 5xx, sobrecarga | o modelo | 60 s |
| 404 (modelo não existe para a chave) | o modelo | 6 h |
| 401/403, chave inválida | o provedor | 6 h |
| rede / timeout | o provedor | 5 min |
| outro | o modelo | 5 min |

As esperas valem por processo (reiniciar o app zera).

## Regra de sincronia

**Não edite uma cópia.** Melhoria nasce na origem, sobe `__version__` (`__init__.py`), entra no changelog abaixo e
é recopiada para os apps. Divergência entre cópias = bug.

## Instrução para colar na sessão de outro app

> Adote o módulo de LLM compartilhado. Leia `C:\Users\Rodrigo\Documents\solucoes\buscador-normativos\levantamento-normativos\llm_cadeia\README.md`
> e siga "Adotar num app": copie a pasta `llm_cadeia/` inteira para junto do `app.py` deste projeto, sem editá-la;
> troque as chamadas diretas ao Gemini/OpenAI por `llm_cadeia.gerar` (mantendo prompts e validação; use
> `sistema=` e `json=True` onde couber); ponha `painel_llm()` na barra lateral; renomeie os segredos para os
> nomes da tabela; rode `python -m pytest llm_cadeia/test_llm_cadeia.py -q` e `python -m llm_cadeia`.
> Se precisar de algo que o módulo não faz, NÃO altere a cópia: registre o pedido para a origem.

## Changelog

- **1.0.1 (28/09/2026)** — achados da adoção no `scopediagram` (rede da Câmara):
  - **Verificado ao vivo:** `local` (`google/gemma-4`, LM Studio do Nuati) com `sistema=` + `json=True` →
    JSON sem cerca, `json.loads` OK, acentos corretos (11,8 s); extração IGOE completa passou no pydantic (~48 s).
    A rede da Câmara deixa passar gemini, groq, cerebras e openrouter.
  - `painel_llm()` atualiza "Última resposta" na mesma execução (gancho `ao_responder` no contexto; erro no
    gancho nunca derruba o `gerar`).
  - OpenAI (modelos de raciocínio): 400 por `max_tokens`/`temperature` → 1 repetição com `max_completion_tokens`
    e sem `temperature`. ⚠ Só teste com dublê.
  - Docstrings desatualizadas corrigidas (`gerar` devolve `Resposta`; presets já verificados com chave real).
  - ⚠ Chave Gemini criada em set/2026 recebe 404 em `gemini-2.5-flash(-lite)` ("no longer available to new
    users"); a lista padrão já cai para 3.x, mas app que fixar `gemini-2.5-flash` quebra com chave nova.

- **1.0.0 (28/09/2026)** — vira pasta copiável (de `llm/cadeia.py` do buscador). `gerar` devolve `Resposta`
  (`texto`, `origem`, `tentativas`); `sistema=`, `json=`; segunda chave `_2` para todo serviço; `painel_llm()`;
  `python -m llm_cadeia`; piso de 4096 tokens também no Gemini (medido: 16 tokens → resposta vazia).
  **Verificado ao vivo (28/09):** gemini, gemini-2, groq, cerebras e openrouter respondem; `sistema=` + `json=True`
  devolvem JSON que passa em `json.loads` nos 5. ⚠ Não verificado: `local` (Gemma do Nuati — inalcançável desta máquina).
- 25/09 — rodízio de modelos, Groq/Cerebras/OpenRouter, chave do usuário por sessão.
- 23/09 — cadeia A (local) > B (Gemini) > C (Gemini 2).
