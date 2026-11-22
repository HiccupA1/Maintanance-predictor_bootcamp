<#
.SYNOPSIS
  Stop the local demo started by tools/demo/start.ps1 (only its processes).
#>
$patterns = 'tools\.demo\.auth_stub', 'uvicorn app\.main:app', 'vite\.js preview'
Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='node.exe'" |
  Where-Object { $cmd = $_.CommandLine; $patterns | Where-Object { $cmd -match $_ } } |
  ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    Write-Host "stopped $($_.ProcessId): $($_.Name)"
  }
