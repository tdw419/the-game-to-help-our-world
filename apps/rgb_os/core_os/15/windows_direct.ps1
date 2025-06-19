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
        }
        else {
            Write-Host "⚠️ Frame $FrameCount render failed" -ForegroundColor Yellow
        }

        $FrameTime = ((Get-Date) - $FrameStart).TotalMilliseconds
        $Delay = [math]::Max(0, $FrameInterval - $FrameTime)
        if ($Delay -gt 0) {
            Start-Sleep -Milliseconds $Delay
        }
    }
}
catch {
    Write-Host "🛑 Rendering stopped: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
    if (Test-Path $TempImage) {
        Remove-Item $TempImage -Force
    }
    [WallpaperChanger]::SystemParametersInfo(20, 0, "", 3)
    Write-Host "✅ Cleanup complete, desktop restored" -ForegroundColor Green
}
