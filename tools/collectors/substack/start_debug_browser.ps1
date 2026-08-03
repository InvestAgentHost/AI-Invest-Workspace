[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [int]$Port = 9222,
    [string]$UserDataDir = "$env:TEMP\substack-archive-browser",
    [string]$StartUrl = "https://substack.com/"
)

function Get-BrowserPath {
    $candidates = @(
        "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe",
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
        "$env:LocalAppData\Microsoft\Edge\Application\msedge.exe",
        "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $registryKeys = @(
        'Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe',
        'Registry::HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe',
        'Registry::HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe',
        'Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe',
        'Registry::HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe',
        'Registry::HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe'
    )

    foreach ($key in $registryKeys) {
        if (Test-Path $key) {
            $item = Get-Item $key
            $executable = $item.GetValue('')
            if ($executable -and (Test-Path $executable)) {
                return $executable
            }
        }
    }

    throw 'Edge or Chrome was not found. Install one of them or start the browser manually with a remote debugging port.'
}

$browserPath = Get-BrowserPath
$arguments = @(
    "--remote-debugging-port=$Port",
    "--user-data-dir=$UserDataDir",
    $StartUrl
)

if ($PSCmdlet.ShouldProcess($browserPath, "Start browser with remote debugging")) {
    Start-Process -FilePath $browserPath -ArgumentList $arguments | Out-Null
    Write-Host "Browser started: $browserPath"
    Write-Host "Debug endpoint: http://127.0.0.1:$Port"
    Write-Host "User data dir: $UserDataDir"
}