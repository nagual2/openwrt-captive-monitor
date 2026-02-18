$Name = "Ubuntu"
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Write-Error "Admin rights required"; exit 1 }
function Enable-FeatureIfAvailable($n) {
  $f = Get-WindowsOptionalFeature -Online -FeatureName $n -ErrorAction SilentlyContinue
  if ($f -and $f.State -ne 'Enabled') { Enable-WindowsOptionalFeature -Online -FeatureName $n -All -NoRestart | Out-Null }
}
Enable-FeatureIfAvailable "Microsoft-Windows-Subsystem-Linux"
Enable-FeatureIfAvailable "VirtualMachinePlatform"
cmd /c "bcdedit /set hypervisorlaunchtype auto" | Out-Null
try { wsl --shutdown | Out-Null } catch {}
try { wsl --terminate $Name | Out-Null } catch {}
try { wsl --set-default-version 2 | Out-Null } catch {}
$names = @(wsl -l -q)
if ($names -notcontains $Name) { Write-Error "Distro not found: $Name"; exit 1 }
wsl --set-version $Name 2
Write-Host "Conversion to WSL2 requested for 'Ubuntu'. Reboot may be required."
