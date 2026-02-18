param()
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Write-Error "Нужны права администратора"; exit 1 }
function Enable-FeatureIfAvailable($name) {
  $feature = Get-WindowsOptionalFeature -Online -FeatureName $name -ErrorAction SilentlyContinue
  if ($feature) {
    if ($feature.State -ne 'Enabled') { Enable-WindowsOptionalFeature -Online -FeatureName $name -All -NoRestart | Out-Null }
    Write-Host "${name}: Enabled"
  } else {
    Write-Host "${name}: Not found"
  }
}
Enable-FeatureIfAvailable "Microsoft-Windows-Subsystem-Linux"
Enable-FeatureIfAvailable "VirtualMachinePlatform"
Enable-FeatureIfAvailable "Windows-Hypervisor-Platform"
try { wsl --update | Out-Null } catch {}
try { wsl --set-default-version 2 | Out-Null } catch {}
cmd /c "bcdedit /set hypervisorlaunchtype auto" | Out-Null
Write-Host "Done. Reboot required to apply changes."
