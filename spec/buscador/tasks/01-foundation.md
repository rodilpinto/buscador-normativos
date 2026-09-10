---
task: 1
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 53-194)
reference: spec/buscador/reference/global-constraints.md
---

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** nada (gate inicial)
> **Onda/trilha:** onda 1 - gate

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

