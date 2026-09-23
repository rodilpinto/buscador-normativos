# Revisão final · o app real, visto pelo auditor (ui-expert, `d4cab80`, 23/09)

3 buscas ao vivo sem LLM (LGPD; licitacao + turismo; 8 keywords), LexML em `bloqueio_waf`, TCU atos em 500. 3 Excel
abertos. Prints em `tests/evidencia/final-ui/` (repo principal, ignorado). **O que funciona:** o aviso do cabeçalho do
Passo 4 é honesto e fica logo abaixo do título; a aba de diagnóstico tem data/hora, "—" e Sim/Não claros.

## Importante
1. **TCU parcial no cabeçalho, "não pôde ser consultada" no relatório:** vai para a seção vermelha "Fontes indisponíveis",
   conta em "Indisponíveis", some de "com resultados", e a planilha diz `Indisponível` — com 16 acórdãos na tela.
   → status/rótulo "Parcial" (laranja), seção e métrica próprias.
2. **A legenda do 0% é falsa:** acórdão com "…IRREGULARIDADES EM LICITAÇÃO…" na ementa dá 0% para "licitacao" —
   `_keyword_relevance` (`llm/gemini_client.py:253`) compara sem tirar acento (o filtro de busca tira).
3. **Janela de cobertura do TCU escondida:** os 500 acórdãos mais recentes (`MAX_PAGES`) = ~1 semana (todos de 16/09/2026);
   "500 itens" não diz isso. → "TCU: só os 500 acórdãos mais recentes (de dd/mm a dd/mm)…" no cabeçalho e na planilha.
4. Planilha de resultados sem coluna de **Procedência** (catalogada × web aberta — convenção do projeto); título das abas usa
   só a 1ª keyword no modo manual.
5. Relatório vira parede de debug (16 blocos vermelhos com HTML/stack Java/URLs, ~4.400px); "não consultadas" some no fim;
   o cabeçalho não diz que 3 keywords não foram à web aberta.
6. Códigos de motivo (`bloqueio_waf`, `http_5xx`, `nao_consultada`, `MAX_GOOGLE_KEYWORDS=5`) são jargão → rótulo humano +
   código entre colchetes.
7. Cards da web aberta superdimensionam o emissor: FAQ do Serpro, notícia da SETUR-DF e página do TCM-GO saem
   "Framework/Padrao · Orgao: Governo Federal" — `"gov.br": "Governo Federal"` (`google_searcher.py:101`) casa df.gov.br e
   go.gov.br.

## Menor
8. Passo 5 sem lembrete de cobertura antes de "Gerar Excel". 9. Snippets do Google com palavras coladas ("doturismoem") —
contra "texto literal"; investigar ddgs/`google_searcher.py`. 10. Rótulos sem acento (Orgao, Relevancia, Situacao, Acordao
TCU); cinza `#666` pequeno. 11. "Sem resultado" em laranja, a mesma cor do parcial. 12. Tipo da célula Relevancia varia
(int/float); Numero/Data vazios em vez de "—".
