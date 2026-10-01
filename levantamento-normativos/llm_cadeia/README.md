# llm_cadeia: LLM com fallback entre provedores (pasta copiável)

**Versão 1.1.0** · **Origem:** `github.com/rodilpinto/nuati-framework` (privado), pasta `llm_cadeia/`.
Histórico de versões: [`CHANGELOG.md`](CHANGELOG.md). Regras de cópia e registro de onde há cópias: README da raiz
do framework.

Um jeito só de chamar LLM em todas as soluções do Nuati. Tenta, em ordem, até alguém responder:

```
chave do usuário (digitada na tela, só na sessão dele)
  → local   (Gemma do servidor do Nuati, OpenAI-compatível)
  → gemini → gemini-2 → groq → groq-2 → cerebras → cerebras-2 → openrouter → openrouter-2
```

Cada provedor tem uma **lista de modelos**. Cota ou sobrecarga num modelo → tenta o próximo modelo do mesmo
provedor (a cota do Gemini é por projeto **e por modelo**). Chave inválida ou rede fora → pula o provedor.
Sem nenhum provedor configurado, `gerar` devolve `texto=None` e o app segue sem LLM. **Nunca levanta exceção.**

## Adotar num app

1. **Copie a pasta inteira** `llm_cadeia/` para a raiz do código do app (ao lado do `app.py`), sem editar nada.
   Registre a cópia no README da raiz do framework ("Registro de cópias"): app, caminho, versão, commit do framework.
2. **Dependências** no `requirements.txt`: `requests` e `google-genai` (sem este, os provedores Gemini somem).
3. **Segredos** em `.streamlit/secrets.toml` (local/servidor) ou em *Secrets* do Streamlit Cloud: tabela abaixo;
   modelo pronto em [`secrets.toml.example`](secrets.toml.example). Os valores internos (endereço do servidor local,
   qual conta é qual) ficam só no `segredos.exemplo.toml` da raiz do framework, que é privado e não se copia.
   Mudou Secrets na nuvem → **Reboot app** (são lidos no import).
4. **Troque a chamada ao LLM** por `gerar` (exemplos abaixo). Mantenha os prompts e a validação do app.
5. **Barra lateral** (opcional, recomendado): `painel_llm()`, ver abaixo.
6. Rode, da pasta que contém `llm_cadeia/`: `python -m pytest llm_cadeia -q` e `python -m llm_cadeia`.

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

**Barra lateral**: tem de rodar **antes** de qualquer `gerar` (a barra lateral roda no topo do script):

```python
from llm_cadeia.painel_streamlit import painel_llm
with st.sidebar:
    painel_llm()          # campo "Usar minha própria chave de IA" + status da cadeia
```

A chave digitada pelo usuário fica só no `st.session_state` daquela sessão (nunca em disco, log, variável de
módulo nem para outros usuários) e vai na frente de todas.

"Última resposta: provedor (modelo)" é atualizada na **mesma** execução do script, logo depois do `gerar`
(o painel instala o gancho `ao_responder` no contexto da sessão); não precisa de `st.rerun()`.

**OpenAI paga:** não é segredo do app. O usuário escolhe "Outro (compatível com OpenAI)", URL base
`https://api.openai.com/v1`, modelo (ex.: `gpt-5-mini`) e a própria chave. Modelos de raciocínio da OpenAI
recusam `max_tokens` e `temperature` ≠ 1: o transporte repete a chamada uma vez com `max_completion_tokens` e
sem `temperature`. ⚠ Coberto por teste com dublê; não verificado ao vivo (sem chave OpenAI em 28/09).

## Segredos (iguais em todos os apps)

| Segredo | Provedor | Onde conseguir |
|---|---|---|
| `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` (opcional) | `local` | servidor OpenAI-compatível da rede interna (endereço: `segredos.exemplo.toml` da raiz do framework). **Só alcançável de dentro da rede da Câmara** |
| `GEMINI_API_KEY`, `GEMINI_API_KEY_2` | `gemini`, `gemini-2` | aistudio.google.com/apikey |
| `GROQ_API_KEY`, `GROQ_API_KEY_2` | `groq`, `groq-2` | console.groq.com/keys |
| `CEREBRAS_API_KEY`, `CEREBRAS_API_KEY_2` | `cerebras`, `cerebras-2` | cloud.cerebras.ai |
| `OPENROUTER_API_KEY`, `OPENROUTER_API_KEY_2` | `openrouter`, `openrouter-2` | openrouter.ai/keys |

Ajustes (todos opcionais):

| Ajuste | Efeito | Padrão |
|---|---|---|
| `GEMINI_MODELS`, `GROQ_MODELS`, … | troca a lista de modelos do serviço (vírgulas) | `PRESETS` e `GEMINI_MODELOS_PADRAO` em `nucleo.py` |
| `LLM_ORDEM` | troca a ordem, ex. `"gemini-2,gemini,groq"`; os omitidos vão para o fim | ordem acima |
| `LLM_SOMENTE` | **só** estes provedores, nesta ordem, ex. `"groq"` (para teste e comparação de modelos). A chave digitada pelo usuário continua valendo | todos |
| `LLM_TIMEOUT_S` | tempo máximo de espera pela resposta do `local`, em segundos | `300` |
| `LLM_DISABLE_THINKING` | `1` desliga o raciocínio do modelo `local` (Gemma/Qwen: `chat_template_kwargs.enable_thinking=false`). Se o servidor recusar o campo, a chamada é repetida sem ele | desligado |

Provedores na nuvem (Gemini e os OpenAI-compatíveis) esperam no máximo 120 s por resposta
(`_TIMEOUT_NUVEM_S` em `nucleo.py`); estourou, o provedor fica em espera 5 min e a cadeia segue.

⚠ Para forçar um provedor num teste, ponha `LLM_SOMENTE` (ou qualquer ajuste) na **variável de ambiente** e **não** no
`secrets.toml`: o `st.secrets` é lido antes do ambiente e carrega também o `~/.streamlit/secrets.toml` global, mesmo
fora do `streamlit run`. A cadeia é montada no import; depois de mudar o ambiente no mesmo processo, chame
`llm_cadeia.recarregar()`.

Segunda chave (`_2`): outro login. Só soma cota do Gemini se for de **outro projeto** Google (a cota é por projeto,
não por chave).

| Onde roda | Segredos |
|---|---|
| Servidor do Nuati | `LLM_BASE_URL` + `LLM_MODEL` + as chaves gratuitas (fallback) |
| Streamlit Cloud | só as chaves gratuitas. Pode ter `LLM_BASE_URL` também: inalcançável, o `local` falha a conexão em 5 s e fica 5 min fora, por processo |

⚠ Trocar Secrets também é deploy: antes de trocar os Secrets de um app, confira quais nomes o código **daquela
branch** lê (LESSONS do framework, incidente de 28/09).

Modelos padrão e limites gratuitos (conferidos nas docs em 25/09/2026): `PRESETS` e `GEMINI_MODELOS_PADRAO` em
`nucleo.py`.

## Diagnóstico

```bash
python -m llm_cadeia      # da pasta que contém llm_cadeia/
```

Uma chamada mínima por modelo de cada provedor configurado; imprime `provedor  modelo  ok|motivo`. Use ao
configurar um servidor novo: gasta 1 requisição por modelo. Nunca imprime chave.

## Esperas após falha

| Falha | Para | Por quanto tempo |
|---|---|---|
| 429 diário | o modelo | até a meia-noite do Pacífico (reset do Gemini) |
| 429 por minuto, 5xx, sobrecarga | o modelo | 60 s |
| 404 (modelo não existe para a chave) | o modelo | 6 h |
| 401/403, chave inválida | o provedor | 6 h |
| rede / timeout | o provedor | 5 min |
| outro | o modelo | 5 min |

As esperas valem por processo (reiniciar o app ou `recarregar()` zera).

## Testes

`python -m pytest llm_cadeia -q`, da pasta que contém `llm_cadeia/`. Nenhum teste faz rede nem importa nada do app.
Um dos testes varre a própria pasta atrás de dado interno (IP de rede privada, login institucional): a pasta tem de
poder ir para um repo público sem exceção na trava de publicação.

## Regra de sincronia

**Não edite uma cópia.** Melhoria nasce no framework, sobe `__version__` (`__init__.py`), entra no
`CHANGELOG.md` e é recopiada para os apps. Divergência entre cópias = bug. Detalhes: README da raiz do framework.
