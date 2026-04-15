"""
Insurance AI Application - Main FastAPI Backend
Handles claims processing, policy analysis, and customer support
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime
import logging
import json
import io
import csv
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

# Import RAG system
from rag import get_rag_system, init_rag_system

# Import conversation memory
from memory import init_memory, get_memory

# Import observability
from observability import (
    init_observability,
    get_observability_status,
    trace_rag_chain,
    trace_llm_call,
    trace_operation,
    get_metrics,
    log_langsmith_event
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize RAG system with FREE Groq LLM (no license required)
# Get free API key from: https://console.groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
init_rag_system(groq_api_key=GROQ_API_KEY)

# Initialize FastAPI app
app = FastAPI(
    title="Insurance AI API",
    description="AI-powered insurance processing system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize memory and RAG on startup
@app.on_event("startup")
async def startup_event():
    """Initialize memory, RAG, and observability systems on startup"""
    logger.info("🚀 Starting Insurance AI Application...")
    
    # Initialize observability (LangSmith + Azure App Insights)
    obs_config = init_observability()
    logger.info(f"📊 Observability initialized: {obs_config}")
    
    # Initialize memory system (Redis or in-memory fallback)
    init_memory()
    logger.info("✅ Memory system initialized")
    
    # Initialize RAG system
    logger.info("✅ All systems ready!")

# ==================== Data Models ====================

class ClaimRequest(BaseModel):
    """Request model for insurance claim processing"""
    claim_id: str
    customer_name: str
    claim_type: str  # auto, health, property, etc.
    description: str
    amount_claimed: float
    incident_date: str

class PolicyAnalysis(BaseModel):
    """Request model for policy analysis"""
    policy_id: str
    customer_id: str
    analysis_type: str  # coverage, risk, compliance, etc.

class DocumentProcessing(BaseModel):
    """Request model for document processing"""
    document_type: str  # claim_form, policy, receipt, etc.
    document_id: str

class ClaimResponse(BaseModel):
    """Response model for claim processing"""
    claim_id: str
    status: str
    confidence_score: float
    recommendation: str
    processing_time: float
    ai_notes: str

class ChatMessage(BaseModel):
    """Chat message for conversational AI"""
    message: str
    conversation_id: Optional[str] = None
    context: Optional[str] = None

# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint with observability status"""
    memory = get_memory()
    obs_status = get_observability_status()
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "memory": memory.health_check() if memory else {"status": "unavailable"},
        **obs_status
    }

# ==================== Claims Processing ====================

@app.post("/api/claims/process", response_model=ClaimResponse)
async def process_claim(claim_request: ClaimRequest, background_tasks: BackgroundTasks):
    """
    Process insurance claim using AI
    Analyzes claim details and provides recommendations
    """
    try:
        logger.info(f"Processing claim: {claim_request.claim_id}")
        
        # Simulate AI processing
        # In production, this would call Azure OpenAI
        recommendation = f"Claim {claim_request.claim_id} requires verification. Initial assessment: UNDER REVIEW"
        confidence = 0.85
        
        response = ClaimResponse(
            claim_id=claim_request.claim_id,
            status="PROCESSING",
            confidence_score=confidence,
            recommendation=recommendation,
            processing_time=2.5,
            ai_notes=f"Processed {claim_request.claim_type} claim for ${claim_request.amount_claimed}"
        )
        
        # Schedule background processing
        background_tasks.add_task(log_claim_processing, claim_request.claim_id)
        
        return response
    except Exception as e:
        logger.error(f"Error processing claim: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/claims/{claim_id}")
async def get_claim_status(claim_id: str):
    """Get status of a specific claim"""
    return {
        "claim_id": claim_id,
        "status": "APPROVED",
        "last_updated": datetime.now().isoformat(),
        "confidence_score": 0.92
    }

# ==================== Policy Analysis ====================

@app.post("/api/policies/analyze")
async def analyze_policy(policy_analysis: PolicyAnalysis):
    """
    Analyze insurance policy using AI
    Identifies coverage gaps and risks
    """
    try:
        logger.info(f"Analyzing policy: {policy_analysis.policy_id}")
        
        analysis = {
            "policy_id": policy_analysis.policy_id,
            "analysis_type": policy_analysis.analysis_type,
            "findings": [
                "Policy covers comprehensive liability",
                "Gap identified in cybersecurity coverage",
                "Recommended coverage: Enhanced property protection"
            ],
            "risk_score": 0.65,
            "recommendations": 3,
            "timestamp": datetime.now().isoformat()
        }
        
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing policy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Document Processing ====================

@app.post("/api/documents/process")
async def process_document(file: UploadFile = File(...), document_type: str = ""):
    """
    Process insurance document using AI
    Extracts data and performs OCR
    """
    try:
        logger.info(f"Processing document: {file.filename}, Type: {document_type}")
        
        # In production, this would use Azure Document Intelligence
        extraction = {
            "document_id": file.filename,
            "document_type": document_type,
            "extracted_fields": {
                "policyholder_name": "John Doe",
                "policy_number": "POL-2024-12345",
                "coverage_amount": 500000,
                "effective_date": "2024-01-15"
            },
            "confidence_score": 0.88,
            "extraction_status": "SUCCESS",
            "timestamp": datetime.now().isoformat()
        }
        
        return extraction
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Chat/Conversational AI ====================

@app.post("/api/rag/query")
async def rag_query(query_data: dict):
    """
    Query with RAG - Retrieve documents and generate answer using Groq LLM
    """
    try:
        query = query_data.get("query", "")
        top_k = query_data.get("top_k", 3)
        record_id = query_data.get("record_id", "")
        
        if not query:
            raise ValueError("Query is required")
        
        logger.info(f"RAG Query: {query}")
        
        # Get RAG system
        rag_system = get_rag_system()
        
        if not rag_system or not rag_system.llm or not rag_system.retriever:
            return {
                "status": "error",
                "answer": "RAG system not properly initialized. Please ensure Groq API key is set.",
                "sources": [],
                "error": "RAG system not initialized"
            }
        
        # Retrieve and answer using RAG
        result = rag_system.retrieve_and_answer(query)
        
        if result.get("status") == "mock" or result.get("status") == "error":
            # If falling back to mock, try to provide better context
            return {
                "status": "success",
                "answer": result.get("answer", "I don't have information to answer this question. Please upload a document first."),
                "sources": result.get("sources", []),
                "warning": "Using limited retrieval mode"
            }
        
        return {
            "status": "success",
            "answer": result.get("answer", "No answer generated"),
            "sources": result.get("sources", []),
            "record_id": record_id
        }
    except Exception as e:
        logger.error(f"Error in RAG query: {str(e)}")
        return {
            "status": "error",
            "answer": f"Error processing query: {str(e)}",
            "sources": [],
            "error": str(e)
        }

@app.post("/api/rag/search")
async def rag_search(search_data: dict):
    """
    Search documents using vector similarity
    """
    try:
        query = search_data.get("query", "")
        top_k = search_data.get("top_k", 5)
        
        if not query:
            raise ValueError("Query is required")
        
        logger.info(f"Document Search: {query}")
        
        rag_system = get_rag_system()
        
        if not rag_system or not rag_system.vector_store:
            return {
                "status": "error",
                "results": [],
                "message": "No documents uploaded yet"
            }
        
        results = rag_system.search_documents(query, top_k)
        
        return {
            "status": "success",
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error in document search: {str(e)}")
        return {
            "status": "error",
            "results": [],
            "error": str(e)
        }

@app.post("/api/chat")
async def chat_with_ai(message: ChatMessage):
    """
    Chat with RAG-powered AI - Uses FREE Groq LLM
    Maintains conversation history in Redis for context-aware responses
    Includes LangSmith tracing and observability
    """
    try:
        # Track request in metrics
        get_metrics().record_chat_request()
        
        # Trace operation
        with trace_operation("chat_request", {"message_length": len(message.message)}):
            logger.info(f"Chat message: {message.message}")
            
            # Get memory and RAG systems
            memory = get_memory()
            rag_system = get_rag_system()
            
            # Generate conversation ID if not provided
            if not message.conversation_id:
                message.conversation_id = f"conv-{datetime.now().isoformat()}"
            
            if not rag_system or not rag_system.llm:
                # Fallback if RAG not initialized
                response = {
                    "conversation_id": message.conversation_id,
                    "user_message": message.message,
                    "ai_response": "RAG system not initialized. Please ensure Groq API key is configured.",
                    "confidence": 0.0,
                    "timestamp": datetime.now().isoformat()
                }
                # Still save to memory
                memory.save_message(message.conversation_id, "user", message.message)
                log_langsmith_event(
                    "chat_failed_no_rag",
                    inputs={"message": message.message},
                    metadata={"conversation_id": message.conversation_id}
                )
                return response
            
            # Save user message to memory
            memory.save_message(message.conversation_id, "user", message.message)
            
            # Get recent conversation context
            context = memory.get_recent_context(message.conversation_id, max_messages=4)
            
            # Build prompt with conversation history
            if context:
                full_query = f"Recent conversation:\n{context}\n\nNew question: {message.message}"
            else:
                full_query = message.message
            
            # Use RAG to answer the question
            result = rag_system.retrieve_and_answer(full_query)
            ai_response = result.get("answer", "Unable to generate response")
            
            # Save AI response to memory
            memory.save_message(message.conversation_id, "assistant", ai_response, {
                "sources": result.get("sources", [])
            })
            
            response = {
                "conversation_id": message.conversation_id,
                "user_message": message.message,
                "ai_response": ai_response,
                "sources": result.get("sources", []),
                "confidence": 0.85,
                "timestamp": datetime.now().isoformat(),
                "context_from_history": bool(context)
            }
            
            # Log to LangSmith
            log_langsmith_event(
                "chat_completed",
                inputs={"message": message.message},
                outputs={"response": ai_response[:200]},
                metadata={"conversation_id": message.conversation_id, "has_context": bool(context)}
            )
            
            return response
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        log_langsmith_event(
            "chat_error",
            inputs={"message": message.message},
            outputs={"error": str(e)},
            metadata={"exception": type(e).__name__}
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat-with-record")
async def chat_with_record(message: ChatMessage):
    """
    Chat with a specific record context - Uses FREE Groq LLM
    Maintains conversation history in Redis
    """
    try:
        logger.info(f"Chat with record: {message.message}")
        
        # Get memory and RAG systems
        memory = get_memory()
        rag_system = get_rag_system()
        
        if not message.conversation_id:
            message.conversation_id = f"conv-{datetime.now().isoformat()}"
        
        if not rag_system or not rag_system.llm:
            memory.save_message(message.conversation_id, "user", message.message)
            return {
                "conversation_id": message.conversation_id,
                "user_message": message.message,
                "ai_response": "RAG system not initialized",
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Save user message to memory
        memory.save_message(message.conversation_id, "user", message.message)
        
        # Get conversation context
        context = memory.get_recent_context(message.conversation_id, max_messages=4)
        
        # Build query with context
        full_query = f"Additional context: {message.context}\n\n" if message.context else ""
        if context:
            full_query += f"Recent conversation:\n{context}\n\nNew question: {message.message}"
        else:
            full_query += message.message
        
        # Retrieve and answer
        # Retrieve and answer
        result = rag_system.retrieve_and_answer(full_query)
        ai_response = result.get("answer", "Unable to generate response")
        
        # Save to memory
        memory.save_message(message.conversation_id, "assistant", ai_response, {
            "sources": result.get("sources", [])
        })
        
        return {
            "conversation_id": message.conversation_id,
            "user_message": message.message,
            "ai_response": ai_response,
            "sources": result.get("sources", []),
            "record_used": message.context,
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat(),
            "context_from_history": bool(context)
        }
    except Exception as e:
        logger.error(f"Error in chat-with-record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Conversation Memory Management ====================

@app.get("/api/memory/health")
async def memory_health_check():
    """Check memory system health"""
    memory = get_memory()
    health = memory.health_check()
    return {
        "status": "ok",
        "memory": health,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str, limit: int = 20):
    """Get full conversation history for a conversation ID"""
    memory = get_memory()
    messages = memory.get_conversation(conversation_id, max_messages=limit)
    summary = memory.get_conversation_summary(conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/conversations/{conversation_id}/summary")
async def get_conversation_summary(conversation_id: str):
    """Get metadata summary of a conversation"""
    memory = get_memory()
    summary = memory.get_conversation_summary(conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    }

@app.delete("/api/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    memory = get_memory()
    success = memory.clear_conversation(conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "cleared": success,
        "timestamp": datetime.now().isoformat()
    }

# ==================== Analytics ====================

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Get analytics dashboard data"""
    return {
        "total_claims": 1250,
        "claims_processed_today": 45,
        "average_processing_time": 2.5,
        "ai_accuracy_rate": 0.88,
        "average_resolution_time_hours": 24,
        "customer_satisfaction": 0.92,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/analytics/claims-trend")
async def get_claims_trend():
    """Get claims processing trends"""
    return {
        "period": "last_30_days",
        "total_claims": 1250,
        "approved": 950,
        "rejected": 125,
        "pending": 175,
        "average_claim_value": 8500,
        "approval_rate": 0.76
    }

# ==================== Background Tasks ====================

async def log_claim_processing(claim_id: str):
    """Log claim processing completion"""
    logger.info(f"Claim {claim_id} processing logged to database")

# ==================== Records Storage ====================

# In-memory storage for records (in production, use database)
records_storage = {}

class RecordUpload(BaseModel):
    """Request model for uploading records"""
    record_id: str
    record_type: str  # claim, policy, customer, document
    record_name: str
    record_data: dict

@app.post("/api/records/upload")
async def upload_record(record: RecordUpload):
    """
    Upload and store a record for later use in chat
    """
    try:
        logger.info(f"Uploading record: {record.record_id}")
        
        records_storage[record.record_id] = {
            "id": record.record_id,
            "type": record.record_type,
            "name": record.record_name,
            "data": record.record_data,
            "uploaded_at": datetime.now().isoformat()
        }
        
        return {
            "status": "SUCCESS",
            "record_id": record.record_id,
            "message": f"Record {record.record_name} uploaded successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error uploading record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/records")
async def list_records():
    """Get list of all uploaded records"""
    return {
        "records": list(records_storage.values()),
        "total": len(records_storage),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/records/{record_id}")
async def get_record(record_id: str):
    """Get a specific record"""
    if record_id not in records_storage:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found")
    
    return {
        "record": records_storage[record_id],
        "timestamp": datetime.now().isoformat()
    }

@app.delete("/api/records/{record_id}")
async def delete_record(record_id: str):
    """Delete a record"""
    if record_id in records_storage:
        deleted = records_storage.pop(record_id)
        return {
            "status": "SUCCESS",
            "message": f"Record {record_id} deleted",
            "deleted_record": deleted,
            "timestamp": datetime.now().isoformat()
        }
    raise HTTPException(status_code=404, detail=f"Record {record_id} not found")

# ==================== File Upload with Parsing ====================

def parse_file_content(file_content: bytes, filename: str) -> dict:
    """
    Parse different file types and extract data
    Returns dict with file_type and parsed_data
    """
    file_ext = Path(filename).suffix.lower()
    
    try:
        # Text file
        if file_ext in ['.txt']:
            text_content = file_content.decode('utf-8', errors='ignore')
            return {
                "file_type": "text",
                "content": text_content,
                "line_count": len(text_content.split('\n'))
            }
        
        # CSV file
        elif file_ext == '.csv':
            text_content = file_content.decode('utf-8', errors='ignore')
            csv_reader = csv.DictReader(io.StringIO(text_content))
            rows = list(csv_reader)
            return {
                "file_type": "csv",
                "columns": csv_reader.fieldnames if csv_reader.fieldnames else [],
                "row_count": len(rows),
                "rows": rows[:100]  # First 100 rows
            }
        
        # PDF file
        elif file_ext == '.pdf':
            if PdfReader is None:
                return {
                    "file_type": "pdf",
                    "error": "PDF library not available",
                    "raw_size": len(file_content)
                }
            
            pdf_reader = PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            return {
                "file_type": "pdf",
                "page_count": len(pdf_reader.pages),
                "content": text[:1000],  # First 1000 chars
                "full_content_length": len(text)
            }
        
        # SQL file
        elif file_ext == '.sql':
            sql_content = file_content.decode('utf-8', errors='ignore')
            return {
                "file_type": "sql",
                "content": sql_content,
                "statement_count": sql_content.count(';')
            }
        
        # JSON file
        elif file_ext == '.json':
            json_content = file_content.decode('utf-8', errors='ignore')
            data = json.loads(json_content)
            return {
                "file_type": "json",
                "data": data,
                "keys": list(data.keys()) if isinstance(data, dict) else None
            }
        
        # Generic binary file
        else:
            return {
                "file_type": "unknown",
                "filename": filename,
                "size_bytes": len(file_content),
                "content_preview": f"Binary file ({len(file_content)} bytes)"
            }
    
    except Exception as e:
        return {
            "file_type": file_ext,
            "error": str(e),
            "filename": filename
        }

@app.post("/api/records/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file and automatically parse it as a record
    Supports: PDF, CSV, TXT, SQL, JSON, and other file types
    """
    try:
        logger.info(f"Uploading file: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Parse file
        parsed_data = parse_file_content(content, file.filename)
        
        # Generate record ID from filename
        file_stem = Path(file.filename).stem
        record_id = f"FILE-{file_stem}-{int(datetime.now().timestamp())}"
        
        # Determine record type from file extension
        file_ext = Path(file.filename).suffix.lower().strip('.')
        record_type_map = {
            'pdf': 'document',
            'csv': 'dataset',
            'txt': 'document',
            'sql': 'database',
            'json': 'data',
            'doc': 'document',
            'docx': 'document'
        }
        record_type = record_type_map.get(file_ext, 'file')
        
        # Store in records storage
        records_storage[record_id] = {
            "id": record_id,
            "type": record_type,
            "name": file.filename,
            "file_type": parsed_data.get("file_type"),
            "data": parsed_data,
            "uploaded_at": datetime.now().isoformat(),
            "file_size_bytes": len(content)
        }
        
        # Add to RAG system with document content
        try:
            rag_system = get_rag_system()
            # Extract text content from parsed data for RAG
            if "content" in parsed_data:
                doc_content = parsed_data["content"]
            elif "rows" in parsed_data:
                doc_content = json.dumps(parsed_data["rows"], indent=2)
            elif "data" in parsed_data:
                doc_content = json.dumps(parsed_data["data"], indent=2)
            else:
                doc_content = str(parsed_data)
            
            rag_system.add_document(
                doc_id=record_id,
                content=doc_content,
                metadata={
                    "filename": file.filename,
                    "file_type": parsed_data.get("file_type"),
                    "record_type": record_type,
                    "uploaded_at": datetime.now().isoformat()
                }
            )
            logger.info(f"Document added to RAG system: {record_id}")
        except Exception as e:
            logger.warning(f"RAG integration warning: {str(e)}")
        
        return {
            "status": "SUCCESS",
            "record_id": record_id,
            "filename": file.filename,
            "file_type": parsed_data.get("file_type"),
            "message": f"File {file.filename} uploaded and parsed successfully",
            "summary": {
                "type": record_type,
                "size_bytes": len(content),
                "parsed_info": {k: v for k, v in parsed_data.items() if k not in ['content', 'rows', 'data']}
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

# ==================== Enhanced Chat with Record Context ====================

class ChatMessageWithRecord(BaseModel):
    """Chat message with record context"""
    message: str
    record_id: Optional[str] = None  # Reference to an uploaded record
    conversation_id: Optional[str] = None
    context: Optional[str] = None

@app.post("/api/chat-with-record")
async def chat_with_record_context(chat: ChatMessageWithRecord):
    """
    Conversational AI with uploaded record context
    """
    try:
        logger.info(f"Chat message with record context: {chat.message}")
        
        # Get record data if provided
        record_context = None
        if chat.record_id and chat.record_id in records_storage:
            record_data = records_storage[chat.record_id]
            record_context = f"\nRECORD CONTEXT:\nType: {record_data['type']}\nName: {record_data['name']}\nData: {record_data['data']}"
        
        # Build system message
        system_message = "You are an insurance support assistant."
        if record_context:
            system_message += record_context
        
        # In production, this would call Azure OpenAI
        response = {
            "conversation_id": chat.conversation_id or "conv-" + datetime.now().isoformat(),
            "user_message": chat.message,
            "record_used": chat.record_id if chat.record_id in records_storage else None,
            "ai_response": f"Based on the uploaded record, I can help you with your inquiry about {records_storage.get(chat.record_id, {}).get('name', 'your request')}. How can I assist you further?",
            "confidence": 0.92,
            "record_summary": records_storage.get(chat.record_id) if chat.record_id and chat.record_id in records_storage else None,
            "suggested_actions": [
                "View full record details",
                "Generate report",
                "Ask follow-up question",
                "Download record"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return response
    except Exception as e:
        logger.error(f"Error in chat with record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== RAG Query Endpoints ====================

class RAGQuery(BaseModel):
    """RAG query request"""
    query: str
    record_id: Optional[str] = None
    top_k: Optional[int] = 3

@app.post("/api/rag/query")
async def rag_query(rag_query: RAGQuery):
    """
    Query uploaded documents using RAG system
    Uses vector similarity search and retrieval-augmented generation
    """
    try:
        logger.info(f"RAG Query: {rag_query.query}")
        
        rag_system = get_rag_system()
        result = rag_system.retrieve_and_answer(rag_query.query)
        
        return {
            "status": "success",
            "query": rag_query.query,
            "answer": result.get("answer"),
            "sources": result.get("sources", []),
            "source_count": len(result.get("sources", [])),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"RAG query error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG query error: {str(e)}")

@app.post("/api/rag/search")
async def rag_search(rag_query: RAGQuery):
    """
    Search documents by semantic similarity
    """
    try:
        logger.info(f"RAG Search: {rag_query.query}")
        
        rag_system = get_rag_system()
        results = rag_system.search_documents(rag_query.query, top_k=rag_query.top_k or 3)
        
        return {
            "status": "success",
            "query": rag_query.query,
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"RAG search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG search error: {str(e)}")

@app.get("/api/rag/document/{record_id}")
async def get_document_for_rag(record_id: str):
    """
    Get document summary and content from RAG system
    """
    try:
        rag_system = get_rag_system()
        summary = rag_system.get_document_summary(record_id)
        
        # Also get original record data if available
        record_data = records_storage.get(record_id) if record_id in records_storage else None
        
        return {
            "status": "success",
            "record_id": record_id,
            "summary": summary,
            "record_data": record_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Document retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document retrieval error: {str(e)}")

# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP Exception: {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
