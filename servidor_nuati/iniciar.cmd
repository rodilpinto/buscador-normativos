@echo off
rem servidor_nuati: o que a tarefa agendada executa (instalar_tarefa.ps1 passa os argumentos, lidos do
rem servidor_nuati.conf). ORIGEM: nuati-framework, pasta servidor_nuati/. Nao edite uma copia.
rem   iniciar.cmd PORTA PASTA_DO_APP ARQUIVO_APP [LOG_MAX_BYTES]
rem Saida do app em <raiz>\logs\app.log; acima de LOG_MAX_BYTES, o log anterior vira app.log.1 ao subir.
setlocal
for %%I in ("%~dp0..") do set "RAIZ=%%~fI"
set "PORTA=%~1"
set "PASTA=%~2"
set "ARQUIVO=%~3"
set "LOGMAX=%~4"
if "%ARQUIVO%"=="" (
  echo uso: iniciar.cmd PORTA PASTA_DO_APP ARQUIVO_APP [LOG_MAX_BYTES]
  exit /b 2
)
if "%LOGMAX%"=="" set "LOGMAX=20971520"
if not exist "%RAIZ%\logs" mkdir "%RAIZ%\logs"
set "LOG=%RAIZ%\logs\app.log"
if exist "%LOG%" for %%F in ("%LOG%") do if %%~zF GTR %LOGMAX% move /y "%LOG%" "%LOG%.1" >nul
set "PYTHONIOENCODING=utf-8"
cd /d "%PASTA%" || (
  echo [%date% %time%] pasta do app nao encontrada: %PASTA% >> "%LOG%"
  exit /b 1
)
echo [%date% %time%] iniciando %ARQUIVO% na porta %PORTA% em %CD% >> "%LOG%"
"%RAIZ%\.venv\Scripts\python.exe" -m streamlit run "%ARQUIVO%" --server.port %PORTA% --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false >> "%LOG%" 2>&1
