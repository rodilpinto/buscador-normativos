# `llm_cadeia` — módulo de LLM portátil (copiar e colar) — design

**Data:** 2026-09-28 · **Status:** aprovado pelo Rodrigo em 28/09 ("yes, looks right — commit and go ahead")
**Ponto de partida:** `levantamento-normativos/llm/cadeia.py` (commit `de9f616`).

## 1. Problema

Várias soluções Streamlit do Nuati chamam LLM, cada uma do seu jeito:

| App | Hoje (lido em 28/09) |
|---|---|
| buscador-normativos | cadeia de provedores (`llm/cadeia.py`) |
| `projeto-nuati-diagrama-de-escopo/llm.py` | Gemini `2.5-flash` **ou** OpenAI; saída JSON validada por schema pydantic; mensagem de sistema |
| `projetos-nuati-checklist/checklist-app/lib/llm.py` | Gemini `2.5-flash` fixo, sem fallback |

Destino final: **servidor do Nuati** (alcança o Gemma local). Uma cópia fica no **Streamlit Cloud** como portfólio
(não alcança o Gemma). Queremos UMA forma de chamar LLM, com fallback entre várias chaves gratuitas (dois logins:
nuati.secin e rodilpinto) e a chave do próprio usuário na frente de tudo.

## 2. Decisão de distribuição

**Copiar e colar uma pasta**, não serviço compartilhado nem pacote pip (decisão do Rodrigo, 28/09). Motivo: poucos
apps, um mantenedor; sem instalação, sem credencial de repo privado no Streamlit Cloud, cada app autossuficiente.
Risco aceito: cópias divergirem → mitigado pela regra da §6.

## 3. A pasta

`levantamento-normativos/llm_cadeia/` — **a origem**. Um app adota copiando a pasta inteira.

| Arquivo | Papel |
|---|---|
| `README.md` | ponto de entrada: o que é, como adotar (5 passos), segredos, uso, diagnóstico, changelog |
| `__init__.py` | API pública + `__version__` |
| `nucleo.py` | cadeia, rodízio de modelos, esperas, transportes. Streamlit só para ler Secrets (opcional) |
| `painel_streamlit.py` | opcional: `painel_llm()` — campo "usar minha chave" + status, para a barra lateral |
| `diagnostico.py` + `__main__.py` | `python -m llm_cadeia`: 1 chamada mínima por provedor/modelo configurado, tabela ok/erro |
| `test_llm_cadeia.py` | testes sem rede, viajam com a cópia |

Dependências: `requests`; `google-genai` (opcional — sem ele, os provedores Gemini somem da cadeia).

## 4. API

```python
from llm_cadeia import gerar
r = gerar(prompt, sistema=None, json=False, temperatura=0.0, max_tokens=1024)
r.texto       # str | None — None quando todos falharam ou não há provedor
r.origem      # "provedor (modelo)" de quem respondeu, ou None
r.tentativas  # list[str]: "provedor/modelo: motivo" de cada falha (nunca a chave)
```
`gerar` **nunca levanta exceção**. Também exportados: `disponivel()`, `descrever()`, `ultimo_usado()`,
`provedor_do_usuario()`, `novo_contexto()`, `usar_contexto()`, `PRESETS`, `GEMINI_MODELOS_PADRAO`.

- `sistema`: Gemini → `system_instruction`; OpenAI-compatível → mensagem `system`.
- `json=True`: Gemini → `response_mime_type="application/json"`; OpenAI-compatível → **sem** `response_format`
  (📝 suspeita não verificada: LM Studio recusa `json_object`); em todos, cercas ```` ``` ```` são retiradas da
  resposta. Validar o JSON continua sendo trabalho do app.
- Resposta vazia não troca de modelo (volta `texto=None`, `origem` preenchida) — evita misturar modelos em silêncio.

## 5. Configuração (Secrets ou variável de ambiente; iguais em todos os apps)

| Segredo | Provedor |
|---|---|
| `LLM_BASE_URL`, `LLM_MODEL` (lista), `LLM_API_KEY` | `local` — servidor OpenAI-compatível (Gemma do Nuati) |
| `GEMINI_API_KEY`, `GEMINI_API_KEY_2` | `gemini`, `gemini-2` |
| `GROQ_API_KEY`, `GROQ_API_KEY_2` | `groq`, `groq-2` |
| `CEREBRAS_API_KEY`, `CEREBRAS_API_KEY_2` | `cerebras`, `cerebras-2` |
| `OPENROUTER_API_KEY`, `OPENROUTER_API_KEY_2` | `openrouter`, `openrouter-2` |
| `<SERVICO>_MODELS` (ex.: `GEMINI_MODELS`) | troca a lista padrão de modelos daquele serviço (vale para as duas chaves) |
| `LLM_ORDEM` | troca a ordem (ex.: `"gemini-2,gemini,groq"`); nomes omitidos entram no fim na ordem padrão |

Convenção 📝 sugerida: sem sufixo = nuati.secin, `_2` = rodilpinto.
Ordem padrão: **usuário** (sempre primeiro) > local > gemini > gemini-2 > groq > groq-2 > cerebras > cerebras-2 >
openrouter > openrouter-2.
Servidor: `LLM_BASE_URL` + chaves. Streamlit Cloud: só as chaves (sem `LLM_BASE_URL`).

## 6. Regra de sincronia

- A origem é **esta pasta neste repo**. Cópias **não são editadas**: melhoria nasce aqui, sobe `__version__`,
  entra no changelog do README, e é recopiada.
- O README da cópia ganha uma linha "Copiado de buscador-normativos @ `<commit>` em `<data>`".
- `CLAUDE.md` deste repo aponta para `llm_cadeia/README.md`.

## 7. Comportamento herdado (sem mudança em relação a `de9f616`)

Esperas: 429 diário → até a meia-noite do Pacífico; 429 por minuto / 5xx / sobrecarga → modelo 60 s; 404 → modelo 6 h;
401/403/chave inválida → provedor 6 h; rede/timeout → provedor 5 min; outro → modelo 5 min. Chave do usuário por
sessão via `ContextVar` (nunca em variável de módulo — LESSONS 25/09). Chaves nunca em log, status ou `tentativas`.
Blocos `<think>` de modelos de raciocínio são removidos.

## 8. Migração deste app

`llm/gemini_client.py` passa a importar de `llm_cadeia` (prompts intocados); `app.py` usa `painel_llm()`;
`llm/cadeia.py` sai (conteúdo e comentários vão para `nucleo.py` — auditoria de documentação no review);
`tests/test_cadeia_llm.py` vira `llm_cadeia/test_llm_cadeia.py` no runner. Critério: runner TUDO VERDE + AppTest
sem exceção + `python -m llm_cadeia` com a chave desta máquina.

## 9. Fora do escopo

Imagens/arquivos no prompt, streaming, serviço compartilhado, pacote pip, migrar os outros dois apps (cada sessão
faz a sua pelo README), subir para `deploy` (só com ok do Rodrigo).
