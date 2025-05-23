# Test-GUIFunctionality.ps1
# This script helps test the GUI functionality to ensure all features work as expected

# Define constants
$projectRoot = Split-Path -Parent $PSCommandPath
$logFile = Join-Path $projectRoot "gui_test_results.log"
$guiLauncherPath = Join-Path $projectRoot "gui\gui_launcher.py"

function Write-Log {
    param (
        [string]$message,
        [string]$type = "INFO"  # INFO, WARNING, ERROR, SUCCESS
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$type] $message"
    
    # Output to console with color
    switch ($type) {
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        default { Write-Host $logMessage }
    }
    
    # Also write to log file
    Add-Content -Path $logFile -Value $logMessage
}

function Test-PythonInstallation {
    try {
        $pythonVersion = & python --version 2>&1
        Write-Log "Python version: $pythonVersion" "INFO"
        return $true
    }
    catch {
        Write-Log "Python not found or not in PATH" "ERROR"
        return $false
    }
}

function Test-RequiredPackages {
    $packages = @("tkinter", "psutil", "pillow")
    $results = @()
    
    foreach ($package in $packages) {
        $cmd = "python -c `"import $package; print('$package is installed')`" 2>&1"
        $output = Invoke-Expression $cmd
        
        if ($output -like "*$package is installed*") {
            Write-Log "Package $package is installed" "SUCCESS"
            $results += @{
                "Package" = $package
                "Status" = "Installed"
            }
        }
        else {
            Write-Log "Package $package is missing or has issues" "WARNING"
            $results += @{
                "Package" = $package
                "Status" = "Missing"
            }
        }
    }
    
    return $results
}

function Test-GUILauncher {
    if (-not (Test-Path $guiLauncherPath)) {
        Write-Log "GUI launcher not found at: $guiLauncherPath" "ERROR"
        return $false
    }
    
    Write-Log "GUI launcher found at: $guiLauncherPath" "SUCCESS"
    return $true
}

function Launch-GUI {
    Write-Log "Launching GUI..." "INFO"
    Write-Log "Note: The GUI will be launched in a separate window. Please interact with it to test functionality." "INFO"
    Write-Log "When done testing, close the GUI and return to this window." "INFO"
    
    # Start the GUI
    Start-Process -FilePath "python" -ArgumentList $guiLauncherPath -Wait
    
    # After GUI is closed
    Write-Log "GUI testing completed. Please provide your feedback below:" "INFO"
    
    $features = @(
        "Version Selection",
        "Development Mode Selection",
        "Time Limit Options",
        "Status Display",
        "Model Version Management",
        "Agent Mode/PyAutoGen Selection"
    )
    
    $results = @{}
    
    foreach ($feature in $features) {
        Write-Host "`nDid the '$feature' feature work correctly? (Y/N/Skip): " -ForegroundColor Cyan -NoNewline
        $response = Read-Host
        
        if ($response -eq "Y" -or $response -eq "y") {
            $results[$feature] = "Working"
            Write-Log "Feature '$feature' reported as working" "SUCCESS"
        }
        elseif ($response -eq "N" -or $response -eq "n") {
            Write-Host "Please provide details about the issue: " -ForegroundColor Yellow -NoNewline
            $issue = Read-Host
            $results[$feature] = "Issue: $issue"
            Write-Log "Feature '$feature' has issue: $issue" "WARNING"
        }
        else {
            $results[$feature] = "Not Tested"
            Write-Log "Feature '$feature' was not tested" "INFO"
        }
    }
    
    # Additional notes
    Write-Host "`nAny additional notes or observations? (press Enter to skip): " -ForegroundColor Cyan
    $notes = Read-Host
    if ($notes) {
        Write-Log "Additional notes: $notes" "INFO"
    }
    
    return $results
}

function Save-TestResults {
    param (
        [hashtable]$packageResults,
        [hashtable]$featureResults,
        [string]$outputPath
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $reportFile = "$outputPath\gui_test_report_$timestamp.md"
    
    $content = @"
# GlowingGoldenGlobe GUI Test Report
Generated: $(Get-Date)

## Environment
- Python: $(python --version 2>&1)
- System: $(Get-WmiObject -Class Win32_OperatingSystem | Select-Object -ExpandProperty Caption)

## Package Status
| Package | Status |
|---------|--------|
$(foreach ($pkg in $packageResults) {
    "| $($pkg.Package) | $($pkg.Status) |"
})

## Feature Test Results
| Feature | Status |
|---------|--------|
$(foreach ($feature in $featureResults.Keys) {
    "| $feature | $($featureResults[$feature]) |"
})

## Recommendations
"@
    
    # Add recommendations based on test results
    $recommendations = @()
    
    # Check for package issues
    $missingPackages = $packageResults | Where-Object { $_.Status -eq "Missing" } | ForEach-Object { $_.Package }
    if ($missingPackages) {
        $recommendations += "Install missing packages: $($missingPackages -join ', ')"
    }
    
    # Check for feature issues
    $problematicFeatures = $featureResults.Keys | Where-Object { $featureResults[$_] -like "Issue:*" }
    if ($problematicFeatures) {
        $recommendations += "Address issues with these features: $($problematicFeatures -join ', ')"
    }
    
    # Add recommendations to report
    if ($recommendations) {
        $content += "`n" + ($recommendations | ForEach-Object { "- $_" } | Out-String)
    }
    else {
        $content += "`n- All tests passed successfully. No specific recommendations."
    }
    
    # Save the report
    $content | Out-File -FilePath $reportFile -Encoding utf8
    Write-Log "Test report saved to: $reportFile" "SUCCESS"
    
    # Open the report
    Invoke-Item $reportFile
}

# Main execution
Clear-Host
Write-Host "GlowingGoldenGlobe - GUI Functionality Test" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host

Write-Log "Starting GUI functionality test" "INFO"

# Test Python installation
if (-not (Test-PythonInstallation)) {
    Write-Log "Python not available. Cannot continue tests." "ERROR"
    exit 1
}

# Test required packages
$packageResults = Test-RequiredPackages

# Test GUI launcher existence
if (-not (Test-GUILauncher)) {
    Write-Log "GUI launcher not found. Cannot continue tests." "ERROR"
    exit 1
}

# Ask user if they want to launch the GUI
Write-Host "`nWould you like to launch the GUI for interactive testing? (Y/N): " -ForegroundColor Cyan -NoNewline
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    $featureResults = Launch-GUI
    
    # Save test results
    Save-TestResults -packageResults $packageResults -featureResults $featureResults -outputPath $projectRoot
}
else {
    Write-Log "Interactive testing skipped by user" "INFO"
}

Write-Log "GUI functionality test completed" "SUCCESS"
Write-Host "`nTest completed. Check the log file for details: $logFile" -ForegroundColor Green
