# servidor_nuati: app Streamlit no servidor do Nuati (pasta copiável)

**Versão 1.0.0** (`$VersaoServidorNuati` no `comum.ps1`) · **Origem:** `github.com/rodilpinto/nuati-framework`
(privado), pasta `servidor_nuati/`. Histórico: [`CHANGELOG.md`](CHANGELOG.md). Receita completa (primeira vez, cada
promoção, voltar atrás): README da raiz do framework, §3, passo 8.

Roda o app num servidor Windows da rede como **tarefa agendada**: sobe junto com o Windows, sem ninguém logado, como a
conta SYSTEM, e tenta reiniciar até 3 vezes se cair. O servidor roda a branch `main` do app (D-C22: o servidor do
Nuati espelha a produção) e **não atualiza sozinho**: a cada promoção, alguém roda o `atualizar.ps1`.

Veio de `checklist-conformidade/servidor/` (validado no servidor do Nuati em 01/10/2026), generalizado para qualquer
app: o que é do app fica num `servidor_nuati.conf` na raiz do repo dele.

| Arquivo | Para quê |
|---|---|
| `instalar_tarefa.ps1` | uma vez por app: cria o `.venv`, instala as dependências, confere a configuração, registra a tarefa, abre a porta no firewall do Windows, sobe o app e espera o health |
| `atualizar.ps1` | a cada promoção (ou mudança de configuração): `git pull --ff-only`, dependências, reinício, health |
| `desinstalar_tarefa.ps1` | para o app, apaga a tarefa e as regras de firewall dela (o clone, o `.venv` e os logs ficam) |
| `iniciar.cmd` | o que a tarefa executa: entra na pasta do app e roda o Streamlit; saída em `logs\app.log` |
| `comum.ps1` | funções dos scripts; lê e valida o `servidor_nuati.conf` |
| `servidor_nuati.conf.example` | modelo do `.conf` do app |

## Adotar num app

1. **Copie a pasta inteira** `servidor_nuati/` para a **raiz do repo** do app (mesmo que o app fique numa subpasta),
   sem editar nada, e registre a cópia no README da raiz do framework ("Registro de cópias").
2. Copie `servidor_nuati.conf.example` para **`servidor_nuati.conf` na raiz do repo** e preencha. Ele vai para o git
   (não tem segredo).

   | Chave | Padrão | O que é |
   |---|---|---|
   | `NOME_TAREFA` | (obrigatória) | nome da tarefa no Agendador; também nomeia a regra de firewall (`<NOME_TAREFA> (TCP <PORTA>)`) |
   | `PORTA` | (obrigatória) | porta do Streamlit; escolha uma livre **no servidor** (receita, passo 8.1) e registre no `segredos.exemplo.toml` do framework |
   | `PASTA_APP` | `.` | onde o app fica, relativa à raiz do repo (buscador: `levantamento-normativos`) |
   | `ARQUIVO_APP` | `app.py` | relativo a `PASTA_APP` |
   | `REQUIREMENTS` | `requirements.txt` | relativo a `PASTA_APP` |
   | `CONFIG` | `.env,.streamlit/secrets.toml` | configuração do app; basta existir uma, **dentro de `PASTA_APP`** |
   | `RAMO` | `main` | branch que o servidor roda; os scripts recusam outra |
   | `LOG_MAX_MB` | `20` | acima disso, ao subir, `logs\app.log` vira `logs\app.log.1` |

3. No `.gitignore` do app: `logs/` e `.venv/` (e a configuração com segredo: `.env`, `.streamlit/secrets.toml`).
4. Rode, da pasta que contém `servidor_nuati/`: `python -m pytest servidor_nuati -q` (Windows; não precisa de
   Administrador).

## Onde o app procura a configuração no servidor

A tarefa roda como **SYSTEM**: o `~/.streamlit/secrets.toml` de um usuário não vale lá. Por isso a configuração fica
**dentro de `PASTA_APP`**, e o `iniciar.cmd` entra nessa pasta antes de subir o Streamlit.

- `.streamlit/secrets.toml`: o Streamlit procura no `.streamlit/` da pasta de onde é rodado e no da pasta do script
  (este vence), além do `~/.streamlit/`. ✅ Conferido no código do Streamlit 1.64: `streamlit/file_util.py:156`
  (`Path.cwd() / ".streamlit"`), `:167` (pasta do script) e `streamlit/config.py:2960` (ordem).
- `.env`: só vale se o app o carrega (ex.: `load_dotenv()`, como o checklist). O buscador não carrega: usa o
  `secrets.toml`.

## Dia a dia (no servidor, PowerShell como Administrador, na raiz do clone)

| Para | Comando |
|---|---|
| ver se está no ar | `Get-ScheduledTask <NOME_TAREFA>` e `http://localhost:<PORTA>/_stcore/health` (responde `ok`) |
| parar / subir | `Stop-ScheduledTask <NOME_TAREFA>` / `Start-ScheduledTask <NOME_TAREFA>` |
| atualizar (código ou configuração) | `powershell -ExecutionPolicy Bypass -File servidor_nuati\atualizar.ps1` |
| trocar a porta | mude `PORTA` no `.conf` (commit, promoção) e rode de novo o `instalar_tarefa.ps1`: a regra de firewall antiga desta tarefa sai |
| tirar do servidor | `powershell -ExecutionPolicy Bypass -File servidor_nuati\desinstalar_tarefa.ps1` |
| log | `logs\app.log` (e o anterior em `logs\app.log.1`) |

## Proteções

- `Parar-App` só encerra, **na porta do app**, processo cuja linha de comando tem `streamlit` e
  `--server.port <PORTA>`; qualquer outro programa na porta faz o script **parar com erro**, sem derrubar nada
  (01/10: o script recusou a 8400, ocupada por outro app).
- `atualizar.ps1` recusa se houver alteração local em arquivo versionado, e não reinicia nada se o `git pull --ff-only`
  falhar (uma `main` reescrita é recusada, de propósito).
- `instalar_tarefa.ps1` e `atualizar.ps1` recusam um clone fora da branch `RAMO`.

## Pegadinhas (✅ medidas no checklist, 01/10)

- **Caminho longo:** `pip install` falha com `WinError 206` (pastas fundas do numpy). Clone em pasta curta
  (ex.: `C:\apps\<app>`).
- **O `python.exe` de um `.venv` é um lançador:** quem escuta na porta pode ser o Python base, como filho. Por isso o
  Streamlit é reconhecido pela linha de comando.
- **PowerShell 5.1 lê `.ps1` sem BOM como ANSI:** os scripts são só ASCII (há teste).
- **A lista de portas liberadas não diz quais estão em uso:** confira antes.
- **Mudança na configuração só vale depois de reiniciar:** `atualizar.ps1`.

## Regra de sincronia

**Não edite uma cópia.** O que é do app fica no `servidor_nuati.conf` dele. Melhoria nasce no framework, sobe
`$VersaoServidorNuati`, entra no `CHANGELOG.md` e é recopiada.
