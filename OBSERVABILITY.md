# Observability Guide - LangSmith & Azure Application Insights

This document describes the observability stack for the Insurance AI application, including LangSmith tracing for LLM chains and Azure Application Insights for distributed tracing and monitoring.

## Overview

The Insurance AI application includes optional observability features:

- **LangSmith Tracing**: Monitor and debug LLM calls, chain execution, and performance
- **Azure Application Insights**: Distributed tracing, metrics, and diagnostics for the entire application
- **Custom Metrics**: Track business metrics like chat requests, document uploads, RAG latency

Both are **optional** — the application works without them, but they provide valuable insights into the system's behavior.

## Architecture

```
┌─────────────────────────────────────┐
│  FastAPI Backend (Port 8000)        │
├─────────────────────────────────────┤
│  observability.py                   │
│  ├─ init_observability()            │
│  ├─ LangSmith tracer setup          │
│  ├─ Azure App Insights config       │
│  └─ Metrics collection              │
├─────────────────────────────────────┤
│  main.py endpoints + tracing        │
│  ├─ @trace_operation("chat")        │
│  ├─ log_langsmith_event()           │
│  └─ get_metrics().record_*()        │
├─────────────────────────────────────┤
│  LangSmith Dashboard (smith.langchain.com)
│  Azure Application Insights (Azure Portal)
└─────────────────────────────────────┘
```

## LangSmith Integration

### What is LangSmith?

LangSmith is a platform built by LangChain to trace, test, and monitor LLM applications. It helps you:
- **Debug chains**: See exactly what inputs/outputs flow through your LLM pipeline
- **Monitor performance**: Track latency, tokens used, and error rates
- **Optimize prompts**: Analyze which prompts work best
- **Replay runs**: Re-run failed chains with same inputs

### Setup LangSmith

#### 1. Create a LangSmith Account
- Go to [smith.langchain.com](https://smith.langchain.com)
- Sign up for free
- Create an organization (or use default)

#### 2. Get Your API Key
- In LangSmith dashboard: **Settings** → **API keys**
- Copy your API key

#### 3. Set Environment Variables
```env
# .env file
LANGSMITH_API_KEY=ls_<your_api_key>
LANGSMITH_PROJECT=insurance-ai
```

#### 4. Automatic Tracing
Once `LANGSMITH_API_KEY` is set, tracing activates automatically:
- Every RAG query is traced
- Every LLM call is recorded
- Chain execution flow is captured

### LangSmith Features in Insurance AI

#### Traced Operations
- `chat_completed` - Successful chat interactions
- `chat_error` - Failed chat requests with error info
- `chat_failed_no_rag` - RAG system initialization issues
- Custom business events via `log_langsmith_event()`

#### Example: View LangSmith Traces

After running chat requests, go to **smith.langchain.com → Projects → insurance-ai** and you'll see:

```json
{
  "name": "chat_completed",
  "inputs": {
    "message": "What is my policy limit?"
  },
  "outputs": {
    "response": "Your policy covers..."
  },
  "metadata": {
    "conversation_id": "conv-2026-04-15T...",
    "has_context": true
  }
}
```

## Azure Application Insights Integration

### What is Application Insights?

Application Insights is Azure's Application Performance Monitoring (APM) service for monitoring:
- **Distributed traces**: End-to-end request flow across services
- **Custom metrics**: Business and technical KPIs
- **Exceptions & failures**: Automatic error tracking
- **Performance analytics**: Response times, throughput, dependencies

### Setup Azure Application Insights

#### Option 1: Manual Setup via Azure Portal

1. **Create Application Insights resource**
   ```bash
   az monitor app-insights component create \
     --app insurance-ai-appinsights \
     --location eastus \
     --resource-group <your-rg> \
     --application-type web
   ```

2. **Get Connection String**
   ```bash
   az monitor app-insights component show \
     --app insurance-ai-appinsights \
     --resource-group <your-rg> \
     --query connectionString
   ```

3. **Set in .env**
   ```env
   APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=<key>;IngestionEndpoint=https://<region>.in.applicationinsights.azure.com/;LiveEndpoint=https://<region>.livediagnostics.monitor.azure.com/
   ```

#### Option 2: Auto-Instrumentation via Bicep (Recommended)

Create `app-insights.bicep`:
```bicep
param location string = 'eastus'
param appName string = 'insurance-ai'

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${appName}-appinsights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 30
  }
}

output connectionString string = appInsights.properties.ConnectionString
```

Deploy:
```bash
az deployment group create \
  --template-file app-insights.bicep \
  --resource-group <your-rg>
```

### Application Insights Features in Insurance AI

#### Automatic Telemetry
- **Requests**: HTTP requests to FastAPI endpoints
- **Exceptions**: Uncaught errors with stack traces
- **Dependencies**: Calls to external services (Groq, Redis, etc.)
- **Performance counters**: CPU, memory usage

#### Custom Metrics
- `insurance_ai.chat.requests` - Total chat request count
- `insurance_ai.rag.latency_ms` - RAG query latency histogram
- `insurance_ai.documents.uploaded` - Documents uploaded count

#### Distributed Tracing
Each chat request creates a trace:
```
[Request] POST /api/chat
  └─ [Span] chat_request
     ├─ [Span] memory_save_user_message
     ├─ [Span] rag_retrieve_and_answer
     └─ [Span] memory_save_assistant_response
```

### Viewing Traces in Azure Portal

1. Go to **Azure Portal** → **Application Insights** → Your resource
2. Click **Performance** tab: See response times by operation
3. Click **Failures** tab: See which requests errored
4. Click **Metrics** tab: See custom metrics (chat requests, RAG latency)
5. Click **Logs** (KQL): Run custom queries on telemetry

Example KQL query - find slow chat requests:
```kusto
requests
| where name == "POST /api/chat"
| where duration > 5000
| project name, duration, timestamp, customDimensions
```

## Health Check Endpoint

The `/health` endpoint now includes observability status:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-04-15T10:30:00",
  "memory": {
    "status": "ok",
    "backend": "redis",
    "conversations": 5
  },
  "observability": {
    "status": "configured",
    "langsmith": {
      "enabled": true,
      "project": "insurance-ai"
    },
    "application_insights": {
      "enabled": true,
      "sdk_available": true
    },
    "telemetry": {
      "tracer": "enabled",
      "metrics": "enabled"
    }
  }
}
```

## Usage Examples

### Example 1: Enable Both LangSmith and Application Insights

```bash
# Set both APIs
export LANGSMITH_API_KEY=ls_<your_key>
export APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...

# Start FastAPI
python -m uvicorn main:app --reload
```

Server startup will show:
```
✅ LangSmith tracing enabled (project: insurance-ai)
✅ Azure Application Insights telemetry enabled
```

### Example 2: Send Chat with LangSmith Tracing

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my deductible?",
    "conversation_id": "conv-user-001"
  }'
```

Then in [smith.langchain.com](https://smith.langchain.com):
1. Go to **Projects** → **insurance-ai**
2. See the traced `chat_completed` event
3. Click to see inputs, outputs, metrics

### Example 3: Query Application Insights Logs

In Azure Portal, use KQL to analyze:

**Top 10 slowest chat requests:**
```kusto
requests
| where name == "POST /api/chat"
| top 10 by duration
| project name, duration, timestamp
```

**Error rate by endpoint:**
```kusto
requests
| summarize FailureCount=sumif(1, success == false), TotalCount=count() by name
| project name, FailureCount, TotalCount, ErrorRate=toreal(FailureCount)/TotalCount*100
| sort by ErrorRate desc
```

**Average RAG latency over time:**
```kusto
customMetrics
| where name == "insurance_ai.rag.latency_ms"
| summarize AvgLatency=avg(value) by bin(timestamp, 5m)
| render timechart
```

## Configuration Reference

### Environment Variables

| Variable | Purpose | Example | Optional |
|----------|---------|---------|----------|
| `LANGSMITH_API_KEY` | LangSmith API key for tracing | `ls_abc123...` | ✅ Yes |
| `LANGSMITH_PROJECT` | LangSmith project name | `insurance-ai` | ✅ Yes |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights telemetry | `InstrumentationKey=...` | ✅ Yes |

### Code Configuration

In `observability.py`:

```python
# Initialize observability
obs_config = init_observability()

# Get current config
config = get_observability_config()
print(config)
# Output:
# {
#   "langsmith_enabled": true,
#   "app_insights_enabled": true,
#   "tracer_available": true,
#   "meter_available": true
# }
```

## Troubleshooting

### "LangSmith API key not found"

**Problem**: Tracing not working

**Solution**:
1. Check `.env` has `LANGSMITH_API_KEY=ls_...`
2. Restart the FastAPI server
3. Verify key is valid: `echo $LANGSMITH_API_KEY`

### "Failed to configure Azure Application Insights"

**Problem**: App Insights not connecting

**Solutions**:
1. Check connection string format is correct
2. Verify Azure credentials are available (`az login`)
3. Check internet connectivity
4. App will continue working without App Insights (it's optional)

### LangSmith traces not appearing

**Problem**: Traced operations not showing in smith.langchain.com

**Solutions**:
1. Verify project name matches: `echo $LANGSMITH_PROJECT`
2. Check API key has proper permissions
3. Wait 5-10 seconds for traces to appear (they're batched)
4. Check browser Network tab for blocked requests to smith.langchain.com

### Application Insights metrics not showing

**Problem**: Custom metrics not visible in Azure Portal

**Solutions**:
1. Confirm connection string is correct
2. Ensure Azure SDK is installed: `pip install azure-monitor-opentelemetry-distro`
3. Send some test requests to generate metrics
4. Metrics appear within 1-2 minutes in Azure Portal

## Best Practices

### 1. Use LangSmith for Development
- Debug LLM chain logic during development
- Test different prompts and see results
- Monitor token usage and costs

### 2. Use Application Insights for Production
- Monitor real-world performance
- Set up alerts for errors and slow requests
- Track business metrics (chat volume, user engagement)

### 3. Custom Metrics
Add metrics for your business needs:

```python
from observability import get_metrics

metrics = get_metrics()
metrics.record_chat_request()  # Custom business event
metrics.record_rag_latency(150.5)  # RAG took 150.5ms
metrics.record_document_upload()  # Document was uploaded
```

### 4. Production Deployment
For Docker Compose:
```yaml
environment:
  - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
  - APPLICATIONINSIGHTS_CONNECTION_STRING=${APPLICATIONINSIGHTS_CONNECTION_STRING}
```

## Further Reading

- [LangSmith Docs](https://docs.smith.langchain.com)
- [Azure Application Insights Docs](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
- [OpenTelemetry Docs](https://opentelemetry.io)
- [FastAPI Logging](https://fastapi.tiangolo.com/advanced/middleware/)
