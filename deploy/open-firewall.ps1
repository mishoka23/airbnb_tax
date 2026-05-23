#Requires -RunAsAdministrator

$rules = @(
    @{
        Name = "Airbnb Tax HTTP"
        Port = 80
    },
    @{
        Name = "Airbnb Tax HTTPS"
        Port = 443
    }
)

foreach ($rule in $rules) {
    $existing = Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Firewall rule already exists: $($rule.Name)"
        continue
    }

    New-NetFirewallRule `
        -DisplayName $rule.Name `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $rule.Port `
        -Action Allow `
        -Profile Any | Out-Null

    Write-Host "Created firewall rule: $($rule.Name) on TCP $($rule.Port)"
}
