# 🏢 Insurance AI Platform

An AI-powered insurance application for internal use providing claims processing, policy analysis, document extraction, and customer support automation.

## ✨ Features

- **Claims Processing**: AI-powered claim analysis and recommendations
- **Policy Analysis**: Automated policy coverage and risk assessment
- **Document Extraction**: OCR and data extraction from insurance documents
- **Chat Support**: Conversational AI for customer inquiries
- **Analytics Dashboard**: Real-time metrics and performance insights
- **Streamlit Frontend**: User-friendly web interface
- **FastAPI Backend**: High-performance REST API

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ or Docker
- pip/conda for dependency management

### Option 1: Local Python Installation

1. **Clone/Create Project**
```bash
cd insurance-ai-app
```

2. **Create Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Run Backend (Terminal 1)**
```bash
python main.py
```
Backend will be available at: `http://localhost:8000`

5. **Run Frontend (Terminal 2)**
```bash
streamlit run app.py
```
Frontend will be available at: `http://localhost:8501`

### Option 2: Docker Compose (Recommended)

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📋 API Documentation

Once the API is running, visit: `http://localhost:8000/docs`

### Key Endpoints

#### Claims Processing
```bash
POST /api/claims/process          # Process a claim
GET  /api/claims/{claim_id}       # Get claim status
```

#### Policy Analysis
```bash
POST /api/policies/analyze        # Analyze policy
```

#### Document Processing
```bash
POST /api/documents/process       # Extract from document
```

#### Chat
```bash
POST /api/chat                    # Send chat message
```

#### Analytics
```bash
GET  /api/analytics/dashboard     # Get dashboard metrics
GET  /api/analytics/claims-trend  # Get claims trends
```

#### Health Check
```bash
GET  /api/health                  # API health status
```

## 📊 Dashboard Features

### Claims Processing
- Create and track insurance claims
- AI-powered recommendations
- Confidence score evaluation
- Processing status monitoring

### Policy Analysis
- Coverage gap identification
- Risk assessment
- Compliance verification
- Optimization recommendations

### Document Processing
- Upload and process documents
- Automatic field extraction
- OCR for scanned documents
- Confidence scoring

### Chat Support
- Conversational AI interface
- Insurance-related Q&A
- Suggested actions
- Conversation history

### Analytics
- Claims metrics dashboard
- Performance trends
- Claims distribution analysis
- Efficiency metrics

## 🔧 Configuration

Edit `.env` file to configure:

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Azure Services (optional)
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_STORAGE_ACCOUNT_NAME=
AZURE_COSMOS_ENDPOINT=
```

## 📁 Project Structure

```
insurance-ai-app/
├── main.py                 # FastAPI backend application
├── app.py                  # Streamlit frontend dashboard
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker Compose configuration
├── .env                   # Environment configuration
├── .azure/
│   └── deployment-plan.md # Azure deployment plan
└── README.md             # This file
```

## 🧪 Testing the Application

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Process a claim
curl -X POST http://localhost:8000/api/claims/process \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-2024-001",
    "customer_name": "John Doe",
    "claim_type": "auto",
    "description": "Vehicle accident",
    "amount_claimed": 5000,
    "incident_date": "2024-01-15"
  }'

# Analyze policy
curl -X POST http://localhost:8000/api/policies/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "POL-2024-001",
    "customer_id": "CUST-001",
    "analysis_type": "coverage"
  }'

# Get analytics
curl http://localhost:8000/api/analytics/dashboard
```

## 🚀 Deployment to Azure

### Using azure-prepare skill:

1. **Prepare for Azure**
```bash
# azure-prepare will generate:
# - azure.yaml
# - Bicep or Terraform files
# - Container configuration
```

2. **Validate Deployment**
```bash
azd validate
```

3. **Deploy to Azure**
```bash
azd up
```

## 📚 Technology Stack

### Backend
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Async**: AsyncIO
- **Documentation**: Swagger/OpenAPI

### Frontend
- **Framework**: Streamlit
- **Visualization**: Plotly
- **Data**: Pandas
- **HTTP**: Requests

### Integration
- **AI**: Azure OpenAI, LangChain
- **Storage**: Azure Blob Storage
- **Database**: Azure Cosmos DB
- **Documents**: Azure Document Intelligence
- **Identity**: Azure Managed Identity

## 🔐 Security Features

- CORS middleware configuration
- Request validation with Pydantic
- Environment variable management
- Error handling and logging
- API health checks

## 📈 Monitoring & Logging

- Structured logging throughout application
- Health check endpoint for monitoring
- Background task logging
- Error tracking and reporting

## 🤝 Development Workflow

1. **Local Development**
   - Run backend and frontend locally
   - Make code changes
   - Test via Streamlit dashboard

2. **Docker Testing**
   - Test in containers with docker-compose
   - Verify multi-service interaction
   - Test environment variable handling

3. **Azure Deployment**
   - Use azure-prepare for infrastructure setup
   - Run azure-validate for preflight checks
   - Deploy with azure-deploy

## 📝 Environment Variables

See `.env` file for all available configuration options.

## 🐛 Troubleshooting

### Backend won't start
- Check if port 8000 is available
- Verify Python version is 3.11+
- Check dependencies: `pip install -r requirements.txt`

### Frontend won't load
- Ensure backend is running
- Check if port 8501 is available
- Verify Streamlit installation

### Docker issues
- Rebuild: `docker-compose build --no-cache`
- Check logs: `docker-compose logs -f`
- Ensure ports 8000 and 8501 are free

## 📞 Support

For issues or questions:
1. Check logs in terminal output
2. Review API documentation at `/docs`
3. Check `.env` configuration
4. Test endpoints with cURL

## 📄 License

Internal Use Only

## 🔄 Version History

- **v1.0.0** - Initial release with core features

---

**Last Updated**: April 9, 2026
