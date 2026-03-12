@echo off
setlocal EnableDelayedExpansion

:: ============================================
:: deploy.bat - Deploy Telegram-Korean-mini-App
:: GitHub Actions auto-deploys after push
:: ============================================

echo.
echo === Korean Mini App Deploy ===
echo.

:: Check git repo
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Not a git repository!
    echo Run: git init
    echo Run: git remote add origin https://github.com/YOUR_USERNAME/Telegram-Korean-mini-App.git
    pause
    exit /b 1
)

:: Check remote
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Remote "origin" not set!
    pause
    exit /b 1
)

:: Get current branch
for /f "tokens=*" %%a in ('git branch --show-current') do set BRANCH=%%a
if "!BRANCH!"=="" set BRANCH=main

:: Show status
echo [1/4] Changes:
git status --short
echo.

:: Commit message
set /p COMMIT_MSG="Commit message (Enter = update): "
if "!COMMIT_MSG!"=="" set COMMIT_MSG=update

:: Add
echo.
echo [2/4] Adding files...
git add -A

:: Commit
echo [3/4] Committing...
git commit -m "!COMMIT_MSG!"

:: Push
echo [4/4] Pushing to GitHub (branch: !BRANCH!)...
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
