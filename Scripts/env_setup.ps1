# Add necessary type for screen handling
Add-Type -AssemblyName System.Windows.Forms

# Function to move and resize window
function Set-WindowPosition {
    param(
        [string]$processName,
        [int]$x,
        [int]$y,
        [int]$width,
        [int]$height,
        [int]$monitorIndex = 0,
        [string]$windowTitle = ""
    )
    
    Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class Window {
            [DllImport("user32.dll")]
            public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int nWidth, int nHeight, bool bRepaint);
            
            [DllImport("user32.dll")]
            public static extern bool SetForegroundWindow(IntPtr hWnd);
            
            [DllImport("user32.dll")]
            public static extern bool BringWindowToTop(IntPtr hWnd);
        }
"@

    $processes = Get-Process | Where-Object { 
        $_.ProcessName -like "*$processName*" -and 
        $_.MainWindowHandle -ne 0 -and
        ($windowTitle -eq "" -or $_.MainWindowTitle -like "*$windowTitle*")
    }
    
    foreach ($process in $processes) {
        $monitor = [System.Windows.Forms.Screen]::AllScreens[$monitorIndex]
        $actualX = $x + $monitor.Bounds.X
        $actualY = $y + $monitor.Bounds.Y
        
        [void][Window]::MoveWindow($process.MainWindowHandle, $actualX, $actualY, $width, $height, $true)
        [void][Window]::SetForegroundWindow($process.MainWindowHandle)
        [void][Window]::BringWindowToTop($process.MainWindowHandle)
    }
}

# Path definitions
$path1 = "I:\WORKSPACE\Applications\mark_csv_exct\Project_4"
$path2 = "C:\Users\Tobia\Downloads\Developments-main\dynamic_v0_05_01"

# Get screen information and calculate dimensions
$monitor1 = [System.Windows.Forms.Screen]::AllScreens[0]
$windowWidth = $monitor1.Bounds.Width / 2
$windowHeight = $monitor1.Bounds.Height / 2

# Open VSCode windows
Set-Location -Path $path1
Start-Process "cmd" -ArgumentList "/c code . && exit" -NoNewWindow
Set-Location -Path $path2
Start-Process "cmd" -ArgumentList "/c code . && exit" -NoNewWindow

# Open File Explorer windows with specific paths
Start-Process "explorer.exe" -ArgumentList $path2  # dynamic_v0_05_01 (top right)
Start-Process "explorer.exe" -ArgumentList $path1  # mark_csv_exct (bottom right)

# Quick wait for windows to initialize
Start-Sleep -Milliseconds 800

# Position VSCode windows (left side)
Set-WindowPosition -processName "Code" -x 0 -y 0 -width $windowWidth -height $windowHeight -monitorIndex 0
Start-Sleep -Milliseconds 300
Set-WindowPosition -processName "Code" -x 0 -y $windowHeight -width $windowWidth -height $windowHeight -monitorIndex 0

# Position File Explorer windows (right side)
Set-WindowPosition -processName "explorer" -windowTitle "dynamic_v0_05_01" -x $windowWidth -y 0 -width $windowWidth -height $windowHeight -monitorIndex 0
Set-WindowPosition -processName "explorer" -windowTitle "Project_4" -x $windowWidth -y $windowHeight -width $windowWidth -height $windowHeight -monitorIndex 0

Write-Host "Setup complete!"