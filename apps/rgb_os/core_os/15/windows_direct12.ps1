# Windows PowerShell Direct Screen Renderer
# Usage: .\windows_direct.ps1 -HtmlFile "test.html" -FPS 3

param(
    [Parameter(Mandatory=$true)]
    [string]$HtmlFile,
    
    [Parameter(Mandatory=$false)]
    [int]$FPS = 2,
    
    [Parameter(Mandatory=$false)]
    [switch]$Fullscreen
)

# Add required assemblies
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# P/Invoke for wallpaper setting
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class WallpaperChanger {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);
    
    public const int SPI_SETDESKWALLPAPER = 20;
    public const int SPIF_UPDATEINIFILE = 0x01;
    public const int SPIF_SENDCHANGE = 0x02;
}
"@

Write-Host "🪟 Windows PowerShell Direct Screen Renderer" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta

# Check if HTML file exists
if (-not (Test-Path $HtmlFile)) {
    Write-Host "❌ HTML file not found: $HtmlFile" -ForegroundColor Red
    exit 1
}

# Get screen resolution
$Screen = [System.Windows.Forms.Screen]::PrimaryScreen
$ScreenWidth = $Screen.Bounds.Width
$ScreenHeight = $Screen.Bounds.Height

Write-Host "📺 Screen resolution: $ScreenWidth x $ScreenHeight" -ForegroundColor Green

# Setup temp directory
$TempDir = $env:TEMP
$TempImage = Join-Path $TempDir "screen_render.png"

# Convert HTML file to absolute path
$HtmlPath = (Resolve-Path $HtmlFile).Path
$HtmlUri = "file:///$($HtmlPath.Replace('\', '/'))"

Write-Host "🎬 Starting direct rendering of: $HtmlFile" -ForegroundColor Cyan
Write-Host "⚠️  This will take over your screen! Press Ctrl+C to stop" -ForegroundColor Yellow

# Create rendering function
function Render-HTMLToScreen {
    param($HtmlUri, $OutputPath, $Width, $Height)
    
    $ChromePaths = @(
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
    )
    
    $ChromeExe = $null
    foreach ($path in $ChromePaths) {
        if (Test-Path $path) {
            $ChromeExe = $path
            break
        }
    }
    
    if (-not $ChromeExe) {
        Write-Host "❌ Chrome or Edge not found. Please install Chrome or Edge." -ForegroundColor Red
        return $false
    }
    
    $Args = @(
        "--headless",
        "--disable-gpu",
        "--window-size=$Width,$Height",
        "--screenshot=`"$OutputPath`"",
        "`"$HtmlUri`""
    )
    
    try {
        $Process = Start-Process -FilePath $ChromeExe -ArgumentList $Args -Wait -PassThru -WindowStyle Hidden
        return ($Process.ExitCode -eq 0)
    } catch {
        Write-Host "⚠️ Rendering error: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

function Set-Wallpaper {
    param($ImagePath)
    try {
        $Result = [WallpaperChanger]::SystemParametersInfo(
            [WallpaperChanger]::SPI_SETDESKWALLPAPER, 
            0, 
            $ImagePath, 
            [WallpaperChanger]::SPIF_UPDATEINIFILE -bor [WallpaperChanger]::SPIF_SENDCHANGE
        )
        return $Result -ne 0
    } catch {
        Write-Host "⚠️ Wallpaper setting error: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

function Show-FullscreenImage {
    param($ImagePath)
    
    if (-not (Test-Path $ImagePath)) { return }
    
    $Form = New-Object System.Windows.Forms.Form
    $Form.WindowState = 'Maximized'
    $Form.FormBorderStyle = 'None'
    $Form.TopMost = $true
    $Form.BackColor = [System.Drawing.Color]::Black
    
    try {
        $Image = [System.Drawing.Image]::FromFile($ImagePath)
        $Form.BackgroundImage = $Image
        $Form.BackgroundImageLayout = 'Stretch'
        
        $Form.Show()
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 100
        $Form.Close()
        $Image.Dispose()
    } catch {
        Write-Host "⚠️ Display error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Main rendering loop
$FrameCount = 0
$StartTime = Get-Date
$FrameInterval = 1000 / $FPS

Write-Host "🚀 Rendering started at $FPS FPS..." -ForegroundColor Green

try {
    while ($true) {
        $FrameStart = Get-Date
        
        if (Render-HTMLToScreen -HtmlUri $HtmlUri -OutputPath $TempImage -Width $ScreenWidth -Height $ScreenHeight) {
            if ($Fullscreen) {
                Show-FullscreenImage -ImagePath $TempImage
            } else {
                Set-Wallpaper -ImagePath $TempImage
            }
            
            $FrameCount++
            if ($FrameCount % 10 -eq 0) {
                $Elapsed = (Get-Date) - $StartTime
                $ActualFPS = $FrameCount / $Elapsed.TotalSeconds
                Write-Host "📊 Frame $FrameCount, $([math]::Round($ActualFPS, 1)) fps actual" -ForegroundColor Cyan
            }
        } else {
            Write-Host "⚠️ Frame $FrameCount render failed" -ForegroundColor Yellow
        }
        
        $FrameTime = ((Get-Date) - $FrameStart).TotalMilliseconds
        $Delay = [math]::Max(0, $FrameInterval - $FrameTime)
        if ($Delay -gt 0) {
            Start-Sleep -Milliseconds $Delay
        }
    }
} catch {
    Write-Host "🛑 Rendering stopped: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
    if (Test-Path $TempImage) {
        Remove-Item $TempImage -Force
    }
    [WallpaperChanger]::SystemParametersInfo(20, 0, "", 3)
    Write-Host "✅ Cleanup complete, desktop restored" -ForegroundColor Green
}
