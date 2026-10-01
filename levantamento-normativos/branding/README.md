# Identidade Visual dos Apps NUATI (Câmara dos Deputados)

Guia de referência para **todos os aplicativos** do Núcleo de Auditoria de TI. É a aplicação digital do **Manual de Identidade Visual (MIV) da Câmara dos Deputados, versão 4.00, dez/2025**, e não uma marca nova: o MIV p.22 proíbe criar marcas ou selos próprios para unidades, serviços e produtos de comunicação interna.

- **Fonte primária:** [`fonte/MIV_Camara_dos_Deputados_v4.00_dez2025.pdf`](fonte/MIV_Camara_dos_Deputados_v4.00_dez2025.pdf), baixado de www2.camara.leg.br/comunicacao/assessoria-de-imprensa/uso-da-marca (o atalho `cd.leg.br/marca` redireciona para lá).
- **Arquivos oficiais da marca:** `RGB_Logotipo_Camara_dos_Deputados.zip`, na mesma página. Os SVGs estão em [`assets/logos/`](assets/logos/).
- **Valores legíveis por máquina:** [`tokens.json`](tokens.json) (cada valor traz a fonte e o status).

**Versão 1.0.0** · **Origem:** `github.com/rodilpinto/nuati-framework` (privado), pasta `branding/`. Histórico:
[`CHANGELOG.md`](CHANGELOG.md). Regras de cópia e registro de onde há cópias: README da raiz do framework.

## Como adotar num app

1. **Copie a pasta inteira** `branding/` para a raiz do app (ao lado do `app.py`), sem editar nada, e registre a cópia
   no README da raiz do framework ("Registro de cópias").
2. **App Streamlit:**
   - copie `branding/streamlit_cd/config.toml` para `.streamlit/config.toml` (se o app já tiver um, junte as seções:
     o `[theme]` vem daqui);
   - no `app.py`:
     ```python
     from branding.streamlit_cd import cd_brand
     cd_brand.configurar_pagina("Nome do App")       # primeira chamada st.*
     cd_brand.cabecalho("Nome do App", "Descrição curta")
     # ... conteúdo ...
     cd_brand.rodape()
     ```
3. **App web (HTML/CSS):** importe `branding/tokens.css` e use as variáveis `--cd-*`.
4. Rode, da pasta que contém `branding/`: `python -m pytest branding -q`.

Dependências: `streamlit` (só para `streamlit_cd/`); o resto é CSS, JSON, SVG e PNG.

Ao atualizar o guia, atualize primeiro o `tokens.json` e depois `tokens.css` e `streamlit_cd/config.toml`.

## Legenda de status

- ✅ **Oficial:** está no MIV (página citada).
- 🌐 **Adaptação digital:** observado no portal camara.leg.br (CSS de 22/09/2026). Usado quando a cor oficial não atinge o contraste mínimo para texto em tela.
- 📝 **Proposta:** decisão deste guia, ainda sem validação da Comid.

## Cores

| Token | Hex | Status | Uso |
|---|---|---|---|
| `verde-cd` | `#00B142` | ✅ MIV p.5 | Logo, faixas e elementos decorativos. **Não usar em texto:** contraste de 2,85:1 sobre branco, abaixo do mínimo WCAG AA de 4,5:1 |
| `azul-cd` | `#0095D4` | ✅ MIV p.5 | Logo e destaques gráficos grandes (3,36:1). Não usar em texto corrido |
| `cinza-cd` | `#414042` | ✅ MIV p.5 | Texto principal e assinatura de unidades (10,31:1) |
| `branco-cd` | `#FFFFFF` | ✅ MIV p.5 | Fundo. O manual imprime "HEX 00000", que é erro de digitação: o RGB é 255 255 255 |
| `verde-acao` | `#2F7958` | 🌐 | Botões primários, links e foco (5,25:1) |
| `verde-escuro` | `#004A2F` | 🌐 | Cabeçalho e rodapé com texto branco (10,39:1) |
| `verde-tinta` | `#E5F7EC` | 🌐 (amostrado das faixas do próprio MIV p.8) | Fundo secundário, sidebar e cards |
| `texto-suave` | `#6D6C6F` | 📝 | Legendas e textos auxiliares (5,22:1) |
| `borda` | `#D6D6D6` | 🌐 | Bordas e divisores |
| `erro` | `#DC3545` | 🌐 | Mensagens de erro (4,53:1) |

Cores de domínio, como os níveis de risco MCGR (Baixo/Moderado/Alto/Muito alto), ficam fora deste guia e seguem a metodologia de cada app.

## Tipografia

- ✅ **REM** (MIV p.4, disponível no Google Fonts). Nas assinaturas de unidades, usar a variação Regular (MIV p.14).
- 📝 Fallback: `system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif`.

## Logo

| Uso | Arquivo | Regra |
|---|---|---|
| Padrão sobre fundo claro | `camara-h2-colorida.svg` | ✅ Versão Preferencial (MIV p.8) |
| Sobre fundo escuro (cabeçalho) | `camara-h2-filetada-branco.svg` | ✅ Versões filetadas podem ser usadas sobre cores sólidas (MIV p.8) |
| Espaço horizontal estreito | `camara-h1-*.svg` | ✅ Variante Horizontal |
| Favicon / ícone | `camara-i-*.svg`, `assets/favicon/` | ✅ A Variante Ícone é de uso exclusivo da comunicação interna (MIV p.8) |

- ✅ Altura mínima em tela: **20 px** (ícone: 16 px) (MIV p.11).
- ✅ Área de proteção: **metade da altura do símbolo** livre ao redor (MIV p.10).
- ✅ Não alterar cores, proporções, contorno ou tipografia, nem a posição do ícone. Usar só os arquivos oficiais (MIV p.12).

## Assinatura da unidade (rodapé)

✅ Na comunicação com o público interno, a assinatura da unidade é facultativa, desde que acompanhe o logo na Versão Preferencial (MIV p.14). Regras:

- **Sem siglas** (MIV p.14): escrever "Núcleo de Auditoria de TI", nunca "NUATI"; "Secretaria de Controle Interno", nunca "SECIN".
- Texto em **Cinza CD**, alinhado à direita e centralizado verticalmente, em até 3 linhas (MIV p.15).
- Logo **à direita** do conjunto de assinaturas, respeitando a hierarquia entre as unidades (MIV p.16).
- ✅ Comunicação com o **público externo** não leva assinatura de unidade (MIV p.14). Apps abertos ao público devem mostrar só a marca da Câmara.

Padrão usado nos apps NUATI (`cd_brand.rodape()`):

```
                    Secretaria de Controle Interno  [LOGO CÂMARA
                         Núcleo de Auditoria de TI   DOS DEPUTADOS]
```

## Layout base dos apps (📝 proposta)

- Cabeçalho: faixa `verde-escuro`, título do app em branco (REM 600), logo filetado branco à direita e filete inferior de 4 px em `verde-cd`.
- Conteúdo: fundo branco, sidebar em `verde-tinta`, botões primários em `verde-acao`.
- Rodapé: assinatura da unidade mais o logo preferencial, como acima.
- Título da aba do navegador: `<Nome do App> | Câmara dos Deputados`; favicon oficial.

## Pendências

- 📝 Confirmar com a Comid (publicidade@camara.leg.br) se ferramentas internas precisam de autorização prévia para usar a marca. O MIV p.21 exige isso para peças produzidas externamente; a regra para peças internas (p.20) não ficou explícita na extração de texto.
- 📝 Confirmar a hierarquia e a grafia oficiais das unidades na assinatura.
