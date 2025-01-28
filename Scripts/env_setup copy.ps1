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
        [switch]$waitForWindow
    )
    
    Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class Window {
            [DllImport("user32.dll")]
            public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int nWidth, int nHeight, bool bRepaint);
            
            [DllImport("user32.dll")]
            public static extern IntPtr GetForegroundWindow();
            
            [DllImport("user32.dll")]
            public static extern bool SetForegroundWindow(IntPtr hWnd);
            
            [DllImport("user32.dll")]
            [return: MarshalAs(UnmanagedType.Bool)]
            public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
            
            [DllImport("user32.dll", SetLastError = true)]
            public static extern bool BringWindowToTop(IntPtr hWnd);
        }

        public struct RECT
        {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;
        }
"@

    if ($waitForWindow) {
        Start-Sleep -Seconds 1
    }
    
    # Get all processes with the given name
    $processes = Get-Process | Where-Object { $_.ProcessName -like "*$processName*" -and $_.MainWindowHandle -ne 0 }
    
    foreach ($process in $processes) {
        # Get the target monitor
        $screens = [System.Windows.Forms.Screen]::AllScreens
        if ($monitorIndex -ge $screens.Count) {
            Write-Host "Monitor index $monitorIndex not found. Using primary monitor."
            $monitorIndex = 0
        }
        
        # Adjust coordinates based on monitor position
        $monitor = $screens[$monitorIndex]
        $actualX = $x + $monitor.Bounds.X
        $actualY = $y + $monitor.Bounds.Y
        
        # Try to move the window multiple times
        $maxAttempts = 3
        $attempt = 0
        $success = $false
        
        while ($attempt -lt $maxAttempts -and -not $success) {
            try {
                [void][Window]::MoveWindow($process.MainWindowHandle, $actualX, $actualY, $width, $height, $true)
                [void][Window]::SetForegroundWindow($process.MainWindowHandle)
                [void][Window]::BringWindowToTop($process.MainWindowHandle)
                $success = $true
            }
            catch {
                Start-Sleep -Milliseconds 500
                $attempt++
            }
        }
    }
}

# Kill existing VSCode processes (optional, uncomment if needed)
# Get-Process | Where-Object { $_.ProcessName -like "*Code*" } | Stop-Process -Force

# Path definitions
$path1 = "I:\WORKSPACE\Applications\mark_csv_exct\Project_4"
$path2 = "C:\Users\Tobia\Downloads\Developments-main\dynamic_v0_05_01"

# Get screen information
$screens = [System.Windows.Forms.Screen]::AllScreens
Write-Host "Detected $($screens.Count) monitors"

# Calculate dimensions for first monitor
$monitor1 = $screens[0]
$windowWidth = $monitor1.Bounds.Width / 2
$windowHeight = $monitor1.Bounds.Height / 2

# Function to wait for VSCode window
function Wait-ForVSCodeWindow {
    $maxAttempts = 30
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        $vsCodeProcesses = Get-Process | Where-Object { $_.ProcessName -like "*Code*" -and $_.MainWindowHandle -ne 0 }
        if ($vsCodeProcesses.Count -gt 0) {
            return $true
        }
        Start-Sleep -Milliseconds 500
        $attempt++
    }
    return $false
}

# Open and position first VSCode window
Set-Location -Path $path1
Start-Process "cmd" -ArgumentList "/c code . && exit"
Wait-ForVSCodeWindow
Start-Sleep -Seconds 2
Set-WindowPosition -processName "Code" -x 0 -y 0 -width $windowWidth -height $windowHeight -monitorIndex 0 -waitForWindow

# Open and position second VSCode window
Set-Location -Path $path2
Start-Process "cmd" -ArgumentList "/c code . && exit"
Wait-ForVSCodeWindow
Start-Sleep -Seconds 2
Set-WindowPosition -processName "Code" -x 0 -y $windowHeight -width $windowWidth -height $windowHeight -monitorIndex 0 -waitForWindow

# Open File Explorer windows
Start-Process "explorer.exe" -ArgumentList $path1
Start-Process "explorer.exe" -ArgumentList $path2
Start-Sleep -Seconds 2

# Position File Explorer windows
Set-WindowPosition -processName "explorer" -x $windowWidth -y 0 -width $windowWidth -height $windowHeight -monitorIndex 0 -waitForWindow
Start-Sleep -Seconds 1
Set-WindowPosition -processName "explorer" -x $windowWidth -y $windowHeight -width $windowWidth -height $windowHeight -monitorIndex 0 -waitForWindow

Write-Host "Development environment setup complete!"
Write-Host "VSCode windows positioned on the left"
Write-Host "File Explorer windows positioned on the right"