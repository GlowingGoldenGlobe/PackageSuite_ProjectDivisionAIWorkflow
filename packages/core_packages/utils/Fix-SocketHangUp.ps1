# Fix-SocketHangUp.ps1
# PowerShell script to fix socket hang up errors
# Run as Administrator for full functionality

param(
    [switch]$AutoFix = $false
)

Write-Host "=== Socket Hang Up Error Fixer ===" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "WARNING: Not running as administrator. Some fixes may not work." -ForegroundColor Yellow
    Write-Host "Restart PowerShell as Administrator for full functionality." -ForegroundColor Yellow
    Write-Host ""
}

# Step 1: Restart WSL
Write-Host "Step 1: Restarting WSL..." -ForegroundColor Green
try {
    wsl --shutdown
    Write-Host "WSL shutdown complete" -ForegroundColor Green
} catch {
    Write-Host "Error restarting WSL: $_" -ForegroundColor Red
}

# Step 2: Test connectivity
Write-Host "`nStep 2: Testing network connectivity..." -ForegroundColor Green
$testSites = @(
    "https://github.com",
    "https://api.anthropic.com", 
    "https://www.google.com"
)

foreach ($site in $testSites) {
    try {
        $response = Invoke-WebRequest -Uri $site -Method Head -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ $site - Reachable" -ForegroundColor Green
        } else {
            Write-Host "✗ $site - Status: $($response.StatusCode)" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ $site - Not reachable" -ForegroundColor Red
    }
}

# Step 3: Network reset (admin only)
if ($isAdmin) {
    Write-Host "`nStep 3: Network reset options (admin mode)..." -ForegroundColor Green
    
    if ($AutoFix -or (Read-Host "Reset Windows network stack? Requires restart (y/n)") -eq 'y') {
        Write-Host "Resetting Windows network stack..." -ForegroundColor Yellow
        
        # Reset winsock
        Write-Host "- Resetting Winsock..." -ForegroundColor Yellow
        netsh winsock reset
        
        # Flush DNS
        Write-Host "- Flushing DNS cache..." -ForegroundColor Yellow
        ipconfig /flushdns
        
        # Reset TCP/IP
        Write-Host "- Resetting TCP/IP stack..." -ForegroundColor Yellow
        netsh int ip reset
        
        # Reset network adapter
        Write-Host "- Resetting network adapters..." -ForegroundColor Yellow
        netsh int reset all
        
        Write-Host "`nNetwork reset complete. Please restart your computer." -ForegroundColor Green
        Write-Host "After restart, run this script again to verify connectivity." -ForegroundColor Cyan
    }
} else {
    Write-Host "`nStep 3: Network reset skipped (requires admin)" -ForegroundColor Yellow
}

# Step 4: Check VS Code settings
Write-Host "`nStep 4: Checking VS Code settings..." -ForegroundColor Green
$vsCodeSettingsPath = "$env:APPDATA\Code\User\settings.json"
if (Test-Path $vsCodeSettingsPath) {
    $settings = Get-Content $vsCodeSettingsPath -Raw
    if ($settings -match "http\.proxyStrictSSL") {
        Write-Host "✓ VS Code network settings found" -ForegroundColor Green
    } else {
        Write-Host "✗ VS Code missing network settings" -ForegroundColor Yellow
        Write-Host "Add these to settings.json:" -ForegroundColor Yellow
        Write-Host '"http.proxyStrictSSL": false,' -ForegroundColor Cyan
        Write-Host '"http.systemCertificates": true,' -ForegroundColor Cyan
        Write-Host '"http.proxySupport": "on",' -ForegroundColor Cyan
        Write-Host '"http.experimental.enableHttp2": true' -ForegroundColor Cyan
    }
}

# Step 5: Check WSL config
Write-Host "`nStep 5: Checking WSL configuration..." -ForegroundColor Green
$wslConfigPath = "$env:USERPROFILE\.wslconfig"
if (Test-Path $wslConfigPath) {
    $wslConfig = Get-Content $wslConfigPath -Raw
    if ($wslConfig -match "networkingMode=mirrored") {
        Write-Host "✓ WSL network optimization found" -ForegroundColor Green
    } else {
        Write-Host "✗ WSL missing network optimization" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ WSL config not found" -ForegroundColor Yellow
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "1. WSL has been restarted" -ForegroundColor White
Write-Host "2. Network connectivity tested" -ForegroundColor White
if ($isAdmin) {
    Write-Host "3. Network stack ready to reset (if chosen)" -ForegroundColor White
} else {
    Write-Host "3. Run as Administrator to reset network" -ForegroundColor Yellow
}
Write-Host "4. VS Code settings checked" -ForegroundColor White
Write-Host "5. WSL configuration checked" -ForegroundColor White

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "- Restart VS Code" -ForegroundColor White
Write-Host "- If issues persist, restart computer" -ForegroundColor White
Write-Host "- Note: Solar activity may affect network stability" -ForegroundColor Yellow

if (-not $isAdmin) {
    Write-Host "`nTip: Run this script as Administrator for full functionality:" -ForegroundColor Cyan
    Write-Host "Start-Process PowerShell -Verb RunAs -ArgumentList '-File', '$PSCommandPath'" -ForegroundColor Green
}