param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("0","10","50","100")]
    [string]$Canary
)

$configPath = "nginx\canary.conf"
$content = Get-Content $configPath -Raw

switch ($Canary) {
    "0" {
        $stableLine = "        server app-stable:8000;"
        $canaryLine = "        server app-canary:8000 down;"
        $msg = "Rolled back. 100% traffic on Stable."
    }
    "10" {
        $stableLine = "        server app-stable:8000 weight=9;"
        $canaryLine = "        server app-canary:8000 weight=1;"
        $msg = "Canary at 10%. Stable gets 90% of traffic."
    }
    "50" {
        $stableLine = "        server app-stable:8000 weight=1;"
        $canaryLine = "        server app-canary:8000 weight=1;"
        $msg = "Canary at 50%. Traffic split evenly."
    }
    "100" {
        $stableLine = "        server app-stable:8000 down;"
        $canaryLine = "        server app-canary:8000;"
        $msg = "Canary at 100%. Fully promoted to production."
    }
}

$content = $content -replace "        server app-stable:8000[^\n]*", $stableLine
$content = $content -replace "        server app-canary:8000[^\n]*", $canaryLine

[System.IO.File]::WriteAllText((Resolve-Path $configPath), $content, [System.Text.UTF8Encoding]::new($false))
docker compose -f docker-compose.canary.yml exec nginx nginx -s reload
Write-Host $msg
