@echo off
setlocal EnableDelayedExpansion

:: ============================================
:: deploy.bat - Deploy Telegram-Korean-mini-App
:: ============================================

echo.
echo === Korean Mini App Deploy ===
echo.

:: Check git repo
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Not a git repository!
    pause
    exit /b 1
)

:: Get current branch
for /f "tokens=*" %%a in ('git branch --show-current') do set BRANCH=%%a
if "!BRANCH!"=="" set BRANCH=main

:: Pull remote changes first (--no-edit skips Vim editor)
echo [1/5] Pulling remote changes...
git pull --no-edit origin !BRANCH!
echo.

:: Show status
echo [2/5] Changes:
git status --short
echo.

:: Commit message
set /p COMMIT_MSG="Commit message (Enter = update): "
if "!COMMIT_MSG!"=="" set COMMIT_MSG=update

:: Add
echo.
echo [3/5] Adding files...
git add -A

:: Commit
echo [4/5] Committing...
git commit -m "!COMMIT_MSG!"

:: Push
echo [5/5] Pushing to GitHub (branch: !BRANCH!)...
git push -u origin !BRANCH!
if errorlevel 1 (
    echo.
    echo [ERROR] Push failed.
    pause
    exit /b 1
)

echo.
echo === DONE! GitHub Actions will auto-deploy ===
echo.
pause
