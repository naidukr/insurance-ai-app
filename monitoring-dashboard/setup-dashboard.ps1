param(
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,

    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory=$true)]
    [string]$AppInsightsName,

    [Parameter(Mandatory=$false)]
    [string]$WorkbookName = "Insurance AI Monitoring Dashboard",

    [Parameter(Mandatory=$false)]
    [string]$WorkbookDescription = "Comprehensive monitoring dashboard for Insurance AI application with performance, errors, usage analytics, and infrastructure metrics"
)

# Login to Azure (uncomment if not already logged in)
# az login

# Set subscription
Write-Host "Setting subscription to: $SubscriptionId"
az account set --subscription $SubscriptionId

# Get Application Insights resource ID
Write-Host "Getting Application Insights resource details..."
$appInsights = az monitor app-insights component show `
    --resource-group $ResourceGroup `
    --name $AppInsightsName `
    --query "{id:id, location:location}" `
    --output json | ConvertFrom-Json

if (-not $appInsights) {
    Write-Error "Application Insights resource '$AppInsightsName' not found in resource group '$ResourceGroup'"
    exit 1
}

Write-Host "Found Application Insights: $($appInsights.id)"

# Read workbook template
$workbookPath = Join-Path $PSScriptRoot "insurance-ai-dashboard.workbook"
if (-not (Test-Path $workbookPath)) {
    Write-Error "Workbook template not found at: $workbookPath"
    exit 1
}

$workbookContent = Get-Content $workbookPath -Raw

# Create workbook
Write-Host "Creating workbook: $WorkbookName"
$workbookResult = az monitor workbook create `
    --resource-group $ResourceGroup `
    --name $WorkbookName `
    --location $appInsights.location `
    --serialized-data $workbookContent `
    --tags "application=insurance-ai" "component=monitoring" "created-by=powershell" `
    --query "{id:id, name:name}" `
    --output json

if ($LASTEXITCODE -eq 0) {
    $workbook = $workbookResult | ConvertFrom-Json
    Write-Host "✅ Workbook created successfully!"
    Write-Host "📊 Workbook ID: $($workbook.id)"
    Write-Host "📊 Workbook Name: $($workbook.name)"
    Write-Host ""
    Write-Host "🔗 Access your dashboard at:"
    Write-Host "https://portal.azure.com/#resource$($workbook.id)"
    Write-Host ""
    Write-Host "📋 Next steps:"
    Write-Host "1. Open the workbook in Azure Portal"
    Write-Host "2. Adjust time ranges and parameters as needed"
    Write-Host "3. Pin important charts to Azure dashboards"
    Write-Host "4. Set up alerts based on key metrics"
} else {
    Write-Error "Failed to create workbook. Check Azure CLI authentication and permissions."
    exit 1
}

# Optional: Create sample alerts
Write-Host ""
$createAlerts = Read-Host "Do you want to create sample alerts for critical metrics? (y/n)"
if ($createAlerts -eq "y" -or $createAlerts -eq "Y") {
    Write-Host "Creating sample alerts..."

    # High error rate alert
    az monitor metrics alert create `
        --name "High Error Rate" `
        --resource $appInsights.id `
        --description "Alert when application error rate exceeds 5%" `
        --condition "total requests failed / total requests > 0.05" `
        --window-size 5m `
        --evaluation-frequency 1m `
        --severity 2

    # Slow response time alert
    az monitor metrics alert create `
        --name "Slow Response Time" `
        --resource $appInsights.id `
        --description "Alert when average response time exceeds 10 seconds" `
        --condition "avg response time > 10000" `
        --window-size 5m `
        --evaluation-frequency 1m `
        --severity 2

    Write-Host "✅ Sample alerts created!"
}

Write-Host ""
Write-Host "🎉 Dashboard setup complete!"
Write-Host "Monitor your Insurance AI application performance, errors, and usage patterns."