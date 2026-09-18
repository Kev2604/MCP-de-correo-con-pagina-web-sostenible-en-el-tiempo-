$init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"ps-test","version":"1.0"}}}'

$toolsList = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

$call = '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"enviar_correo","arguments":{"destinatario":"test@example.com","asunto":"Prueba MCP","cuerpo":"Hola desde MCP","html":"<p>Hola desde MCP</p>"}}}'

$messages = @($init, $toolsList, $call)

$stdinPath = Join-Path $PSScriptRoot 'test_mcp_tool_in.txt'
$stdoutPath = Join-Path $PSScriptRoot 'test_mcp_tool_out.txt'
$stderrPath = Join-Path $PSScriptRoot 'test_mcp_tool_err.txt'

@($messages -join "`n") | Set-Content -Encoding UTF8 $stdinPath

$process = Start-Process -FilePath "docker" -ArgumentList @("run","--rm","-i","--env-file","C:/Users/KFsil/OneDrive/Desktop/mcp-correo/.env","mcp-correo:latest") -NoNewWindow -PassThru -RedirectStandardInput $stdinPath -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
$process.WaitForExit()

Write-Host "--- STDOUT ---"
Get-Content $stdoutPath -Raw
Write-Host "--- STDERR ---"
Get-Content $stderrPath -Raw
Write-Host "--- EXIT CODE ---"
$process.ExitCode
