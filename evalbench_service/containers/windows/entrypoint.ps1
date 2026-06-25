# evalbench_service/containers/windows/entrypoint.ps1
$ErrorActionPreference = 'Stop'

# Ensure we are in the correct directory
Set-Location C:\evalbench

# Check if we are running in Kubernetes (GKE)
if ($env:KUBERNETES_SERVICE_HOST) {
    Write-Host "GKE detected. Starting evalbench server in standalone mode..."
    # In GKE, we only run the gRPC server.
    # We run it in the foreground so the container stays alive as long as the server runs.
    python evalbench/eval_server.py
} else {
    Write-Host "Combined mode detected. Starting server, frontend, and precompute on Windows..."
    
    # Set precompute interval to 30 seconds for combined/local mode (matches Linux entrypoint)
    $env:PRECOMPUTE_INTERVAL = "30"
    
    # Start evalbench_server (gRPC)
    Write-Host "Starting evalbench_server..."
    $server = Start-Process -FilePath "python" -ArgumentList "evalbench/eval_server.py" -PassThru -NoNewWindow
    
    # Start precompute_trends
    Write-Host "Starting precompute_trends..."
    $precompute = Start-Process -FilePath "python" -ArgumentList "viewer/run_precompute.py" -PassThru -NoNewWindow
    
    # Start frontend (using waitress instead of gunicorn on Windows)
    Write-Host "Starting frontend (waitress)..."
    # We run waitress-serve. It should be in the .venv\Scripts which is in PATH.
    $frontend = Start-Process -FilePath "waitress-serve" -ArgumentList "--port=3000", "main:me" -WorkingDirectory "C:\evalbench\viewer" -PassThru -NoNewWindow
    
    # Monitor processes
    Write-Host "Monitoring processes..."
    while ($true) {
        if ($server.HasExited) {
            Write-Error "evalbench_server exited with code $($server.ExitCode)!"
            break
        }
        if ($frontend.HasExited) {
            Write-Error "frontend exited with code $($frontend.ExitCode)!"
            break
        }
        if ($precompute.HasExited) {
            Write-Host "precompute_trends exited, restarting..."
            $precompute = Start-Process -FilePath "python" -ArgumentList "viewer/run_precompute.py" -PassThru -NoNewWindow
        }
        Start-Sleep -Seconds 2
    }
    
    # Clean up processes on exit
    Write-Host "Shutting down processes..."
    Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $precompute.Id -Force -ErrorAction SilentlyContinue
    
    Exit 1 # Exit with error if any main process crashed
}
