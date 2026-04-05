@echo off
title Germany Telugu Movies - Management Tool
color 0E

:MENU
cls
echo ============================================================
echo       GERMANY TELUGU MOVIES - Management Tool
echo       germany-telugu-movies.com
echo ============================================================
echo.
echo   [1]  Start Local Server (Preview Website)
echo   [2]  Fetch Seat Data (Update Shows)
echo   [3]  Send Notification Emails
echo   [4]  Send Welcome Email
echo   [5]  Send Welcome to All Users
echo   [6]  Open Website (Live)
echo   [7]  Open GitHub Repository
echo   [8]  Open Firebase Console
echo   [9]  Git: Pull Latest Changes
echo  [10]  Git: Push Changes
echo  [11]  Git: Status
echo  [12]  Git: Quick Commit All Changes
echo  [13]  Open in VS Code
echo  [14]  Validate HTML (Check for Errors)
echo  [15]  Clear Browser Cache Reminder
echo   [0]  Exit
echo.
echo ============================================================
set /p choice="  Select an option: "

if "%choice%"=="1" goto SERVER
if "%choice%"=="2" goto FETCH
if "%choice%"=="3" goto NOTIFY
if "%choice%"=="4" goto WELCOME
if "%choice%"=="5" goto WELCOMEALL
if "%choice%"=="6" goto OPENLIVE
if "%choice%"=="7" goto GITHUB
if "%choice%"=="8" goto FIREBASE
if "%choice%"=="9" goto PULL
if "%choice%"=="10" goto PUSH
if "%choice%"=="11" goto STATUS
if "%choice%"=="12" goto COMMIT
if "%choice%"=="13" goto VSCODE
if "%choice%"=="14" goto VALIDATE
if "%choice%"=="15" goto CACHE
if "%choice%"=="0" goto EXIT

echo.
echo  Invalid option. Try again.
timeout /t 2 >nul
goto MENU

:SERVER
cls
echo ============================================================
echo   Starting Local Server on http://localhost:8000
echo   Press Ctrl+C to stop the server
echo ============================================================
echo.
start "" http://localhost:8000
python -m http.server 8000
goto MENU

:FETCH
cls
echo ============================================================
echo   Fetching Seat Data...
echo ============================================================
echo.
python scripts/fetch_seats.py
echo.
echo  Done! Seat data updated.
pause
goto MENU

:NOTIFY
cls
echo ============================================================
echo   Send Ticket Notification
echo ============================================================
echo.
echo  Available movie keys:
echo    ustaad, peddi, paradise, spirit, varanasi
echo    vishwambhara, fauzi
echo.
set /p moviekey="  Enter movie key: "
set /p movieurl="  Enter movie URL (e.g. https://germany-telugu-movies.com/peddi-movie.html): "
echo.
echo  Sending notifications for %moviekey%...
python scripts/send_notify.py %moviekey% %movieurl%
echo.
pause
goto MENU

:WELCOME
cls
echo ============================================================
echo   Send Welcome Email to a User
echo ============================================================
echo.
set /p wemail="  Enter user email: "
set /p wname="  Enter user name: "
echo.
echo  Sending welcome email to %wname% (%wemail%)...
python scripts/send_notify.py welcome %wemail% %wname%
echo.
pause
goto MENU

:WELCOMEALL
cls
echo ============================================================
echo   Send Welcome Email to ALL Users
echo ============================================================
echo.
echo  This will send welcome emails to all registered users.
set /p confirm="  Are you sure? (y/n): "
if /i "%confirm%"=="y" (
    python scripts/send_notify.py welcome-all
)
echo.
pause
goto MENU

:OPENLIVE
start "" https://germany-telugu-movies.com
goto MENU

:GITHUB
start "" https://github.com
echo.
echo  (Opening GitHub - navigate to your repository)
timeout /t 2 >nul
goto MENU

:FIREBASE
start "" https://console.firebase.google.com
timeout /t 2 >nul
goto MENU

:PULL
cls
echo ============================================================
echo   Pulling Latest Changes...
echo ============================================================
echo.
git pull
echo.
pause
goto MENU

:PUSH
cls
echo ============================================================
echo   Pushing to Remote...
echo ============================================================
echo.
git push
echo.
pause
goto MENU

:STATUS
cls
echo ============================================================
echo   Git Status
echo ============================================================
echo.
git status
echo.
git log --oneline -5
echo.
pause
goto MENU

:COMMIT
cls
echo ============================================================
echo   Quick Commit All Changes
echo ============================================================
echo.
git status
echo.
set /p msg="  Enter commit message: "
git add -A
git commit -m "%msg%"
echo.
echo  Changes committed!
echo.
set /p dopush="  Push to remote? (y/n): "
if /i "%dopush%"=="y" git push
echo.
pause
goto MENU

:VSCODE
start "" code .
goto MENU

:VALIDATE
cls
echo ============================================================
echo   Checking HTML Files...
echo ============================================================
echo.
echo  HTML files in project:
echo  ----------------------
for %%f in (*.html) do (
    echo   %%f
)
echo.
echo  Checking for common issues...
echo.
findstr /i /m "TODO FIXME HACK" *.html *.js *.css 2>nul
if %errorlevel%==0 (
    echo  ^ Found TODO/FIXME markers in the above files.
) else (
    echo  No TODO/FIXME markers found.
)
echo.
echo  Checking for broken image references...
findstr /i /n "src=\"images/" *.html 2>nul | findstr /v /i ".png .jpg .jpeg .gif .svg .webp" >nul 2>nul
echo  Basic validation complete.
echo.
pause
goto MENU

:CACHE
cls
echo ============================================================
echo   Clear Browser Cache
echo ============================================================
echo.
echo  To see your latest changes on the live site:
echo.
echo   1. Hard refresh: Ctrl + Shift + R
echo   2. Or open DevTools (F12) ^> Network ^> Disable cache
echo   3. GitHub Pages can take 1-10 minutes to update
echo.
echo  Tip: Use incognito/private window to bypass cache.
echo.
pause
goto MENU

:EXIT
echo.
echo  Goodbye!
timeout /t 1 >nul
exit
