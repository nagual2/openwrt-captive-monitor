# Setup OpenWrt in Hyper-V
# Run as Administrator

$VMName = "OpenWrt-Dev"
$VMPath = "C:\VMs"
$VHDPath = Join-Path $VMPath "openwrt-dev.vhdx"
$SwitchName = "OpenWrt-Internal"

# 1. Check Hyper-V status
$feature = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V
if ($feature.State -ne "Enabled") {
    Write-Host "[!] Hyper-V is NOT enabled. Enabling now..." -ForegroundColor Yellow
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All -NoRestart
    Write-Host "[!] Hyper-V enabled. REBOOT REQUIRED!" -ForegroundColor Red
    return
}

# 2. Create Switch
if (!(Get-VMSwitch -Name $SwitchName -ErrorAction SilentlyContinue)) {
    Write-Host "[+] Creating Virtual Switch: $SwitchName..." -ForegroundColor Green
    New-VMSwitch -Name $SwitchName -SwitchType Internal
}

# 3. Create VM
if (!(Get-VM -Name $VMName -ErrorAction SilentlyContinue)) {
    Write-Host "[+] Creating VM: $VMName..." -ForegroundColor Green
    New-VM -Name $VMName -MemoryStartupBytes 512MB -Generation 2 -Path $VMPath -SwitchName $SwitchName
    
    # Disable Secure Boot
    Set-VMFirmware -VMName $VMName -EnableSecureBoot Off
    
    # Set Boot Order
    Set-VMBootOrder -VMName $VMName -BootOrder "HardDiskDrive"
    
    # Add Disk
    Add-VMHardDiskDrive -VMName $VMName -Path $VHDPath
    
    Write-Host "[+] VM $VMName created successfully." -ForegroundColor Green
} else {
    Write-Host "[!] VM $VMName already exists." -ForegroundColor Yellow
}

Write-Host "`nDone! Start VM with: Start-VM -Name $VMName" -ForegroundColor Cyan
