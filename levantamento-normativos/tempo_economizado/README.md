# tempo_economizado: quanto trabalho manual o app poupou (pasta copiável)

**Versão 1.0.0** · **Origem:** `github.com/rodilpinto/nuati-framework` (privado), pasta `tempo_economizado/`.
Histórico: [`CHANGELOG.md`](CHANGELOG.md). Regras de cópia e registro de onde há cópias: README da raiz do framework.

Uma conta só, igual em todos os apps, para a linha "tempo de trabalho manual poupado" e para a explicação de onde
saiu o número. Base escolhida pelo Rodrigo em 30/09 (F-A2): o modelo do `analise-fracionamento-dispensa`.

## A conta

Cada **etapa** do trabalho que a pessoa faria à mão tem:

- **quantas vezes** ela se repete neste resultado (o app mede: itens gerados, casos, termos, subprocessos…);
- **quanto tempo** leva cada vez (estimativa do app, em minutos).

```
tempo à mão    = soma de (quantas vezes × tempo de cada) de todas as etapas
tempo poupado  = tempo à mão − tempo que a ferramenta levou   (nunca negativo)
```

Cada etapa tem sua própria quantidade. Um app em que tudo escala pelo número de itens (o checklist) usa a mesma
quantidade em todas as linhas; um app com elementos de tipos diferentes (o scopediagram) usa uma quantidade por
tipo. Os testes reescrevem os quatro modelos que existiam em 29/09 (checklist, fracionamento, scopediagram,
DOU/pesquisa_diario) nesta base e conferem que dão o mesmo número de antes.

## O que o usuário vê

Uma linha e um dropdown:

> ⏱️ Tempo de trabalho manual poupado: cerca de 8h38min
>
> ▸ **Como chegamos a esse número?**
>
> Se uma pessoa fizesse este trabalho à mão, levaria cerca de **8h40min**. A ferramenta fez em **2 min**. A diferença,
> **8h38min**, é o tempo poupado.
>
> Para cada etapa do trabalho manual, a conta é: **quantas vezes a etapa se repete neste resultado × quanto tempo leva
> cada vez**.
>
> | Etapa do trabalho manual | Quantas vezes | Tempo de cada | Total |
> |:--|--:|--:|--:|
> | Classificar cada item sem código | 200 itens | 2 min | 6h40min |
> | Documentar cada caso | 8 casos | 15 min | 2h |
> | **Total à mão** | | | **8h40min** |
> | Menos o tempo da ferramenta | | | − 2 min |
> | **Tempo poupado** | | | **8h38min** |
>
> Os tempos de cada etapa são estimativas de referência de quem faz esse trabalho, não cronometragens. O número serve
> para dar a ordem de grandeza do tempo poupado.

A ordem é de propósito (pedido do Rodrigo, 30/09: *"eli5 … não ter fricção e nem levantar questionamentos
desnecessários"*): primeiro a história em uma frase, depois a conta linha a linha em palavras do dia a dia, e por fim
uma frase curta dizendo de onde vêm os tempos. Sem tempo da ferramenta informado, as linhas de desconto somem.

## Adotar num app

1. **Copie a pasta inteira** `tempo_economizado/` para a raiz do app (ao lado do `app.py`), sem editar nada, e
   registre a cópia no README da raiz do framework ("Registro de cópias").
2. **Declare as etapas do app** no código do app (não na pasta): descrição do que a pessoa faria à mão, a quantidade
   medida no resultado e os minutos de cada vez. Escreva a descrição como quem faz o trabalho ("Ler cada artigo do
   normativo"), porque ela aparece na tabela.
3. **Mostre** com o painel pronto, ou monte o seu com `resumo()` e `explicar()`:

```python
from tempo_economizado import Etapa, estimar
from tempo_economizado.painel_streamlit import mostrar_tempo_economizado

n = len(itens)
est = estimar([
    Etapa("Ler e interpretar cada dispositivo legal", n, 2.0),
    Etapa("Avaliar probabilidade e impacto de cada item", n, 1.5),
    Etapa("Documentar cada caso de interesse", n_casos, 15.0, unidade="caso"),
], automatico_min=duracao_da_geracao_em_min)     # 0 = não informado
mostrar_tempo_economizado(est)                    # nada aparece se ainda não há resultado
```

4. Rode, da pasta que contém `tempo_economizado/`: `python -m pytest tempo_economizado -q`.

| Peça | O que faz |
|---|---|
| `Etapa(descricao, quantidade, minutos_por_unidade, unidade="item", unidade_plural="")` | uma linha da conta; plural automático (`item`→`itens`, `caso`→`casos`, `regulador`→`reguladores`) ou informado |
| `estimar(etapas, automatico_min=0)` | devolve `Estimativa` com `manual_min`, `economia_min`, `economia_horas`, `economia_dias_uteis(8)` |
| `formatar_tempo(min)` | `35 s`, `1,5 min`, `45 min`, `1h`, `7h30min` |
| `resumo(est)` | a linha "Tempo de trabalho manual poupado: cerca de …" |
| `explicar(est, nota=...)` | o Markdown do dropdown; `nota=""` tira a frase final, ou troque o texto (ex.: quando os tempos forem medidos) |
| `painel_streamlit.mostrar_tempo_economizado(est)` | linha + dropdown "Como chegamos a esse número?" |

Dependências: nenhuma para a conta; `streamlit` só para `painel_streamlit.py`.

## Regra de sincronia

**Não edite uma cópia.** Melhoria nasce no framework, sobe `__version__`, entra no `CHANGELOG.md` e é recopiada.
Os tempos por etapa são do app (ficam no código dele), não desta pasta.
