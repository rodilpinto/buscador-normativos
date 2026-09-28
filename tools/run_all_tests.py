# -*- coding: utf-8 -*-
"""Roda todas as suites registradas do app e devolve um exit code confiavel.

Quantas e quais suites: ver SUITES_SCRIPT e SUITES_PYTEST abaixo — a docstring
nao repete o numero de proposito, para nao ficar falsa quando uma suite entrar
(a emenda C2 pegou exatamente esse defeito no plano).

A maioria das suites sao scripts com helper record() e NAO sao pytest: elas
imprimem um resumo no fim e o processo sai. As de SUITES_PYTEST sao pytest. Este runner normaliza
as duas formas num unico resultado, e compara cada suite com a linha de base
(BASELINE) para que uma suite que ENCOLHEU nao passe como verde.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "levantamento-normativos"

# ⚠ Cada suite-script imprime o resumo num formato DIFERENTE. Verificado em
# 2026-09-16 rodando as tres. Um regex generico casa so uma delas e devolve
# zero teste para as outras duas, o que passaria como sucesso silencioso.
# Cada padrao captura (passed, failed) NESSA ordem.
SUITES_SCRIPT = {
    # Results: 13/13 passed, 0/13 failed
    "test_searchers.py": re.compile(r"Results:\s*(\d+)/\d+\s*passed,\s*(\d+)/\d+\s*failed"),
    # Total: 53  |  PASS: 53  |  FAIL: 0
    "test_llm_phase3.py": re.compile(r"Total:\s*\d+\s*\|\s*PASS:\s*(\d+)\s*\|\s*FAIL:\s*(\d+)"),
    # Total: 98 | Passed: 98 | Failed: 0
    "test_comprehensive.py": re.compile(
        r"Total:\s*\d+\s*\|\s*Passed:\s*(\d+)\s*\|\s*Failed:\s*(\d+)"
    ),
}
# Nasceu com UMA suite pytest (emenda B2): test_backends.py so existe a partir
# da Task 5/6, e registra-la antes faria o pytest sair com 4 (arquivo ausente)
# e o runner acusar regressao onde nao houve. Pela mesma regra, cada suite entra
# aqui no commit que a CRIA: tests/test_fontes_indisponiveis.py entrou na frente 2
# (Task 2, 2026-09-23) — sem rede, requests.get e time.sleep dublados.
SUITES_PYTEST = ["test_phase4.py", "tests/test_fontes_indisponiveis.py", "tests/test_cadeia_llm.py"]

PADRAO_PYTEST = re.compile(r"(\d+) passed")

# Linha de base medida em 2026-09-16 (e re-medida em 2026-09-22, apos o merge).
# E um PISO, nao igualdade (emenda B3): teste novo e legitimo nao pode virar
# vermelho. Mas piso sozinho apodrece (emenda C1): crescimento e sinalizado, e
# suite registrada SEM entrada aqui e erro, nao silencio.
# Regra: mudanca intencional de composicao atualiza este dict NO MESMO COMMIT
# que acrescenta o teste — o aviso de crescimento existe para lembrar disso.
BASELINE = {
    "test_searchers.py": 13,
    "test_llm_phase3.py": 65,   # revisao final FIX-FONTES (23/09): +1 (F-UX2, relevancia sem acento)
    "test_comprehensive.py": 98,
    "test_phase4.py": 94,   # T9: +1 (origem curta do app) +2 (escape da tela, item carregado T2/T3) +2 (review: _md_html no card, aviso da web aberta) ; FIX-SAIDA: +14 (N1 +1, S-SEC +2, N8 +3, UX1+N3 +5, N9 +3); review FIX-SAIDA: +4 (char de controle)
    "tests/test_cadeia_llm.py": 14,   # 23/09: cadeia A > B > C (7); 25/09: rodizio de modelos, presets, chave do usuario (7 -> 14)
    "tests/test_fontes_indisponiveis.py": 66,   # T2: 16 + 1 da review; T3: +9 + 3 da review; T4: +3, o xfail vira passed, +2 do tester (colegiados) +1 da review (M5); T5: +8 + 1 (log sem chave do CSE)
    # ^ revisao final FIX-FONTES (23/09): 45 -> 60, +15 = F-N2 3, F-M2 1, F-N4 1, F-N5 3, F-UX3 1, F-MT503 1, F-MT1 1, F-MT3 1, F-SSRF 3
    # ^ review da FIX-FONTES (23/09): 60 -> 66, +6 = SSRF todos os enderecos 2, found_by exato 2 (TCU, LexML), duplicatas do Google 1, janela no singular 1
}


def _rodar(cmd: list[str]) -> tuple[int, str, float]:
    """Devolve (exit code, saida, segundos).

    O tempo entra na tabela porque a primeira execucao completa (2026-09-22)
    levou 8m53s: as suites LIVE batem em LexML (bloqueado por WAF) e TCU (500
    com retries). Sem o tempo por suite, "o runner esta lento" nao tem onde
    ser investigado.
    """
    inicio = time.monotonic()
    # 'roda sem LLM' so e garantido se o runner nao herdar a chave (rodada 2: test_comprehensive achou GEMINI_API_KEY no ambiente e levou 429 do Gemini)
    # ⚠ st.secrets VENCE a variavel vazia: se existir
    # levantamento-normativos/.streamlit/secrets.toml (hoje so ha o .example),
    # as suites achariam a chave ali e chamariam o LLM de verdade. O conserto
    # de codigo e da frente 5 (plano frente 2, Global Constraints).
    proc = subprocess.run(
        cmd, cwd=APP, env={**os.environ, "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""},
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return proc.returncode, proc.stdout + proc.stderr, time.monotonic() - inicio


def main() -> int:
    linhas: list[tuple[str, int, int, float]] = []
    falhou = False

    for s, padrao in SUITES_SCRIPT.items():
        # emenda A5: o exit code NAO e descartado. test_llm_phase3.py restaura
        # o ambiente DEPOIS de imprimir o resumo; se essa linha levantar, o
        # resumo esta verde e o processo sai != 0. So o regex nao pegaria.
        code, saida, seg = _rodar([sys.executable, s])
        m = padrao.search(saida)
        if not m:
            # Resumo ilegivel e FALHA, nunca "zero teste, tudo bem": a suite pode
            # ter morrido antes de imprimir, ou mudado de formato.
            print(f"[ERRO] {s}: nao consegui ler o resumo final (exit {code})")
            falhou = True
            continue
        passed, failed = int(m.group(1)), int(m.group(2))
        linhas.append((s, passed, failed, seg))
        if failed or passed == 0:
            falhou = True
        if code != 0:
            print(f"[ERRO] {s}: resumo verde mas o processo saiu com exit {code}")
            falhou = True

    for s in SUITES_PYTEST:
        code, saida, seg = _rodar([sys.executable, "-m", "pytest", s, "-q"])
        m = PADRAO_PYTEST.search(saida)
        passed = int(m.group(1)) if m else 0
        linhas.append((s, passed, 0 if code == 0 else 1, seg))
        if code != 0:
            falhou = True

    largura = max(len(n) for n, _, _, _ in linhas) if linhas else 20
    print()
    print(f"{'suite'.ljust(largura)} | passed | failed | baseline |   tempo")
    print("-" * (largura + 39))
    for nome, p, f, seg in linhas:
        esperado = BASELINE.get(nome)
        print(
            f"{nome.ljust(largura)} | {str(p).rjust(6)} | {str(f).rjust(6)} | "
            f"{str(esperado if esperado is not None else '?').rjust(8)} | {seg:6.1f}s"
        )
        # emendas A9 + B3 + C1, no laco de impressao (C3): aqui `nome` existe.
        if esperado is None:
            print(f"[ERRO] {nome} esta no runner mas nao tem entrada no BASELINE — sem protecao contra encolhimento")
            falhou = True
        elif p < esperado:
            print(f"[ERRO] {nome} encolheu: baseline {esperado}, agora {p}")
            falhou = True
        elif p > esperado:
            print(f"[AVISO] {nome} cresceu: baseline {esperado} -> {p}; atualize o BASELINE neste commit")
    print()
    print("TUDO VERDE" if not falhou else "HOUVE FALHA")
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
