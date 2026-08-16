param(
    [string]$TaskName = "DescompliADS Meta Sync",
    [string]$DailyAt = "03:00"
)

$BackendPath = Split-Path -Parent $PSScriptRoot
$PythonPath = Join-Path $BackendPath ".venv\Scripts\python.exe"
$SyncScript = Join-Path $PSScriptRoot "sync_meta_all.py"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Ambiente virtual não encontrado em $PythonPath"
}
if (-not (Test-Path -LiteralPath $SyncScript)) {
    throw "Script de sincronização não encontrado em $SyncScript"
}

try {
    $TriggerTime = [datetime]::ParseExact($DailyAt, "HH:mm", $null)
}
catch {
    throw "DailyAt deve usar o formato HH:mm, por exemplo 03:00."
}

$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument 'scripts\sync_meta_all.py' `
    -WorkingDirectory $BackendPath
$Trigger = New-ScheduledTaskTrigger -Daily -At $TriggerTime
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Sincroniza diariamente contas e métricas da Meta no DescompliADS." `
    -Force | Out-Null

Write-Output "Tarefa '$TaskName' configurada diariamente às $DailyAt."
Write-Output "Teste agora com: Start-ScheduledTask -TaskName '$TaskName'"
