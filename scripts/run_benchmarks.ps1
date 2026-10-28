# run_benchmarks.ps1
# Orquestador del Benchmark para PowerShell en Windows
# Ejecuta el runner y ajusta las variables de entorno para Docker Compose

param(
    [switch]$Pilot = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $ScriptDir "..")

$Engines = @("MongoDB", "PostgreSQL")
$Profiles = @("PROFILE_A_BASELINE", "PROFILE_B_MEDIUM", "PROFILE_C_SEVERE")
$Queries = @("Q1", "Q2")
$Concurrencies = @(1, 10, 50)
$RunsPerCell = 3

function Apply-ResourceProfile {
    param([string]$ProfileName)
    Write-Host "[*] Aplicando límites cgroups v2 para: $ProfileName" -ForegroundColor Cyan
    switch ($ProfileName) {
        "PROFILE_A_BASELINE" {
            $env:BENCHMARK_CPUS = "4.0"
            $env:BENCHMARK_MEMORY = "4096m"
            $env:BENCHMARK_MEM_SWAP = "4096m"
        }
        "PROFILE_B_MEDIUM" {
            $env:BENCHMARK_CPUS = "2.0"
            $env:BENCHMARK_MEMORY = "2048m"
            $env:BENCHMARK_MEM_SWAP = "2048m"
        }
        "PROFILE_C_SEVERE" {
            $env:BENCHMARK_CPUS = "1.0"
            $env:BENCHMARK_MEMORY = "1024m"
            $env:BENCHMARK_MEM_SWAP = "1024m"
        }
    }
    docker compose up -d --remove-orphans
    Start-Sleep -Seconds 5
}

if ($Pilot) {
    Write-Host "==========================================================" -ForegroundColor Yellow
    Write-Host " MODO PILOTO: Ejecutando 1 celda de prueba y verificación " -ForegroundColor Yellow
    Write-Host "==========================================================" -ForegroundColor Yellow
    Apply-ResourceProfile "PROFILE_A_BASELINE"
    python benchmark_runner.py --engine "MongoDB" --profile "PROFILE_A_BASELINE" --query "Q1" --concurrency 1 --run-number 1 --warmup 10 --duration 30 --cooldown 5
    Write-Host "[+] Prueba piloto completada. Revise ./results/benchmark_results.csv" -ForegroundColor Green
    exit 0
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " INICIANDO MATRIZ DE BENCHMARK COMPLETA (36 celdas × 3)   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

$cellCounter = 0
foreach ($engine in $Engines) {
    foreach ($profile in $Profiles) {
        Apply-ResourceProfile $profile
        foreach ($query in $Queries) {
            foreach ($concurrency in $Concurrencies) {
                $cellCounter++
                Write-Host "`n>>> Celda $cellCounter / 36: Motor=$engine | Perfil=$profile | Query=$query | Concurrencia=$concurrency <<<" -ForegroundColor Magenta
                for ($run = 1; $run -le $RunsPerCell; $run++) {
                    Write-Host "--- Corrida $run de $RunsPerCell ---" -ForegroundColor Yellow
                    python benchmark_runner.py --engine $engine --profile $profile --query $query --concurrency $concurrency --run-number $run --warmup 60 --duration 300 --cooldown 60
                }
            }
        }
    }
}

