# Changelog do llm_cadeia

Versão atual em `__init__.py` (`__version__`). Cada versão nasce no `nuati-framework` e é recopiada para os apps.

## 1.1.0 (29/09/2026): primeira versão nascida no nuati-framework

Pedidos do checklist-conformidade (`_sessao/TODO.md`, P0, "Pedidos para a origem") e seção A do
`LEVANTAMENTO-FRAMEWORK.md`. Cada item tem teste (`test_a_*` … `test_e_*`). ✅ Ao vivo em 29/09 (PC do trabalho, `python -m llm_cadeia`): todos os
provedores configurados responderam em pelo menos um modelo, com o tempo limite novo no Gemini já ativo.

- **a · Tempo limite do `local` configurável:** `LLM_TIMEOUT_S` (segundos); padrão sobe de 120 s para **300 s**
  (📝 valor escolhido pelo framework: o app antigo do checklist usava 300 s; medido 154 s com raciocínio para 5.000
  caracteres de normativo). A conexão continua falhando em 5 s. O provedor "Outro" digitado pelo usuário usa o mesmo
  tempo do `local`.
- **b · Desligar o raciocínio do `local`:** `LLM_DISABLE_THINKING=1` envia `chat_template_kwargs.enable_thinking=false`
  (Gemma/Qwen). Servidor que recusar o campo com 400 recebe a chamada de novo, uma vez, sem ele (este caminho: só
  teste com dublê). ✅ **Verificado ao vivo (29/09, PC do trabalho, `google/gemma-4` do servidor local):** o servidor
  aceita o campo (HTTP 200); o mesmo prompt curto de análise em JSON levou 27,1 s sem e 3,8 s com o ajuste.
- **c · Sem dado interno na pasta:** saíram o endereço do servidor local e os logins das contas (README, docstring,
  comentário, testes). Os valores ficam no `segredos.exemplo.toml` da raiz do framework (privado, não se copia); a pasta
  traz um `secrets.toml.example` só com marcadores. Teste novo varre a pasta. Efeito: a trava do
  `publicar_github.sh` do checklist não precisa mais de exceção para `llm_cadeia/`.
- **d · Forçar um só provedor:** `LLM_SOMENTE` (ex.: `"groq"`) usa só os provedores listados, nesta ordem
  (`LLM_ORDEM` continua pondo os omitidos no fim). `recarregar()` remonta a cadeia depois de mudar o ambiente.
  O `st.secrets` continua lido antes do ambiente: para teste, ponha o ajuste no ambiente, não no `secrets.toml`.
- **e · Tempo limite no Gemini:** 120 s por chamada (`HttpOptions(timeout=ms)` na SDK `google-genai`;
  `request_options={"timeout": s}` na SDK antiga ⚠ não instalada aqui, sem teste). Estourou: o provedor fica 5 min
  em espera, como qualquer falha de rede.
- README reescrito para a origem nova; changelog saiu do README para este arquivo.

Compatibilidade: API pública igual à 1.0.1, mais `recarregar()`. Nomes de segredo iguais; os ajustes novos são
opcionais. Muda o comportamento em um ponto: o `local` espera até 300 s (antes 120 s).

## 1.0.1 (28/09/2026): achados da adoção no `scopediagram` (rede da Câmara)

Origem então: `buscador-normativos` (trazida para cá sem mudança de código, de `buscador-normativos @ f58b79a`).

- **Verificado ao vivo:** `local` (`google/gemma-4`, LM Studio do Nuati) com `sistema=` + `json=True` → JSON sem
  cerca, `json.loads` OK, acentos corretos (11,8 s); extração IGOE completa passou no pydantic (~48 s). A rede da
  Câmara deixa passar gemini, groq, cerebras e openrouter.
- `painel_llm()` atualiza "Última resposta" na mesma execução (gancho `ao_responder` no contexto; erro no gancho nunca
  derruba o `gerar`).
- OpenAI (modelos de raciocínio): 400 por `max_tokens`/`temperature` → 1 repetição com `max_completion_tokens` e sem
  `temperature`. ⚠ Só teste com dublê.
- Docstrings desatualizadas corrigidas (`gerar` devolve `Resposta`; presets já verificados com chave real).
- ⚠ Chave Gemini criada em set/2026 recebe 404 em `gemini-2.5-flash(-lite)` ("no longer available to new users");
  a lista padrão já cai para 3.x, mas app que fixar `gemini-2.5-flash` quebra com chave nova.

## 1.0.0 (28/09/2026): vira pasta copiável (de `llm/cadeia.py` do buscador)

`gerar` devolve `Resposta` (`texto`, `origem`, `tentativas`); `sistema=`, `json=`; segunda chave `_2` para todo
serviço; `painel_llm()`; `python -m llm_cadeia`; piso de 4096 tokens também no Gemini (medido: 16 tokens → resposta
vazia). **Verificado ao vivo (28/09):** gemini, gemini-2, groq, cerebras e openrouter respondem; `sistema=` +
`json=True` devolvem JSON que passa em `json.loads` nos 5. ⚠ Não verificado: `local`.

## Antes do pacote

- 25/09: rodízio de modelos, Groq/Cerebras/OpenRouter, chave do usuário por sessão.
- 23/09: cadeia A (local) > B (Gemini) > C (Gemini 2).
