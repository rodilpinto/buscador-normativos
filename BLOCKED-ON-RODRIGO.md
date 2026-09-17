---
title: "Bloqueios no humano — Buscador de Base Normativa"
maintained_by: sessões do Claude Code; só o Rodrigo resolve
last_updated: 2026-09-16
related: [_DECISOES-PENDENTES.md, _TODO.md, decisions/DECISIONS-LOG.md]
---

# Bloqueado no humano

> Índice acumulativo de ações que só o Rodrigo pode fazer (pedidos a terceiros, credenciais,
> acessos, decisões de gate). **Nunca é resetado**; item resolvido vira trilha DONE no fim.
> Entradas são índices finos — o pacote completo mora no doc da área.

---

## 🔴 B-01 · Pedir ao Alexandro um modelo de embeddings no servidor local

- **Aberto em:** 2026-09-16 · **Origem:** decisão D-C1.2 (board da consolidação, grupo 2)
- **Bloqueia:** nada agora. É **melhoria**, não pré-requisito.

**O pedido, pronto para repassar:**

> O LM Studio em `http://10.10.111.125:1234/v1` serve hoje o `google/gemma-4`, que é modelo de
> **geração**. Para o buscador agrupar resultados por assunto, precisamos também de um modelo de
> **embeddings** carregado no mesmo servidor, exposto em `/v1/embeddings`.
> Serve qualquer um multilíngue de boa qualidade — por exemplo `multilingual-e5-large`,
> `bge-m3` ou similar. São modelos pequenos (~500MB–2GB) e rodam junto com o de geração.

**Por que não trava nada.** A decisão D-C1.2 escolheu `sentence-transformers` rodando **dentro do
app** justamente para não depender desta resposta. Quando o modelo existir no servidor, a troca é
de configuração: a interface de embeddings é a mesma, muda só quem gera o vetor.

**Estado:** aguardando o Rodrigo repassar.

---

## ⏳ Também depende do humano (sem pedido formulado ainda)

- **Medir a lacuna de cobertura** das fontes catalogadas contra um tema real, antes de fechar o
  MVP. Requisito derivado do comentário do Rodrigo no grupo 5 do board
  ("ferramenta de pesquisa que não pega o máximo não é segura"). Precisa de um tema real e do
  julgamento de quem conhece o acervo — não dá para automatizar a aferição.

---

## 🔴 B-02 · Escolher entre dobrar as emendas no corpo ou construir com elas como estão

- **Aberto em:** 2026-09-16 · **Detalhe completo:** decisão **D-C9** em `_DECISOES-PENDENTES.md`
- **Bloqueia:** o início da Fase 1 (as duas opções levam à mesma primeira task, a T3).

Pergunta de uma linha, com as opções e a recomendação no ledger. Não exige pesquisa nem consulta
a terceiros — é preferência de forma.

---

## 🔴 B-03 · Autorizar o registro do repo na auto-memória do `projetos-nuati`

- **Aberto em:** 2026-09-16 · **Origem:** emenda B8 da rodada 2 adversarial
- **Bloqueia:** nada do código. Só o item de `_TODO.md` §P3.

O `~/Documents/projetos-nuati/MEMORY.md` **não existe** (verificado). O MEMORY.md real desse
projeto é a auto-memória em `~/.claude/projects/C--Users-Rodrigo-Documents-projetos-nuati/memory/`,
e a regra global `memory-write-policy` proíbe criar ou editar auto-memória sem autorização
explícita. **Pergunta ao Rodrigo:** autoriza acrescentar uma linha lá apontando para este repo?

---

## ✅ DONE

- [x] **2026-09-16 · Tag `levantamento-v1-streamlit` empurrada para o remoto.** Era o ponto de
      restauração de toda a trava anti-regressão e existia **só nesta máquina**
      (`git ls-remote --tags origin` voltava vazio). O plano só a empurrava na T9, a última task —
      até lá, perder o disco perderia o rollback. Fechado no checkpoint de 16/09; confirmado por
      `git ls-remote --tags origin`.
