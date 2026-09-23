# -*- coding: utf-8 -*-
"""Gate visual da frente 2: dirige o app pelo navegador e AFIRMA o que a UI diz.

Pre-requisito: o app no ar em http://localhost:8501
    (em levantamento-normativos/: python -m streamlit run app.py --server.headless true)
Uso (na raiz):  PYTHONIOENCODING=utf-8 python tools/dirigir_app.py
Usa o Chrome instalado (channel="chrome"): os navegadores do Playwright nao
estao baixados nesta maquina (ENVIRONMENT.md, 2026-09-22).
Assume o cenario de 22/09 (LexML bloqueado). Se o LexML voltar, o gate
avisa e o humano decide — nao ha como ser verde e vermelho ao mesmo tempo.
"""
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "tests" / "evidencia" / "v11_passo4.png"   # evidencia de sessao, NAO versionada
SAIDA.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 1440, "height": 1600})
    pg.goto("http://localhost:8501", wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(3000)
    pg.get_by_text("Inserir palavras-chave manualmente").click()
    pg.wait_for_timeout(2000)
    ta = pg.locator("textarea").first
    ta.click(); ta.fill("LGPD\nprotecao de dados pessoais")
    pg.keyboard.press("Control+Enter"); pg.wait_for_timeout(2500)
    pg.get_by_role("button", name="Proximo >>").click(); pg.wait_for_timeout(3000)
    pg.get_by_role("button", name="Iniciar Busca").click()
    for _ in range(60):
        pg.wait_for_timeout(5000)
        if "Passo 4 - " in pg.inner_text("body"):
            break
    pg.wait_for_timeout(3000)
    pg.screenshot(path=str(SAIDA), full_page=True)
    texto = pg.inner_text("body")
    print(texto[:4000])
    b.close()

print("\n=== GATE V11 ===")
m = re.search(r"Revisar Resultados \((\d+) normativos\)", texto)
n_cab = int(m.group(1)) if m else 0
n_cards = texto.count("Ver detalhes")
checks = {
    "relatório mostra ≥1 indisponível": bool(re.search(r"·\s*[1-9]\d*\s*indisponíveis", texto)),
    "bloqueio_waf visível na tela": "bloqueio_waf" in texto,
    "aviso por fonte presente": ("indisponível (" in texto),
    "TCU declarado parcial (acórdãos 200, atos 500 — cenário de 22/09)": ("tcu respondeu parcialmente" in texto),
    "origem no card": any(o in texto for o in ("(heurística)", "(modelo)", "(fallback)")),
    "nenhum card sumiu (cards == N do cabeçalho)": n_cab > 0 and n_cards == n_cab,
    "'0 erros' não aparece": "0 erros" not in texto,   # mantido por historia; nao e o gate
}
for k, v in checks.items():
    print(f"  {'OK ' if v else 'FALHOU'} {k}")
if not checks["relatório mostra ≥1 indisponível"]:
    print("  ⚠ Se o LexML voltou a responder, este gate nao se aplica hoje — confirmar no relatório.")
assert all(v for k, v in checks.items() if k not in ("'0 erros' não aparece",)), "gate V11 reprovou"
print("GATE V11 OK — abrir e OLHAR:", SAIDA)
