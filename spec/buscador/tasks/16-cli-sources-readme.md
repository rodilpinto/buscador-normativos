---
task: 16
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 2444-2641)
reference: spec/buscador/reference/global-constraints.md
---

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T1-T15
> **Onda/trilha:** onda 5 - trilha G (fechamento)

## Task 16: CLI, registro das fontes e README

**Files:**
- Create: `buscador/cli.py`, `README.md`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: tudo
- Produces: `fontes_padrao(cfg) -> list[Fonte]`, `main(argv: list[str] | None = None) -> int`

Comandos: `buscador servir` (sobe o app com as fontes reais) e `buscador buscar "<tema>"` (headless, para script).

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_cli.py`:

```python
import pytest
from buscador.cli import main, fontes_padrao
from buscador.config import Config


def test_fontes_padrao_traz_as_tres_catalogadas(tmp_path):
    nomes = {f.nome for f in fontes_padrao(Config(raiz_dados=tmp_path,
                                                  banco=tmp_path / "t.db"))}
    assert {"planalto", "legin-camara", "tcu"} <= nomes


def test_main_sem_argumentos_devolve_2_e_mostra_uso(capsys):
    assert main([]) == 2
    assert "uso" in capsys.readouterr().out.lower()


def test_main_com_comando_desconhecido_devolve_2(capsys):
    assert main(["inventado"]) == 2
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_cli.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/cli.py`:

```python
"""CLI. `servir` sobe a interface; `buscar` roda headless para script."""
from __future__ import annotations

import argparse
import sys

from buscador.busca import executar_busca
from buscador.config import Config, carregar_config
from buscador.db import conectar, criar_schema
from buscador.fontes.base import Fonte
from buscador.fontes.legin_camara import FonteLegin
from buscador.fontes.planalto import FontePlanalto
from buscador.fontes.tcu import FonteTCU


def fontes_padrao(cfg: Config) -> list[Fonte]:
    return [FontePlanalto(), FonteLegin(), FonteTCU()]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    p = argparse.ArgumentParser(prog="buscador", add_help=True)
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("servir").add_argument("--porta", type=int, default=8077)
    sub.add_parser("buscar").add_argument("tema")

    if not argv:
        print("uso: buscador [servir|buscar] ...")
        return 2
    args = p.parse_args(argv)
    if args.cmd is None:
        print("uso: buscador [servir|buscar] ...")
        return 2

    cfg = carregar_config()
    if args.cmd == "servir":
        import uvicorn
        from buscador.web.app import criar_app
        app = criar_app(cfg)
        app.state.fontes = fontes_padrao(cfg)
        uvicorn.run(app, host="127.0.0.1", port=args.porta)
        return 0

    conn = conectar(cfg.banco)
    criar_schema(conn)
    bid = executar_busca(conn, args.tema, fontes_padrao(cfg), cfg.acervo_raizes)
    print(f"busca {bid} criada; abra http://127.0.0.1:8077/busca/{bid}")
    return 0
```

- [ ] **Step 4: Escrever o README**

`README.md`:

```markdown
# Buscador de Base Normativa

Monta o acervo de critério de uma ação de controle: pesquisa um tema em fontes
catalogadas e na web aberta, entrega uma lista **triável em poucas decisões**, e baixa
e organiza só o que sobreviveu à triagem.

## Instalação

    py -m venv .venv && .venv/Scripts/pip install -e ".[dev]"

## Uso

    buscador servir            # http://127.0.0.1:8077
    buscador buscar "LGPD"     # headless

## Configuração (variáveis de ambiente)

| Variável | Efeito |
|---|---|
| `BUSCADOR_DADOS` | raiz dos dados (padrão `dados`) |
| `BUSCADOR_ACERVO` | acervos existentes p/ o selo "já tenho", separados por `;` |
| `BUSCADOR_LLM_URL` | endpoint OpenAI-compatível; **sem isso o sistema roda igual** |
| `BUSCADOR_LLM_MODELO` | nome do modelo |
| `BUSCADOR_LLM_CHAVE` | chave, quando a API exigir |

## Como a triagem economiza decisões

1. **Já tenho** — cruza com o acervo existente e marca o que é redundante
2. **Grupo** — decide categoria inteira de uma vez
3. **Vinculação** — "contexto" nasce desmarcado
4. **Pré-marcação** — sugestão com motivo; você confirma ou diverge

⚠ A pré-marcação é **sugestão do sistema**, não julgamento validado. Duas travas
impedem que ela decida sozinha: item `obrigatorio` nunca nasce desmarcado, e nada vindo
da web aberta nasce marcado.

## Rastreabilidade

Toda linha guarda fonte, procedência, URL, sha256 do arquivo, data da coleta, a decisão
humana e o motivo da pré-marcação — inclusive quando você divergiu. Título e ementa são
copiados **literalmente** da fonte; texto de LLM vai para coluna separada.
```

- [ ] **Step 5: Rodar a suíte inteira**

Run: `py -m pytest -v`
Expected: todos passam

- [ ] **Step 6: Commit**

```bash
git add buscador/cli.py README.md tests/test_cli.py
git commit -m "feat: CLI, registro das fontes reais e README"
```

---

## Self-Review

**Cobertura da spec:**

| Requisito | Task |
|---|---|
| §2 M1 já-tenho | 9, 14 |
| §2 M2 grupo | 14 |
| §2 M3 vinculação | 10 |
| §2 M4 pré-marcação | 10 |
| §4 B1 híbrido de fontes | 5, 6, 7 |
| §4 B2 app web | 14, 15 |
| §4 B3 LLM opcional | 8 |
| §4 B4 pasta por tema | 12 |
| §4 B5 mostrar já-tenho | 14 |
| Mitigação B4 (dedup sha256) | 12 |
| Mitigação B5 (ação de grupo) | 14 |
| §6 rastreabilidade | 2, 13 |
| §7 travas anti-ancoragem | 10 |
| §7 260 chars | 12 |
| §8 roda sem LLM | 8 |

**Consistência de tipos:** `chave_dedup` (3) usada em 4-7, 11 · `Resultado` (3) produzido por todas as fontes · `conectar`/`criar_schema` (2) usados em 11-15 · `premarcar_todos` (10) chamado em 11 · `baixar_selecionados`/`gerar_planilha` (12, 13) chamados em 15 · `fontes_padrao` (16) alimenta `app.state.fontes` de 15.

**Sem placeholders:** todo passo traz código real; nenhum "similar à Task N".

---

## Riscos de execução conhecidos

1. **Os seletores CSS das Tasks 5-7 são suposição.** Planalto, Legin e TCU podem usar
   outra marcação. As fixtures deixam o teste verde mesmo se o seletor estiver errado
   **para o site real**. Ao implementar: baixe uma página real, confirme o seletor, e
   **substitua a fixture pela página real**. Se o seletor mudar, o teste de contrato
   quebra ruidosamente — que é o desenho.
2. **A rota de busca de cada fonte** (`/busca?q=`, `/legin/busca?termo=`) precisa ser
   confirmada contra o site. Só `extrair()` está coberto por teste; `buscar()` toca rede.
3. **A web aberta não tem provedor definido.** A Task 7 recebe a função por injeção de
   propósito: escolher o provedor é uma decisão sua, não deste plano.
