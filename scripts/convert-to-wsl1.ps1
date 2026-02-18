$Name = "Ubuntu"
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Write-Error "Admin rights required"; exit 1 }
try { wsl --shutdown | Out-Null } catch {}
$null = (try { wsl --terminate $Name | Out-Null } catch {})
$names = @(wsl -l -q)
if ($names -notcontains $Name) { Write-Error "Distro not found: $Name"; exit 1 }
wsl --set-version $Name 1
Write-Host "Conversion to WSL1 requested for 'Ubuntu'."
