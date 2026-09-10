---
task: 15
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 2291-2443)
reference: spec/buscador/reference/global-constraints.md
---

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T14 (mesmo `app.py`), T11, T12, T13
> **Onda/trilha:** onda 4 - trilha F (web), NUNCA em paralelo com T14

## Task 15: Web — nova busca e aplicação do download

**Files:**
- Modify: `buscador/web/app.py`
- Create: `buscador/web/templates/inicio.html`
- Test: `tests/test_web_fluxo.py`

**Interfaces:**
- Consumes: `executar_busca`, `baixar_selecionados`, `gerar_planilha`
- Produces: rotas `GET /`, `POST /buscas`, `POST /busca/{id}/aplicar`

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_web_fluxo.py`:

```python
from fastapi.testclient import TestClient
from buscador.config import Config
from buscador.web.app import criar_app


def _cli(tmp_path, fontes=None):
    cfg = Config(raiz_dados=tmp_path, banco=tmp_path / "t.db")
    app = criar_app(cfg)
    if fontes is not None:
        app.state.fontes = fontes
    return TestClient(app), cfg


def test_inicio_lista_buscas_e_tem_formulario(tmp_path):
    cli, _ = _cli(tmp_path)
    r = cli.get("/")
    assert r.status_code == 200
    assert 'name="tema"' in r.text


def test_post_buscas_cria_e_redireciona_para_triagem(tmp_path):
    from buscador.fontes.base import FonteFake
    cli, _ = _cli(tmp_path, [FonteFake(nome="f", itens=[("A", "https://x/a.pdf")])])
    r = cli.post("/buscas", data={"tema": "LGPD"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/busca/1"


def test_aplicar_baixa_e_gera_planilha(tmp_path):
    from buscador.fontes.base import FonteFake
    cli, cfg = _cli(tmp_path, [FonteFake(nome="f", itens=[("A", "https://x/a.pdf")])])
    cli.post("/buscas", data={"tema": "LGPD"})
    cli.post("/busca/1/decisoes", data={"fica": ["1"]})
    app = cli.app
    app.state.baixar_fn = lambda url: b"conteudo"
    r = cli.post("/busca/1/aplicar", follow_redirects=False)
    assert r.status_code == 303
    assert (tmp_path / "planilhas" / "busca-1.xlsx").exists()


def test_aplicar_sem_triagem_devolve_400(tmp_path):
    from buscador.fontes.base import FonteFake
    cli, _ = _cli(tmp_path, [FonteFake(nome="f", itens=[("A", "https://x/a.pdf")])])
    cli.post("/buscas", data={"tema": "LGPD"})
    assert cli.post("/busca/1/aplicar").status_code == 400
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_web_fluxo.py -v`
Expected: FAIL — rotas `/` e `/buscas` não existem (404)

- [ ] **Step 3: Implementar as rotas novas**

Em `buscador/web/app.py`, dentro de `criar_app`, **antes** do `return app`, acrescente:

```python
    from buscador.busca import executar_busca
    from buscador.download import baixar_selecionados
    from buscador.planilha import gerar_planilha

    app.state.fontes = []
    app.state.baixar_fn = None

    @app.get("/")
    def inicio(request: Request):
        c = conn()
        buscas = c.execute("SELECT * FROM buscas ORDER BY id DESC").fetchall()
        return TEMPLATES.TemplateResponse(request, "inicio.html", {"buscas": buscas})

    @app.post("/buscas")
    def nova_busca(tema: str = Form(...)):
        c = conn()
        bid = executar_busca(c, tema, app.state.fontes, cfg.acervo_raizes)
        return RedirectResponse(f"/busca/{bid}", status_code=303)

    @app.post("/busca/{busca_id}/aplicar")
    def aplicar(busca_id: int):
        c = conn()
        busca = c.execute("SELECT * FROM buscas WHERE id=?", (busca_id,)).fetchone()
        if busca is None:
            raise HTTPException(status_code=404, detail="busca nao encontrada")
        if busca["triado_em"] is None:
            raise HTTPException(status_code=400, detail="triagem ainda nao gravada")
        baixar_selecionados(c, busca_id, cfg.raiz_dados, app.state.baixar_fn)
        gerar_planilha(c, busca_id, cfg.raiz_dados / "planilhas" / f"busca-{busca_id}.xlsx")
        return RedirectResponse(f"/busca/{busca_id}", status_code=303)
```

E adicione ao fim de `triagem.html`, dentro do bloco `corpo`, fora do `<form>`:

```html
<form method="post" action="/busca/{{ busca.id }}/aplicar">
  <button type="submit">Baixar e organizar o que ficou</button>
</form>
```

- [ ] **Step 4: Criar o template de início**

`buscador/web/templates/inicio.html`:

```html
{% extends "base.html" %}
{% block titulo %}Buscador de Base Normativa{% endblock %}
{% block corpo %}
<h1>Buscador de Base Normativa</h1>
<form method="post" action="/buscas">
  <input name="tema" placeholder="Tema da ação de controle" size="50" required>
  <button type="submit">Buscar</button>
</form>
<h2>Buscas anteriores</h2>
<ul>
{% for b in buscas %}
  <li><a href="/busca/{{ b.id }}">{{ b.tema }}</a>
      <span class="motivo">{{ b.criado_em }}{% if b.triado_em %} · triada{% endif %}
      {% if b.baixado_em %} · baixada{% endif %}</span></li>
{% else %}
  <li class="motivo">nenhuma busca ainda</li>
{% endfor %}
</ul>
{% endblock %}
```

- [ ] **Step 5: Rodar a suíte inteira**

Run: `py -m pytest -v`
Expected: todos passam

- [ ] **Step 6: Commit**

```bash
git add buscador/web tests/test_web_fluxo.py
git commit -m "feat: fluxo web completo (nova busca, triagem, aplicar)"
```

---

