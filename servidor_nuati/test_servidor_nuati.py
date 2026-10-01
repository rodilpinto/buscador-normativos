# -*- coding: utf-8 -*-
"""Testes do servidor_nuati. Viajam com a pasta: nao importam nada de app, nao fazem rede externa
e nao precisam de Administrador (registrar tarefa e firewall fica como conferencia manual no passe).

Rodam as funcoes de verdade no Windows PowerShell 5.1 (o do servidor), num repo descartavel com a
pasta servidor_nuati/ copiada. Fora do Windows, pulam.

Rodar da pasta que CONTEM servidor_nuati/:
    python -m pytest servidor_nuati -q
"""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

PASTA = Path(__file__).resolve().parent
PS = shutil.which("powershell")
pytestmark = pytest.mark.skipif(os.name != "nt" or PS is None, reason="precisa do Windows PowerShell")

SCRIPTS = sorted(PASTA.glob("*.ps1")) + sorted(PASTA.glob("*.cmd"))


def _ps(comando: str, cwd: Path | None = None, timeout: int = 120):
    return subprocess.run([PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", comando],
                          cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)


def _repo(tmp_path: Path, conf: str, arquivos: dict[str, str] | None = None) -> Path:
    raiz = tmp_path / "repo"
    shutil.copytree(PASTA, raiz / "servidor_nuati", ignore=shutil.ignore_patterns("__pycache__", "test_*"))
    (raiz / "servidor_nuati.conf").write_text(conf, encoding="ascii")
    for caminho, texto in (arquivos or {"app.py": "", "requirements.txt": ""}).items():
        alvo = raiz / caminho
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(texto, encoding="utf-8")
    return raiz


def _comum(raiz: Path) -> str:
    return f". '{raiz / 'servidor_nuati' / 'comum.ps1'}'; "


def _ler_conf(raiz: Path):
    r = _ps(_comum(raiz) + "Ler-Conf | ConvertTo-Json -Compress")
    return r, (json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None)


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _esperar_porta(porta: int, segundos: float = 15) -> None:
    fim = time.time() + segundos
    while time.time() < fim:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", porta)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError(f"nada escutando em {porta}")


SERVIDOR_HEALTH = r"""
import sys, http.server
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        corpo = b"ok" if self.path == "/_stcore/health" else b"nao"
        self.send_response(200); self.end_headers(); self.wfile.write(corpo)
    def log_message(self, *a): pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
"""


def _subir_servidor(porta: int, *extras: str) -> subprocess.Popen:
    p = subprocess.Popen([sys.executable, "-c", SERVIDOR_HEALTH, str(porta), *extras])
    _esperar_porta(porta)
    return p


# --- os arquivos ---------------------------------------------------------------------------

@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_scripts_so_em_ascii(script):
    """O PowerShell 5.1 le .ps1 sem BOM como ANSI: acento quebra (LICOES do checklist, 01/10)."""
    script.read_bytes().decode("ascii")


@pytest.mark.parametrize("script", sorted(PASTA.glob("*.ps1")), ids=lambda p: p.name)
def test_parser_do_powershell_aceita(script):
    r = _ps("$e = $null; [void][System.Management.Automation.Language.Parser]::ParseFile("
            f"'{script}', [ref]$null, [ref]$e); $e | ForEach-Object {{ $_.Message }}; exit $e.Count")
    assert r.returncode == 0, r.stdout + r.stderr


def test_versao_igual_no_script_no_readme_e_no_changelog():
    versao = re.search(r'\$VersaoServidorNuati = "(\d+\.\d+\.\d+)"', (PASTA / "comum.ps1").read_text()).group(1)
    assert f"**Versão {versao}**" in (PASTA / "README.md").read_text(encoding="utf-8")
    assert f"## {versao} " in (PASTA / "CHANGELOG.md").read_text(encoding="utf-8")


# --- servidor_nuati.conf ----------------------------------------------------------------------

def test_conf_minima_usa_os_padroes(tmp_path):
    raiz = _repo(tmp_path, "NOME_TAREFA=MeuApp\nPORTA=8409\n")
    r, conf = _ler_conf(raiz)
    assert r.returncode == 0, r.stdout + r.stderr
    assert conf["NOME_TAREFA"] == "MeuApp" and conf["PORTA"] == 8409
    assert Path(conf["PASTA_APP_ABS"]) == raiz
    assert conf["ARQUIVO_APP"] == "app.py" and conf["RAMO"] == "main"
    assert conf["LOG_MAX_BYTES"] == 20 * 1024 * 1024
    assert Path(conf["REQUIREMENTS_ABS"]) == raiz / "requirements.txt"


def test_conf_com_app_em_subpasta_como_o_buscador(tmp_path):
    raiz = _repo(tmp_path, "# buscador\nNOME_TAREFA=BuscadorNormativos\nPORTA = 8404\n"
                           "PASTA_APP=levantamento-normativos\nLOG_MAX_MB=5\n",
                 {"levantamento-normativos/app.py": "", "levantamento-normativos/requirements.txt": ""})
    r, conf = _ler_conf(raiz)
    assert r.returncode == 0, r.stdout + r.stderr
    assert Path(conf["PASTA_APP_ABS"]) == raiz / "levantamento-normativos"
    assert Path(conf["REQUIREMENTS_ABS"]) == raiz / "levantamento-normativos" / "requirements.txt"
    assert conf["LOG_MAX_BYTES"] == 5 * 1024 * 1024


@pytest.mark.parametrize("conf,mensagem", [
    ("PORTA=8409\n", "NOME_TAREFA"),
    ("NOME_TAREFA=Meu App\nPORTA=8409\n", "NOME_TAREFA"),
    ("NOME_TAREFA=X\n", "PORTA"),
    ("NOME_TAREFA=X\nPORTA=80\n", "PORTA"),
    ("NOME_TAREFA=X\nPORTA=oito\n", "PORTA"),
    ("NOME_TAREFA=X\nPORTA=8409\nPOTRA=8410\n", "chave desconhecida 'POTRA'"),
    ("NOME_TAREFA=X\nPORTA=8409\nisto nao e chave\n", "linha 3"),
    ("NOME_TAREFA=X\nPORTA=8409\nPASTA_APP=nao-existe\n", "PASTA_APP nao existe"),
    ("NOME_TAREFA=X\nPORTA=8409\nARQUIVO_APP=outro.py\n", "ARQUIVO_APP"),
    ("NOME_TAREFA=X\nPORTA=8409\nREQUIREMENTS=req.txt\n", "REQUIREMENTS"),
    ("NOME_TAREFA=X\nPORTA=8409\nLOG_MAX_MB=0\n", "LOG_MAX_MB"),
])
def test_conf_errada_para_com_mensagem_clara(tmp_path, conf, mensagem):
    r, _ = _ler_conf(_repo(tmp_path, conf))
    assert r.returncode == 1
    assert "[ERRO]" in r.stdout and mensagem in r.stdout


def test_sem_conf_explica_o_que_fazer(tmp_path):
    raiz = _repo(tmp_path, "")
    (raiz / "servidor_nuati.conf").unlink()
    r, _ = _ler_conf(raiz)
    assert r.returncode == 1 and "servidor_nuati.conf.example" in r.stdout


def test_configuracao_do_app_fica_dentro_da_pasta_do_app(tmp_path):
    raiz = _repo(tmp_path, "NOME_TAREFA=X\nPORTA=8409\nPASTA_APP=sub\n",
                 {"sub/app.py": "", "sub/requirements.txt": "", ".env": "na raiz nao vale"})
    cmd = _comum(raiz) + "$c = Ler-Conf; $a = Achar-Configuracao $c; if ($a) { $a } else { 'NENHUMA' }"
    assert _ps(cmd).stdout.strip() == "NENHUMA"
    (raiz / "sub" / ".streamlit").mkdir()
    (raiz / "sub" / ".streamlit" / "secrets.toml").write_text("X = 1\n")
    assert _ps(cmd).stdout.strip() == ".streamlit/secrets.toml"


def test_ramo_errado_recusa(tmp_path):
    raiz = _repo(tmp_path, "NOME_TAREFA=X\nPORTA=8409\n")
    git = ["git", "-C", str(raiz)]
    subprocess.run(git + ["init", "-q", "-b", "homologacao"], check=True)
    r = _ps(_comum(raiz) + "$c = Ler-Conf; Exigir-Ramo $c; 'PASSOU'")
    assert r.returncode == 1 and "'homologacao'" in r.stdout and "PASSOU" not in r.stdout
    subprocess.run(git + ["switch", "-q", "-c", "main"], check=True)
    assert _ps(_comum(raiz) + "$c = Ler-Conf; Exigir-Ramo $c; 'PASSOU'").stdout.strip() == "PASSOU"


# --- processo na porta e saude --------------------------------------------------------------------

def test_parar_app_recusa_matar_outro_programa(tmp_path):
    raiz = _repo(tmp_path, "NOME_TAREFA=X\nPORTA=8409\n")
    porta = _porta_livre()
    outro = _subir_servidor(porta)
    try:
        r = _ps(_comum(raiz) + f"Parar-App 'TarefaQueNaoExiste' {porta}; 'PASSOU'")
        assert r.returncode == 1 and "ocupada por outro programa" in r.stdout
        assert outro.poll() is None   # continua vivo
    finally:
        outro.kill()


def test_parar_app_encerra_o_streamlit_da_porta(tmp_path):
    raiz = _repo(tmp_path, "NOME_TAREFA=X\nPORTA=8409\n")
    porta = _porta_livre()
    falso = _subir_servidor(porta, "streamlit", "--server.port", str(porta))   # linha de comando de Streamlit
    try:
        r = _ps(_comum(raiz) + f"Parar-App 'TarefaQueNaoExiste' {porta}; 'PASSOU'")
        assert r.returncode == 0 and "PASSOU" in r.stdout, r.stdout + r.stderr
        falso.wait(timeout=10)
    finally:
        falso.kill()


def test_parar_app_nao_confunde_porta_com_prefixo(tmp_path):
    """--server.port 84091 nao e o Streamlit da porta 8409."""
    raiz = _repo(tmp_path, "NOME_TAREFA=X\nPORTA=8409\n")
    porta = _porta_livre()
    outro = _subir_servidor(porta, "streamlit", "--server.port", f"{porta}1")
    try:
        r = _ps(_comum(raiz) + f"Parar-App 'TarefaQueNaoExiste' {porta}")
        assert r.returncode == 1 and outro.poll() is None
    finally:
        outro.kill()


def test_esperar_app(tmp_path):
    raiz = _repo(tmp_path, "NOME_TAREFA=X\nPORTA=8409\n")
    porta = _porta_livre()
    servidor = _subir_servidor(porta)
    try:
        assert _ps(_comum(raiz) + f"Esperar-App {porta} 10").stdout.strip() == "True"
    finally:
        servidor.kill()
    assert _ps(_comum(raiz) + f"Esperar-App {_porta_livre()} 2").stdout.strip() == "False"


# --- iniciar.cmd ------------------------------------------------------------------------------

def test_iniciar_cmd_entra_na_pasta_do_app_e_roda_o_log(tmp_path):
    """Sobe com um .venv sem streamlit: o comando falha logo, mas o log mostra pasta, arquivo e porta."""
    raiz = _repo(tmp_path, "NOME_TAREFA=X\nPORTA=8409\n", {"sub/app.py": "", "sub/requirements.txt": ""})
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(raiz / ".venv")], check=True, timeout=120)
    logs = raiz / "logs"
    logs.mkdir()
    (logs / "app.log").write_text("x" * 200)
    r = subprocess.run(["cmd", "/c", str(raiz / "servidor_nuati" / "iniciar.cmd"), "8499", str(raiz / "sub"),
                        "app.py", "100"], capture_output=True, text=True, timeout=120)
    assert r.returncode != 0                                     # sem streamlit no .venv
    assert (logs / "app.log.1").read_text() == "x" * 200         # o log grande virou .1
    novo = (logs / "app.log").read_text(encoding="utf-8", errors="replace")
    assert f"iniciando app.py na porta 8499 em {raiz / 'sub'}" in novo
    assert "No module named streamlit" in novo


def test_iniciar_cmd_sem_argumentos_explica_o_uso():
    r = subprocess.run(["cmd", "/c", str(PASTA / "iniciar.cmd")], capture_output=True, text=True, timeout=30)
    assert r.returncode == 2 and "uso: iniciar.cmd" in r.stdout
