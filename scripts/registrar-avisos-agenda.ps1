# Registra (o actualiza) la tarea programada que lanza los avisos de la agenda cada 5 minutos.
#   ./scripts/registrar-avisos-agenda.ps1
# Quitarla:  Unregister-ScheduledTask -TaskName UNED-AvisosAgenda -Confirm:$false
# Usa pythonw (sin ventana) con tu usuario; funciona aunque el servidor web no esté arrancado.
# Si el PC estaba apagado, al volver a estar disponible se ejecuta y avisa solo de lo que aún sea útil.
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$pythonw = Join-Path $repo '.venv\Scripts\pythonw.exe'
$script = Join-Path $PSScriptRoot 'avisos_agenda.py'
if (-not (Test-Path $pythonw)) { throw "No existe $pythonw (arranca antes ./scripts/run.ps1 para crear el entorno)." }

$accion = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$script`"" -WorkingDirectory $repo
$disparador = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 2)

Register-ScheduledTask -TaskName 'UNED-AvisosAgenda' -Action $accion -Trigger $disparador -Settings $ajustes `
    -Description 'Notificaciones de Windows para eventos y tareas de la agenda UNED' -Force | Out-Null

Get-ScheduledTask -TaskName 'UNED-AvisosAgenda' | Select-Object TaskName, State | Format-Table -AutoSize
(Get-ScheduledTaskInfo -TaskName 'UNED-AvisosAgenda').NextRunTime
