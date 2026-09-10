> Material transversal extraído do plano; citado pelos arquivos de task. Fonte: docs/superpowers/plans/2026-09-08-buscador-normativos.md

# Buscador de Base Normativa — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir um app web local que, a partir de um tema, pesquisa normativos em fontes catalogadas e na web aberta, e entrega uma lista **triável em poucas decisões humanas**, baixando e organizando só o que sobrevive à triagem.

**Architecture:** Pipeline de 6 etapas com estado em SQLite, o que torna cada etapa retomável. Adaptadores de fonte isolados atrás de um protocolo comum, cada um com fixture HTML salva e teste de contrato. O LLM é opcional atrás de um protocolo: com `NullLLM` o sistema roda inteiro. A interface web é FastAPI + Jinja2 + JS puro, sem framework de frontend.

**Tech Stack:** Python 3.13 · FastAPI · Jinja2 · sqlite3 (stdlib) · httpx · selectolax · openpyxl · pytest

**Spec:** `docs/superpowers/specs/2026-09-08-buscador-normativos-design.md`

## Global Constraints

- **Python:** `C:\Users\P_8106\AppData\Local\Programs\Python\Python313\python.exe`. Rodar via **Bash**, não PowerShell — caminhos acentuados quebram no PowerShell 5.1.
- **Encoding:** todo arquivo `.py` é UTF-8. Todo `open()` passa `encoding="utf-8"` explicitamente.
- **Windows, limite de 260 caracteres:** nomes de pasta de tema no máximo **32 caracteres**; toda operação de arquivo usa o helper `caminho_longo()` da Task 13. Acima de 260 o Python falha **em silêncio** (`isfile` devolve `False`).
- **Texto normativo nunca é parafraseado.** Título e ementa são copiados literalmente da fonte. Texto derivado de LLM vai para campo separado (`ementa_llm`), nunca sobrescreve `ementa`.
- **Procedência obrigatória** em todo resultado: `catalogada` ou `web-aberta`.
- **O sistema roda inteiro sem LLM.** Nenhum caminho de código pode exigir chave de API.
- **Web aberta nunca é pré-marcada `fica`** (mitigação de risco da spec §7).
- **Item `obrigatorio` nunca é pré-marcado `sai`** (mitigação de ancoragem, spec §7).
- Commits frequentes, um por task no mínimo.

---

## File Structure

| Arquivo | Responsabilidade |
|---|---|
| `buscador/config.py` | Configuração, caminhos, catálogo de fontes |
| `buscador/db.py` | Schema SQLite, conexão, migração |
| `buscador/modelos.py` | Dataclasses do domínio |
| `buscador/normalizar.py` | Normalização de URL/título, chave de dedup |
| `buscador/llm.py` | Protocolo LLM + `NullLLM` + adaptador OpenAI-compatível |
| `buscador/palavras_chave.py` | Expansão de tema em termos de busca |
| `buscador/fontes/base.py` | Protocolo `Fonte` e `ResultadoBruto` |
| `buscador/fontes/planalto.py` | Adaptador do Planalto |
| `buscador/fontes/legin_camara.py` | Adaptador do Legin (Câmara) |
| `buscador/fontes/tcu.py` | Adaptador do portal do TCU |
| `buscador/fontes/web_aberta.py` | Busca genérica, rede de segurança |
| `buscador/acervo.py` | Índice sha256 do acervo existente, selo já-tenho |
| `buscador/premarcacao.py` | Regras de pré-marcação com justificativa |
| `buscador/busca.py` | Orquestrador da busca |
| `buscador/download.py` | Download, sha256, organização por tema, duplicatas |
| `buscador/planilha.py` | Planilha-registro openpyxl |
| `buscador/web/app.py` | FastAPI: rotas |
| `buscador/web/templates/` | Jinja2 |
| `buscador/cli.py` | CLI |
