# Triagem da revisão final (orquestrador, 23/09)

> Critério: **entra agora** o que é falha de segurança ou o que faz a tela/planilha **afirmar algo falso** sobre o que foi
> consultado, achado ou pontuado (o objetivo da frente 2). **Vai para depois** o que é explicabilidade/rótulo humano
> (frente 4), feature nova (Fase 2) ou refatoração sem mentira visível (P3). 📝 Triagem minha — o Rodrigo pode revertê-la.

## Entra agora — em duas trilhas paralelas (arquivos disjuntos, só `tools/run_all_tests.py` em comum)

### Trilha FIX-FONTES (`../bn-fix-fontes`, branch `frente2/fix-fontes`, porta 8541) — searchers, base, heurística
| id | origem | o quê |
|---|---|---|
| F-N2 | spec N2 | LexML: XML válido que não é `searchRetrieveResponse`, ou com `srw:diagnostics` → `resposta_ilegivel` com a mensagem |
| F-M2 | spec (sobe T2 M2) | LexML: WAF/HTML no `_sru_url` cacheado entra em `_urls_mortos` e tenta a cadeia |
| F-N4 | spec N4 | TCU: keyword que casa acórdão já trazido por outra sai `ok` (conta matches), e `found_by` acumula |
| F-N5 | spec N5 | os 3 searchers: a keyword em curso cortada por `max_results` sai `parcial=True` com "cortado em max_results" |
| F-UX3 | ux 3 | TCU: janela de cobertura no detalhe ("os N acórdãos mais recentes, de dd/mm/aaaa a dd/mm/aaaa") |
| F-UX2 | ux 2 | heurística de relevância sem acento (reusar a normalização do filtro) |
| F-SSRF | seg. alto + baixo | Google `_fetch_page_metadata`: sem redirect automático, revalidar cada `Location`; limitar bytes lidos |
| F-MT1 | manut. 1 | `FonteIndisponivel` valida contra `models.MOTIVOS` (fim da cópia `_CONHECIDOS`) |
| F-MT3 | manut. 3 | detalhe do `bloqueio_waf` do scraping não afirma "seguidas" |
| F-MT503 | manut. perda | 503 dentro da janela: detalhe ganha "tente de novo após 21h BRT" |
| F-T1 | testes alto | `test_lexml_cql_injection_sanitization` dublado (sem rede) |

### Trilha FIX-SAÍDA (`../bn-fix-saida`, branch `frente2/fix-saida`, porta 8551) — app, planilha, models
| id | origem | o quê |
|---|---|---|
| S-SEC | seg. **crítico** | aba Normativos: nenhuma célula vira fórmula — manter o texto LITERAL (sem acrescentar `'`: forçar tipo string), em todas as colunas de texto |
| S-N1 | spec **bloqueador** | aviso "Nenhuma fonte catalogada entregou" só quando TODAS as catalogadas morreram; AppTest "LexML morto, TCU saudável" |
| S-UX1+N3 | ux 1 + spec N3 | "parcial" deixa de ser "indisponível": rótulo **"Parcial"** na tela e na planilha para `error`+`parcial`; seção/métrica próprias; parcial sem match → `st.warning`, sem "com sucesso". ⚠ se o hash do golden mudar, PARAR e reportar |
| S-N8 | spec N8 | aba de diagnóstico: keyword gravada literal (só neutralizar fórmula, sem redigir segredo nela) |
| S-N9 | spec N9 | Passo 3 não diz "Busca concluida" verde quando tudo ficou indisponível |
| S-MT2 | manut. 2 | docstring de `rotulo_status` (a tela não usa) |

## Vai para depois
- **Frente 4 (explicabilidade, F8/F9):** ux 5 (relatório enxuto, detalhe técnico recolhido), ux 6 (rótulos humanos dos
  motivos), ux 8 (lembrete no Passo 5), ux 10-11 (acentos, cores), ux 7 + spec N7 (emissor/tipo que nós inventamos:
  "Governo Federal" para qualquer `gov.br`, `nome` montado) — são decisão de apresentação.
- **Fase 2 (F1 procedência):** ux 4 (coluna Procedência; título com todas as keywords).
- **P3:** spec N6; ux 9 (snippets colados — investigar); ux 12; manut. 4 e 5 e menores (deriva de retry, helpers);
  testes alto #1 (golden que passe pelos searchers com payload real congelado).
- **🔴 D-C17** segue com o Rodrigo (a revisão de spec reforça: perda silenciosa; o `_merge` troca o `nome` também).
