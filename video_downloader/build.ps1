$ErrorActionPreference = "Stop"
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
Set-Location $PSScriptRoot
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements.txt
& $py -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name "UniversalVideoDownloader" `
  --collect-all yt_dlp `
  --collect-all imageio_ffmpeg `
  --hidden-import yt_dlp `
  --hidden-import imageio_ffmpeg `
  app.py
Write-Host "EXE: $PSScriptRoot\dist\UniversalVideoDownloader.exe"
