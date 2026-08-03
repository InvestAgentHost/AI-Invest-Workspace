[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [int]$Port = 9222,
    [string]$UserDataDir = "$env:TEMP\x-research-browser",
    [string]$StartUrl = "https://x.com/",
    [string]$BrowserPath
)

function Get-BrowserPath([string]$ExplicitPath) {
    if ($ExplicitPath) {
        if (Test-Path -LiteralPath $ExplicitPath -PathType Leaf) {
            return (Resolve-Path -LiteralPath $ExplicitPath).Path
        }
        throw "BrowserPath does not exist: $ExplicitPath"
    }

    $candidates = @(
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:LocalAppData\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "$env:LocalAppData\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles}\BraveSoftware\Brave-Browser\Application\brave.exe",
        "${env:ProgramFiles(x86)}\BraveSoftware\Brave-Browser\Application\brave.exe",
        "$env:LocalAppData\BraveSoftware\Brave-Browser\Application\brave.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }

    foreach ($name in @("chrome.exe", "msedge.exe", "brave.exe", "chromium.exe")) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command -and $command.Source) { return $command.Source }
    }

    foreach ($name in @("chrome.exe", "msedge.exe", "brave.exe")) {
        $registryKeys = @(
            "Registry::HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\$name",
            "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\$name",
            "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\$name"
        )
        foreach ($key in $registryKeys) {
            if (-not (Test-Path -LiteralPath $key)) { continue }
            $registeredPath = (Get-Item -LiteralPath $key).GetValue("")
            if ($registeredPath -and (Test-Path -LiteralPath $registeredPath -PathType Leaf)) {
                return $registeredPath
            }
        }
    }

    $playwrightRoot = Join-Path $env:LocalAppData "ms-playwright"
    if (Test-Path -LiteralPath $playwrightRoot) {
        $playwrightChrome = Get-ChildItem -LiteralPath $playwrightRoot -Filter chrome.exe -Recurse -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
        if ($playwrightChrome) { return $playwrightChrome }
    }

    throw "Chrome, Edge, Brave, or Playwright Chromium was not found. Pass -BrowserPath with the browser executable."
}

$browserPath = Get-BrowserPath -ExplicitPath $BrowserPath
$arguments = @(
    "--remote-debugging-port=$Port",
    "--user-data-dir=`"$UserDataDir`"",
    $StartUrl
)

if ($PSCmdlet.ShouldProcess($browserPath, "Start an isolated browser for authorized X collection")) {
    Start-Process -FilePath $browserPath -ArgumentList $arguments -WindowStyle Normal | Out-Null
    Write-Host "Browser started. Log in to X manually in this window."
    Write-Host "CDP endpoint: http://127.0.0.1:$Port"
    Write-Host "Local browser profile: $UserDataDir"
}
