@echo off
setlocal enabledelayedexpansion

:: Check if .env file exists
if not exist ".env" (
    echo .env file not found.
    exit /b 1
)

:: Loop through .env file and set variables
for /f "usebackq delims== tokens=1,*" %%A in (".env") do (
    set "key=%%A"
    set "val=%%B"
    
    :: Clean up whitespace/carriage returns and ignore comments or empty keys
    if not "!key!"=="" (
        echo !key! | findstr /R "^#" >nul
        if errorlevel 1 (
            set "!key!=!val!"
        )
    )
)

echo Starting RQ worker with the following Redis URL: %REDIS_URL%
rq worker --worker-class rq.worker.SimpleWorker --url %REDIS_URL% index_queue

endlocal