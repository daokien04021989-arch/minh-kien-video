@echo off
rem Cai 1 lan tren may 2: tu lay file cat moi 5 phut/lan vao C:\DonCat
set REPO=https://raw.githubusercontent.com/daokien04021989-arch/minh-kien-video/don-cat
if not exist "C:\DonCat" mkdir "C:\DonCat"
curl -fsSL "%REPO%/lay-don.bat" -o "C:\DonCat\lay-don.bat"
if errorlevel 1 (
  echo Khong tai duoc. Kiem tra mang Internet roi chay lai.
  pause
  exit /b 1
)
schtasks /create /f /sc minute /mo 5 /tn "MinhKien_LayFileCat" /tr "C:\DonCat\lay-don.bat"
call "C:\DonCat\lay-don.bat"
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\File cat (DonCat).lnk');$s.TargetPath='C:\DonCat';$s.Save()"
start "" "C:\DonCat"
echo.
echo XONG. File cat moi se tu ve thu muc C:\DonCat (co loi tat ngoai Desktop).
pause
