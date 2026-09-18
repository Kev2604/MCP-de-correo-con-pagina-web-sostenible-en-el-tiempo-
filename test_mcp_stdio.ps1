$payload = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"ps-test","version":"1.0"}}}'

$bytes = [System.Text.Encoding]::UTF8.GetBytes($payload + "`n")
$process = Start-Process -FilePath "docker" -ArgumentList @("run","--rm","-i","--env-file","C:/Users/KFsil/OneDrive/Desktop/mcp-correo/.env","mcp-correo:latest") -NoNewWindow -PassThru -RedirectStandardInput "$PSScriptRoot/test_mcp_in.txt" -RedirectStandardOutput "$PSScriptRoot/test_mcp_out.txt" -RedirectStandardError "$PSScriptRoot/test_mcp_err.txt"

[System.IO.File]::WriteAllBytes((Join-Path $PSScriptRoot 'test_mcp_in.txt'), $bytes)
$process.WaitForExit()

Write-Host "--- STDOUT ---"
Get-Content (Join-Path $PSScriptRoot 'test_mcp_out.txt') -Raw
Write-Host "--- STDERR ---"
Get-Content (Join-Path $PSScriptRoot 'test_mcp_err.txt') -Raw
Write-Host "--- EXIT CODE ---"
$process.ExitCode
