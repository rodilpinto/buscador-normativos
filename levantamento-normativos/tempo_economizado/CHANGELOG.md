# Changelog do tempo_economizado

Versão atual em `__init__.py` (`__version__`).

## 1.0.0 (30/09/2026): nasce no nuati-framework

Base escolhida pelo Rodrigo (F-A2, board `decisions/board-2026-09-29-1933-tempo-economizado.html`, 30/09): o modelo
de `analise-fracionamento-dispensa`, `nualc/report.py`, função `estimativa_ganho` (@ `91f3e67`): lista de (etapa,
quantidade medida, minutos por unidade), menos o tempo da execução automática. Código novo, escrito a partir dele (não
é cópia):

- `Etapa` e `estimar()` fazem a mesma conta; `Estimativa` traz também `economia_dias_uteis(horas_por_dia)` (o
  fracionamento usa `HORAS_DIA_UTIL`).
- Explicação do checklist (`app.py:499-565` @ `92ac158`: tabela "Como calculamos essa estimativa?" num expander)
  reescrita em linguagem simples, como pedido junto com a decisão: a frase "à mão X, a ferramenta Y, a diferença é o
  poupado" vem antes da tabela; colunas "Quantas vezes / Tempo de cada / Total"; nota final curta.
- 📝 Texto da nota padrão (`NOTA_PADRAO`) e do título do dropdown ("Como chegamos a esse número?") propostos pelo
  Claude; trocáveis por parâmetro.
- Testes reescrevem os 4 modelos de 29/09 nesta base e conferem o mesmo número: fracionamento, checklist (50 itens →
  7h30min; ⚠ as 8 etapas de lá somam 9,0 min por item, embora o comentário do código diga 8,0), scopediagram (9,4 h no
  exemplo) e DOU/pesquisa_diario (10 termos × 3 datas → 32,5 min).
