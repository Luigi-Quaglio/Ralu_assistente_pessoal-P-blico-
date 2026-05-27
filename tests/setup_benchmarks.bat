@echo off
REM Script de preparação para executar benchmarks do TCC
REM Execute este script ANTES de rodar os benchmarks

echo =====================================================
echo  PREPARACAO DOS BENCHMARKS - RALU TCC
echo =====================================================
echo.

REM Verifica se está no diretório correto
if not exist "src\ralu.py" (
    echo ERRO: Execute este script do diretorio Ralu/
    echo Exemplo: cd Ralu ^&^& tests\setup_benchmarks.bat
    pause
    exit /b 1
)

echo [1/4] Instalando dependencias...
python -m pip install -r requirements.txt
python -m pip install psutil

echo.
echo [2/4] Verificando instalacao do Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo AVISO: Ollama nao encontrado. Instale em https://ollama.ai
) else (
    echo OK: Ollama instalado
)

echo.
echo [3/4] Verificando modelo do Ollama...
ollama list | findstr "llama" >nul
if errorlevel 1 (
    echo AVISO: Nenhum modelo encontrado
    echo Execute: ollama pull llama3.2
) else (
    echo OK: Modelo encontrado
)

echo.
echo [4/4] Criando diretorio de saida...
if not exist "data\benchmarks" mkdir data\benchmarks
echo OK: data\benchmarks criado

echo.
echo =====================================================
echo  PREPARACAO CONCLUIDA
echo =====================================================
echo.
echo Agora voce pode executar os benchmarks:
echo   python tests\run_all_benchmarks.py
echo.
echo Ou individualmente:
echo   python tests\benchmark_latency.py
echo   python tests\benchmark_classifier.py
echo   python tests\benchmark_memory.py
echo.

pause
