# `llm_cadeia` portátil — Implementation Plan

> **For agentic workers:** executado inline nesta sessão (superpowers:executing-plans), a pedido do Rodrigo ("go ahead").

**Goal:** transformar `llm/cadeia.py` na pasta copiável `llm_cadeia/`, com `sistema`, `json`, chaves `_2` para todo
serviço, `Resposta` com tentativas, painel Streamlit e diagnóstico.

**Architecture:** spec `docs/superpowers/specs/2026-09-28-llm-cadeia-portatil-design.md` (SSOT; o plano não a repete).

**Tech Stack:** Python 3.13, requests, google-genai (opcional), Streamlit (opcional), pytest.

## Global Constraints

- `gerar` nunca levanta exceção; chave nunca em log/status/`tentativas`.
- Chave do usuário só via `ContextVar` (nunca variável de módulo).
- `nucleo.py` não importa nada do projeto; Streamlit só para ler Secrets, dentro de `try`.
- Comentários de `llm/cadeia.py` migram para `nucleo.py` (regra docs-move-with-code); `git mv` para manter história.
- Runner (`tools/run_all_tests.py`) TUDO VERDE ao fim de cada task; UTF-8 explícito; rodar via Bash.

---

### Task 1: pacote `llm_cadeia` (núcleo + API nova + testes)

**Files:** `git mv llm/cadeia.py llm_cadeia/nucleo.py`; create `llm_cadeia/__init__.py`;
`git mv tests/test_cadeia_llm.py llm_cadeia/test_llm_cadeia.py`; modify `llm/gemini_client.py`, `tools/run_all_tests.py`.

**Interfaces — Produces:**
`gerar(prompt, sistema=None, json=False, temperatura=0.0, max_tokens=1024) -> Resposta`;
`Resposta(texto: str|None, origem: str|None, tentativas: list[str])`;
`disponivel()`, `descrever()`, `ultimo_usado()`, `provedor_do_usuario(tipo, chave, modelo="", base_url="")`,
`novo_contexto()`, `usar_contexto(ctx)`, `PRESETS`, `GEMINI_MODELOS_PADRAO`, `__version__ = "1.0.0"`.
Transportes: `_gerar_openai(p, modelo, prompt, sistema, json, temperatura, max_tokens)` e `_gerar_gemini(...)` mesma assinatura.

- [ ] Testes novos (falham antes): `tentativas` lista falhas sem chave; `sistema` vira mensagem `system` no payload
      OpenAI; `json=True` tira cercas ```` ```json ````; `GROQ_API_KEY_2` gera provedor `groq-2` logo após `groq`;
      testes existentes adaptados a `Resposta` e à nova assinatura dos transportes.
- [ ] Implementar; `gemini_client._generate` usa `gerar(...).texto`.
- [ ] Runner com a suíte no novo caminho (baseline = nova contagem) → TUDO VERDE. Commit.

### Task 2: `painel_streamlit.painel_llm()` + `app.py`

- [ ] Mover o bloco da barra lateral de `app.py` para `painel_llm()` (mesmas `key=` dos widgets, mesmo texto).
- [ ] `app.py`: `from llm_cadeia.painel_streamlit import painel_llm` e chamar dentro de `with st.sidebar:`.
- [ ] AppTest: sem exceção; escolher Groq + chave falsa → `usuario — openai/gpt-oss-120b` no status. Commit.

### Task 3: diagnóstico

- [ ] `diagnostico.py`: `diagnosticar() -> list[tuple[provedor, modelo, "ok"|motivo]]`, chamando cada modelo de cada
      provedor configurado com "Responda só: ok" (ignora esperas); `__main__.py` imprime tabela. Teste sem rede com
      transportes dublados.
- [ ] Rodar de verdade com a chave desta máquina. Commit.

### Task 4: README e docs

- [ ] `llm_cadeia/README.md` (adotar em 5 passos, segredos, uso, diagnóstico, regra de sincronia, changelog).
- [ ] `CLAUDE.md` ponteiro; `secrets.toml.example` com `_2`; `log.md`; `SESSION-ONBOARD` §8. Runner final. Commit.
