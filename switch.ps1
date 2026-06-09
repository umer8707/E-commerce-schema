param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("blue","green")]
    [string]$Target
)

$configPath = "nginx\nginx.conf"
$content = Get-Content $configPath -Raw

$current = if ($content -match "server app-blue:8000") { "blue" } else { "green" }

if ($current -eq $Target) {
    Write-Host "Already on $Target. No change needed."
    exit 0
}

if ($Target -eq "blue") {
    $content = $content -replace "server app-green:8000;", "server app-blue:8000;"
} else {
    $content = $content -replace "server app-blue:8000;", "server app-green:8000;"
}

Set-Content -Path $configPath -Value $content -NoNewline -Encoding utf8
docker compose -f docker-compose.blue-green.yml exec nginx nginx -s reload
Write-Host "Switched from $current to $Target. Traffic now going to $Target."
