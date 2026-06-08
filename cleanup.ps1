# Cleanup script for GPU Monitor Dashboard (Windows)
# This script helps resolve container configuration issues

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "GPU Monitor Dashboard Cleanup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Stop and remove the container
Write-Host "🛑 Stopping and removing container..." -ForegroundColor Yellow
docker-compose down

# Remove the container completely
Write-Host "🗑️  Removing container..." -ForegroundColor Yellow
docker rm -f gpu-monitor-dashboard 2>$null

# Remove the image
Write-Host "🗑️  Removing Docker image..." -ForegroundColor Yellow
docker rmi gpu-monitor-dashboard_gpu-monitor 2>$null

# Prune dangling images
Write-Host "🧹 Pruning dangling images..." -ForegroundColor Yellow
docker image prune -f

# Clean up Docker system
Write-Host "🧹 Cleaning up Docker system..." -ForegroundColor Yellow
docker system prune -f

Write-Host ""
Write-Host "✅ Cleanup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To redeploy:" -ForegroundColor White
Write-Host "   .\deploy.ps1" -ForegroundColor Gray
Write-Host ""
