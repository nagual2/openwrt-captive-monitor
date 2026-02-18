param()
$Distro = "Ubuntu"
$Base = "C:\WSL"
$Backup = Join-Path $Base "Ubuntu-backup.tar"
$BackupGz = "$Backup.gz"
$Install = Join-Path $Base "Ubuntu"
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Write-Error "Admin rights required"; exit 1 }
New-Item -ItemType Directory -Path $Base -Force | Out-Null
function SizeMB($p){ if (Test-Path $p) { [Math]::Round((Get-Item $p).Length/1MB,2) } else { 0 } }
function DirSizeMB($p){ if (Test-Path $p) { [Math]::Round((Get-ChildItem -LiteralPath $p -Recurse -Force -File | Measure-Object Length -Sum).Sum/1MB,2) } else { 0 } }
try { wsl --terminate $Distro | Out-Null } catch {}
$sw = [System.Diagnostics.Stopwatch]::StartNew()
Write-Progress -Activity "Export" -Status "Starting" -PercentComplete 0
$p = Start-Process -FilePath "wsl.exe" -ArgumentList @("--export",$Distro,$Backup) -PassThru -NoNewWindow
$last = 0
while (-not $p.HasExited) {
  $sz = SizeMB $Backup
  $delta = $sz - $last
  $speed = if ($delta -gt 0) { [Math]::Round($delta,2) } else { 0 }
  Write-Progress -Activity "Export" -Status ("{0} MB, {1} MB/s, {2}" -f $sz,$speed,$sw.Elapsed.ToString()) -PercentComplete 50
  $last = $sz
  Start-Sleep -Milliseconds 800
}
Write-Progress -Activity "Export" -Completed
function Ensure7Zip() {
  $has7z = Get-Command 7z -ErrorAction SilentlyContinue
  if ($has7z) { return $true }
  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if ($winget) { winget install --id 7zip.7zip -e --accept-source-agreements --accept-package-agreements | Out-Null }
  $has7z = Get-Command 7z -ErrorAction SilentlyContinue
  if ($has7z) { return $true }
  return $false
}
$Archive = $Backup
if (Test-Path $Backup) {
  if (Ensure7Zip) {
    $sw2 = [System.Diagnostics.Stopwatch]::StartNew()
    Write-Progress -Activity "Compress" -Status "Starting" -PercentComplete 0
    $p2 = Start-Process -FilePath "7z.exe" -ArgumentList @("a","-tgzip","-mx=5","-mmt=on",$BackupGz,$Backup) -PassThru -NoNewWindow
    $last2 = 0
    $inSize = SizeMB $Backup
    while (-not $p2.HasExited) {
      $outSz = SizeMB $BackupGz
      $delta2 = $outSz - $last2
      $spd2 = if ($delta2 -gt 0) { [Math]::Round($delta2,2) } else { 0 }
      $pct = if ($inSize -gt 0) { [Math]::Min(99,[int](($outSz/$inSize)*100)) } else { 50 }
      Write-Progress -Activity "Compress" -Status ("{0} MB → {1} MB, {2} MB/s, {3}" -f $inSize,$outSz,$spd2,$sw2.Elapsed.ToString()) -PercentComplete $pct
      $last2 = $outSz
      Start-Sleep -Milliseconds 800
    }
    Write-Progress -Activity "Compress" -Completed
    if (Test-Path $BackupGz) { Remove-Item $Backup -Force; $Archive = $BackupGz }
  }
}
wsl --unregister $Distro
New-Item -ItemType Directory -Path $Install -Force | Out-Null
$sw3 = [System.Diagnostics.Stopwatch]::StartNew()
Write-Progress -Activity "Import" -Status "Starting" -PercentComplete 0
$p3 = Start-Process -FilePath "wsl.exe" -ArgumentList @("--import",$Distro,$Install,$Archive,"--version","2") -PassThru -NoNewWindow
$last3 = 0
while (-not $p3.HasExited) {
  $is = DirSizeMB $Install
  $d3 = $is - $last3
  $sp3 = if ($d3 -gt 0) { [Math]::Round($d3,2) } else { 0 }
  Write-Progress -Activity "Import" -Status ("{0} MB, {1} MB/s, {2}" -f $is,$sp3,$sw3.Elapsed.ToString()) -PercentComplete 50
  $last3 = $is
  Start-Sleep -Milliseconds 800
}
Write-Progress -Activity "Import" -Completed
Write-Host ("Done. Imported '{0}' to WSL2 from {1}." -f $Distro,$Archive)
