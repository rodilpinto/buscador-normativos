---
task: 14
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 2049-2290)
reference: spec/buscador/reference/global-constraints.md
---

> ⛔ **SUPERADO — não execute.** Cópia verbatim de uma task do plano de 16 tasks, superado em
> 2026-09-16. Plano vigente: `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md`.

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T2, T3, T11
> **Onda/trilha:** onda 4 - trilha F (web)

## Task 14: Web — página de triagem e ações de grupo

**Files:**
- Create: `buscador/web/app.py`, `buscador/web/templates/base.html`, `buscador/web/templates/triagem.html`
- Test: `tests/test_web_triagem.py`

**Interfaces:**
- Consumes: tudo anterior
- Produces: `criar_app(cfg: Config) -> FastAPI` com rotas `GET /busca/{id}` (triagem) e `POST /busca/{id}/decisoes` (grava)

Esta é a tela que resolve a dor. Mecanismo **M2** (decisão por grupo) mora aqui, e a mitigação de **B5** é o botão "desmarcar todos os já-tenho".

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_web_triagem.py`:

```python
from fastapi.testclient import TestClient
from buscador.config import Config
from buscador.db import conectar, criar_schema
from buscador.busca import executar_busca
from buscador.fontes.base import FonteFake
from buscador.web.app import criar_app


def _app(tmp_path):
    cfg = Config(raiz_dados=tmp_path, banco=tmp_path / "t.db")
    conn = conectar(cfg.banco)
    criar_schema(conn)
    bid = executar_busca(conn, "LGPD", [FonteFake(nome="f", itens=[
        ("Lei nº 1", "https://x.gov.br/l1.htm"),
        ("Lei nº 2", "https://x.gov.br/l2.htm")])], [])
    conn.close()
    return TestClient(criar_app(cfg)), bid


def test_pagina_de_triagem_lista_os_resultados(tmp_path):
    cli, bid = _app(tmp_path)
    r = cli.get(f"/busca/{bid}")
    assert r.status_code == 200
    assert "Lei nº 1" in r.text
    assert "Lei nº 2" in r.text


def test_pagina_mostra_o_motivo_da_premarcacao(tmp_path):
    cli, bid = _app(tmp_path)
    assert "Aplicavel, de fonte catalogada" in cli.get(f"/busca/{bid}").text


def test_pagina_traz_o_botao_de_desmarcar_ja_tenho(tmp_path):
    cli, bid = _app(tmp_path)
    assert 'data-acao="desmarcar-ja-tenho"' in cli.get(f"/busca/{bid}").text


def test_post_de_decisoes_grava_e_redireciona(tmp_path):
    cli, bid = _app(tmp_path)
    r = cli.post(f"/busca/{bid}/decisoes", data={"fica": ["1"]},
                 follow_redirects=False)
    assert r.status_code == 303
    from buscador.db import conectar as c2
    conn = c2(tmp_path / "t.db")
    linhas = {x["id"]: x["decisao"] for x in
              conn.execute("SELECT id, decisao FROM resultados")}
    assert linhas[1] == "fica"
    assert linhas[2] == "sai"


def test_busca_inexistente_devolve_404(tmp_path):
    cli, _ = _app(tmp_path)
    assert cli.get("/busca/999").status_code == 404
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_web_triagem.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar o app**

`buscador/web/app.py`:

```python
"""App web local. Sem autenticacao: roda em localhost, uso individual."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from buscador.config import Config
from buscador.db import conectar, criar_schema

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def criar_app(cfg: Config) -> FastAPI:
    app = FastAPI(title="Buscador de Base Normativa")
    app.state.cfg = cfg

    def conn():
        c = conectar(cfg.banco)
        criar_schema(c)
        return c

    @app.get("/busca/{busca_id}")
    def triagem(request: Request, busca_id: int):
        c = conn()
        busca = c.execute("SELECT * FROM buscas WHERE id = ?", (busca_id,)).fetchone()
        if busca is None:
            raise HTTPException(status_code=404, detail="busca nao encontrada")
        linhas = c.execute(
            "SELECT * FROM resultados WHERE busca_id = ? ORDER BY categoria, titulo",
            (busca_id,)).fetchall()
        grupos: dict[str, list] = {}
        for linha in linhas:
            grupos.setdefault(linha["categoria"] or "sem-categoria", []).append(linha)
        return TEMPLATES.TemplateResponse(request, "triagem.html", {
            "busca": busca, "grupos": grupos, "total": len(linhas)})

    @app.post("/busca/{busca_id}/decisoes")
    def gravar(busca_id: int, fica: list[int] = Form(default=[])):
        c = conn()
        agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
        c.execute("UPDATE resultados SET decisao='sai', decidido_em=? "
                  "WHERE busca_id=?", (agora, busca_id))
        if fica:
            marcas = ",".join("?" * len(fica))
            c.execute(f"UPDATE resultados SET decisao='fica', decidido_em=? "
                      f"WHERE busca_id=? AND id IN ({marcas})",
                      (agora, busca_id, *fica))
        c.execute("UPDATE buscas SET triado_em=? WHERE id=?", (agora, busca_id))
        return RedirectResponse(f"/busca/{busca_id}", status_code=303)

    return app
```

- [ ] **Step 4: Implementar os templates**

`buscador/web/templates/base.html`:

```html
<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>{% block titulo %}Buscador{% endblock %}</title>
<style>
 body{font-family:system-ui,sans-serif;margin:0;padding:0 24px 120px;background:#0d1117;color:#f0f6fc}
 h1{font-size:24px} .grupo{border:1px solid #26303b;border-radius:10px;margin:18px 0;padding:12px}
 .grupo h2{font-size:16px;margin:0 0 8px} .item{padding:8px;border-top:1px solid #1a222c}
 .motivo{color:#9ba3ad;font-size:13px} .selo{font-size:11px;border-radius:4px;padding:1px 6px;margin-left:6px}
 .selo.tenho{background:#3b2f14;color:#e8b84b} .selo.web{background:#3b1f1d;color:#e5534b}
 .barra{position:fixed;left:0;right:0;bottom:0;background:#141a22;border-top:1px solid #26303b;padding:12px 24px}
 button{background:#e8b84b;color:#0d1117;border:0;border-radius:8px;padding:8px 16px;font-weight:700;cursor:pointer}
 .acao{background:#26303b;color:#f0f6fc;font-weight:400;font-size:12px;padding:4px 10px}
</style></head>
<body>{% block corpo %}{% endblock %}</body></html>
```

`buscador/web/templates/triagem.html`:

```html
{% extends "base.html" %}
{% block titulo %}Triagem — {{ busca.tema }}{% endblock %}
{% block corpo %}
<h1>Triagem: {{ busca.tema }}</h1>
<p class="motivo">{{ total }} resultados. Pré-marcação sugerida pelo sistema —
confira e diverja onde discordar.</p>
<form method="post" action="/busca/{{ busca.id }}/decisoes">
 <p>
  <button type="button" class="acao" data-acao="marcar-todos">marcar todos</button>
  <button type="button" class="acao" data-acao="desmarcar-todos">desmarcar todos</button>
  <button type="button" class="acao" data-acao="desmarcar-ja-tenho">desmarcar todos os já-tenho</button>
  <button type="button" class="acao" data-acao="desmarcar-web">desmarcar web aberta</button>
 </p>
 {% for categoria, itens in grupos.items() %}
 <div class="grupo" data-categoria="{{ categoria }}">
  <h2>{{ categoria }} ({{ itens|length }})
   <button type="button" class="acao" data-acao="grupo-marcar">marcar grupo</button>
   <button type="button" class="acao" data-acao="grupo-desmarcar">desmarcar grupo</button>
  </h2>
  {% for r in itens %}
  <div class="item">
   <label>
    <input type="checkbox" name="fica" value="{{ r.id }}"
           data-ja-tenho="{{ 1 if r.ja_tenho else 0 }}"
           data-procedencia="{{ r.procedencia }}"
           {% if r.pre_marca == 'fica' %}checked{% endif %}>
    <b>{{ r.titulo }}</b>
    {% if r.ja_tenho %}<span class="selo tenho">já tenho</span>{% endif %}
    {% if r.procedencia == 'web-aberta' %}<span class="selo web">web aberta</span>{% endif %}
   </label>
   <div class="motivo">{{ r.ementa or '' }}</div>
   <div class="motivo">↳ {{ r.pre_motivo }} · <a href="{{ r.url }}" target="_blank">fonte</a></div>
  </div>
  {% endfor %}
 </div>
 {% endfor %}
 <div class="barra">
  <span id="contador"></span>
  <button type="submit">Gravar decisões</button>
 </div>
</form>
<script>
 const caixas = () => [...document.querySelectorAll('input[name=fica]')];
 function contar(){
   const n = caixas().filter(c => c.checked).length;
   document.getElementById('contador').textContent = n + ' de ' + caixas().length + ' marcados — ';
 }
 document.addEventListener('click', e => {
   const acao = e.target.dataset.acao;
   if (!acao) return;
   const grupo = e.target.closest('.grupo');
   if (acao === 'marcar-todos') caixas().forEach(c => c.checked = true);
   if (acao === 'desmarcar-todos') caixas().forEach(c => c.checked = false);
   if (acao === 'desmarcar-ja-tenho') caixas().forEach(c => { if (c.dataset.jaTenho === '1') c.checked = false; });
   if (acao === 'desmarcar-web') caixas().forEach(c => { if (c.dataset.procedencia === 'web-aberta') c.checked = false; });
   if (acao === 'grupo-marcar') grupo.querySelectorAll('input[name=fica]').forEach(c => c.checked = true);
   if (acao === 'grupo-desmarcar') grupo.querySelectorAll('input[name=fica]').forEach(c => c.checked = false);
   contar();
 });
 document.addEventListener('change', contar);
 contar();
</script>
{% endblock %}
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_web_triagem.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add buscador/web tests/test_web_triagem.py
git commit -m "feat: pagina de triagem com acoes de grupo (M2) e desmarcar ja-tenho"
```

---

