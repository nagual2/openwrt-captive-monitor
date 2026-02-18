param()
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Write-Error "Нужны права администратора"; exit 1 }
try { wsl --shutdown | Out-Null } catch {}
function Disable-FeatureIfPresent($name) {
  $feature = Get-WindowsOptionalFeature -Online -FeatureName $name -ErrorAction SilentlyContinue
  if ($feature) {
    if ($feature.State -ne 'Disabled') { Disable-WindowsOptionalFeature -Online -FeatureName $name -NoRestart | Out-Null }
    Write-Host "${name}: Disabled"
  } else {
    Write-Host "${name}: Not found"
  }
}
Disable-FeatureIfPresent "Windows-Hypervisor-Platform"
Disable-FeatureIfPresent "VirtualMachinePlatform"
Disable-FeatureIfPresent "Microsoft-Hyper-V-All"
cmd /c "bcdedit /set hypervisorlaunchtype off" | Out-Null
Write-Host "Done. Reboot required to apply changes."
