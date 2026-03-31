@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "SYT_PY=%SCRIPT_DIR%syt.py"
set "SCRIPT_DIR_CLEAN=%SCRIPT_DIR:~0,-1%"

if not exist "%SYT_PY%" (
    echo Error: syt.py not found in %SCRIPT_DIR%
    exit /b 1
)

echo.
echo.  installing syt...
echo.

set "WRAPPER=%SCRIPT_DIR%syt.bat"
(
    echo @echo off
    echo where py ^>nul 2^>^&1
    echo if %%errorlevel%%==0 ^(
    echo   py -3 "%SYT_PY%" %%*
    echo ^) else ^(
    echo   python "%SYT_PY%" %%*
    echo ^)
) > "%WRAPPER%"

set "PS_WRAPPER=%SCRIPT_DIR%syt.ps1"
(
    echo if (Get-Command py -ErrorAction SilentlyContinue^) { py -3 "%SYT_PY%" @args } else { python "%SYT_PY%" @args }
) > "%PS_WRAPPER%"

echo %PATH% | findstr /i /c:"%SCRIPT_DIR_CLEAN%" >nul 2>&1
if errorlevel 1 (
    echo   Adding %SCRIPT_DIR_CLEAN% to user PATH...
    set "PS_CMD=$user=[Environment]::GetEnvironmentVariable('Path','User');$dir='%SCRIPT_DIR_CLEAN%';if([string]::IsNullOrWhiteSpace($user)){$new=$dir}else{$parts=$user -split ';';if($parts -contains $dir){$new=$user}else{$new=$user+';'+$dir}};[Environment]::SetEnvironmentVariable('Path',$new,'User')"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "%PS_CMD%" >nul 2>&1
    if errorlevel 1 (
        echo   Could not update PATH automatically.
        echo   Manually add this to your PATH: %SCRIPT_DIR_CLEAN%
    ) else (
        echo   PATH updated. Restart your terminal.
    )
)

where yt-dlp >nul 2>&1
if errorlevel 1 (
    echo   WARNING: yt-dlp not found. install it:  pip install yt-dlp
)
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo   WARNING: ffmpeg not found. install it:  download it from https://ffmpeg.org/download.html
)

echo.
echo   done! syt installed to %WRAPPER% :3
echo   usage:  syt [link]   or just   syt
echo.
pause