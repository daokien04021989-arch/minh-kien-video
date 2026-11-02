@echo off
rem Tu dong lay goi file cat moi tu kho don-cat ve C:\DonCat (Co Khi Minh Kien)
set REPO=https://raw.githubusercontent.com/daokien04021989-arch/minh-kien-video/don-cat
set DIR=C:\DonCat
if not exist "%DIR%" mkdir "%DIR%"
cd /d "%DIR%"
curl -fsSL "%REPO%/danh-sach.txt?t=%RANDOM%%RANDOM%" -o danh-sach.txt
if errorlevel 1 exit /b 1
for /f "usebackq delims=" %%f in ("danh-sach.txt") do (
  if not exist "%%~nf\" (
    curl -fsSL "%REPO%/%%f" -o "%%f"
    if not errorlevel 1 (
      mkdir "%%~nf"
      tar -xf "%%f" -C "%%~nf"
      del "%%f"
    )
  )
)
exit /b 0
