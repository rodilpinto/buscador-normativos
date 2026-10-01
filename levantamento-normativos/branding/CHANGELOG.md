# Changelog do branding

Versão atual em `__init__.py` (`__version__`).

## 1.0.0 (30/09/2026): entra no nuati-framework

Trazido de `checklist-conformidade`, branch `feat/llm-cadeia` @ `92ac158` (servidor interno), pasta `branding/`. Os 27
arquivos de lá vieram sem mudança (mesmo hash git), exceto:

- `__init__.py`: ganhou a docstring e `__version__ = "1.0.0"` (era vazio);
- `README.md`: a seção "Como apontar um app para este guia" (que mandava ao repo do checklist) virou "Como adotar num
  app", apontando para o framework; nada mais mudou no guia.

Novos: este `CHANGELOG.md` e `test_branding.py` (tokens.json, tokens.css e config.toml concordam; os 7 contrastes
citados no guia conferem com a fórmula do WCAG; os arquivos citados existem; assinatura sem siglas; helpers do
Streamlit com dublê).

Decisão: só a identidade da Câmara (F-A1, Rodrigo, 29/09); o `nuati.css` do auditflowmongodb não entra.
