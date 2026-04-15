# Insurance AI Application Monitoring Dashboard

This directory contains Azure Monitor Workbooks for monitoring the Insurance AI application.

## Files

- `insurance-ai-dashboard.workbook` - Azure Monitor Workbook template for application monitoring
- `setup-dashboard.ps1` - PowerShell script to create and configure the dashboard
- `monitoring_dashboard.py` - Streamlit component for local monitoring dashboard
- `README.md` - This documentation file

## Dashboard Features

The monitoring dashboard includes:

### Application Health
- Request count and response times
- Error rates and failed requests
- Application availability

### Performance Metrics
- RAG query latency
- Chat request throughput
- Document upload metrics

### Custom Telemetry
- LangSmith tracing integration
- Azure Application Insights distributed tracing
- Custom metrics from the observability module

### Infrastructure Monitoring
- Redis memory usage (if using containerized Redis)
- Container health (if deployed via Docker)

## Setup Instructions

### Prerequisites

1. Azure Application Insights resource configured
2. Application deployed with observability enabled
3. Azure CLI installed (optional, for automated setup)

### Option 1: Manual Setup via Azure Portal

1. Go to Azure Portal → Application Insights resource
2. Navigate to "Workbooks" in the left menu
3. Click "New" → "New Workbook"
4. Click "Advanced Editor" (</>) button
5. Copy the content from `insurance-ai-dashboard.workbook`
6. Click "Apply" to save the workbook

### Option 2: Automated Setup

Run the PowerShell script:

```powershell
.\setup-dashboard.ps1 -SubscriptionId "your-subscription-id" -ResourceGroup "your-rg" -AppInsightsName "your-app-insights-name"
```

## Local Development Monitoring

For local development and testing, you can integrate the monitoring dashboard directly into your Streamlit app:

### Add to app.py

```python
# Add this import at the top of app.py
from monitoring_dashboard.monitoring_dashboard import render_monitoring_dashboard

# Add this to your sidebar or main content
if st.sidebar.checkbox("📊 Monitoring Dashboard"):
    render_monitoring_dashboard()
```

### Features of Local Dashboard

- **Health Tab**: Application status, observability configuration, backend connectivity
- **Performance Tab**: Response times, error rates, RAG latency metrics
- **Usage Tab**: Chat requests, document uploads, user activity trends
- **System Tab**: Memory backend status, Redis connectivity, system resources

## Dashboard Sections

### 1. Overview
- Application status summary
- Key metrics at a glance
- Recent alerts and issues

### 2. Performance
- Response time trends
- Throughput charts
- RAG latency analysis

### 3. Errors & Reliability
- Error rate monitoring
- Exception tracking
- Failed request analysis

### 4. Usage Analytics
- Chat request patterns
- Document upload trends
- User engagement metrics

### 5. Infrastructure
- Redis memory monitoring
- Container resource usage
- System health indicators

## Custom Queries

The dashboard uses KQL queries to analyze Application Insights telemetry:

```kql
// Chat requests over time
AppRequests
| where Name contains "chat"
| summarize count() by bin(TimeGenerated, 5m)
| render timechart
```

```kql
// RAG latency percentiles
AppMetrics
| where Name == "insurance_ai.rag.latency_ms"
| summarize percentiles(Value, 50, 95, 99) by bin(TimeGenerated, 1h)
```

## Alerts Configuration

Set up alerts for critical metrics:

1. High error rate (>5%)
2. Slow response times (>10s)
3. Redis connection failures
4. High memory usage

## Troubleshooting

### Dashboard Not Loading Data
- Verify Application Insights connection string is correct
- Check that telemetry is being sent from the application
- Confirm time range settings

### Missing Custom Metrics
- Ensure observability.py is properly initialized
- Check Azure Application Insights SDK is installed
- Verify APPLICATIONINSIGHTS_CONNECTION_STRING environment variable

### Performance Issues
- Use sampling for high-traffic applications
- Configure appropriate retention policies
- Monitor ingestion costs

## Integration with CI/CD

Add dashboard deployment to your pipeline:

```yaml
- task: AzureCLI@2
  displayName: 'Deploy Monitoring Dashboard'
  inputs:
    azureSubscription: 'your-service-connection'
    scriptType: 'ps'
    scriptLocation: 'inlineScript'
    inlineScript: |
      .\setup-dashboard.ps1 -SubscriptionId "$(subscriptionId)" -ResourceGroup "$(resourceGroup)" -AppInsightsName "$(appInsightsName)"
```