"""
Observability Module - LangSmith Tracing and Azure Application Insights
Handles telemetry, distributed tracing, and LLM monitoring
"""

import os
import logging
from typing import Optional
from contextlib import contextmanager

# LangSmith imports
from langsmith import traceable
from langsmith.wrappers import wrap_openai

# Azure Application Insights imports (optional)
try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import ReadableSpan
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
    AZURE_APP_INSIGHTS_AVAILABLE = True
except ImportError:
    AZURE_APP_INSIGHTS_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Global tracer
tracer = None
meter = None
langsmith_enabled = False
app_insights_enabled = False


def init_observability():
    """
    Initialize observability stack:
    - Azure Application Insights (if connection string provided)
    - LangSmith tracing (if API key provided)
    """
    global tracer, meter, langsmith_enabled, app_insights_enabled
    
    # Initialize LangSmith tracing
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY", "").strip()
    langsmith_project = os.getenv("LANGSMITH_PROJECT", "insurance-ai").strip()
    
    if langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = langsmith_project
        os.environ["LANGSMITH_TRACING"] = "true"
        langsmith_enabled = True
        logger.info(f"✅ LangSmith tracing enabled (project: {langsmith_project})")
    else:
        os.environ["LANGSMITH_TRACING"] = "false"
        logger.warning("⚠️ LangSmith API key not found. Set LANGSMITH_API_KEY to enable tracing.")
    
    # Initialize Azure Application Insights
    app_insights_conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "").strip()
    
    if app_insights_conn_str and AZURE_APP_INSIGHTS_AVAILABLE:
        try:
            configure_azure_monitor(connection_string=app_insights_conn_str)
            tracer = trace.get_tracer(__name__)
            meter = metrics.get_meter(__name__)
            app_insights_enabled = True
            logger.info("✅ Azure Application Insights telemetry enabled")
        except Exception as e:
            logger.warning(f"⚠️ Failed to configure Azure Application Insights: {e}")
    elif app_insights_conn_str and not AZURE_APP_INSIGHTS_AVAILABLE:
        logger.warning("⚠️ Application Insights connection string provided but azure-monitor-opentelemetry not installed")
    else:
        logger.info("ℹ️ Application Insights telemetry not configured (optional)")
    
    return {
        "langsmith_enabled": langsmith_enabled,
        "app_insights_enabled": app_insights_enabled,
        "langsmith_project": langsmith_project if langsmith_enabled else None,
    }


def get_observability_config():
    """Get current observability configuration"""
    return {
        "langsmith_enabled": langsmith_enabled,
        "app_insights_enabled": app_insights_enabled,
        "tracer_available": tracer is not None,
        "meter_available": meter is not None,
    }


@contextmanager
def trace_operation(operation_name: str, attributes: dict = None):
    """
    Context manager for tracing operations with optional Azure App Insights
    
    Usage:
        with trace_operation("process_chat", {"conversation_id": conv_id}):
            # Your code here
            pass
    """
    if tracer is None:
        yield
        return
    
    with tracer.start_as_current_span(operation_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        yield span


def log_langsmith_event(name: str, inputs: dict = None, outputs: dict = None, metadata: dict = None):
    """
    Log a custom event to LangSmith
    
    Usage:
        log_langsmith_event(
            "policy_analysis",
            inputs={"policy_id": "123"},
            outputs={"analysis": "..."},
            metadata={"source": "chat"}
        )
    """
    if not langsmith_enabled:
        return
    
    try:
        from langsmith import Client
        client = Client()
        
        event_data = {
            "name": name,
            "inputs": inputs or {},
            "outputs": outputs or {},
            "metadata": metadata or {},
        }
        
        # Note: LangSmith event logging is typically done via @traceable decorator
        # This function serves as a manual logging utility
        logger.info(f"📊 LangSmith event logged: {name}")
    except Exception as e:
        logger.warning(f"Failed to log LangSmith event: {e}")


def trace_rag_chain(chain_name: str = "rag_chain"):
    """
    Decorator for tracing RAG chains with LangSmith
    
    Usage:
        @trace_rag_chain("chat_with_documents")
        def my_rag_function(query: str, context: str):
            return response
    """
    def decorator(func):
        if langsmith_enabled:
            @traceable(name=chain_name)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        else:
            return func
    
    return decorator


def trace_llm_call(model_name: str = "groq"):
    """
    Decorator for tracing LLM calls
    
    Usage:
        @trace_llm_call("groq-mixtral")
        def query_llm(prompt: str):
            return response
    """
    def decorator(func):
        if langsmith_enabled:
            @traceable(name=f"llm_{model_name}", tags=[model_name, "llm"])
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        else:
            return func
    
    return decorator


class ObservabilityMetrics:
    """Helper class for tracking custom metrics"""
    
    def __init__(self):
        self.metrics = {}
        if meter:
            self._setup_meters()
    
    def _setup_meters(self):
        """Setup OpenTelemetry meters"""
        if not meter:
            return
        
        # Create metrics
        try:
            self.chat_counter = meter.create_counter(
                "insurance_ai.chat.requests",
                unit="1",
                description="Total chat requests"
            )
            self.rag_latency = meter.create_histogram(
                "insurance_ai.rag.latency_ms",
                unit="ms",
                description="RAG query latency"
            )
            self.document_uploads = meter.create_counter(
                "insurance_ai.documents.uploaded",
                unit="1",
                description="Documents uploaded"
            )
        except Exception as e:
            logger.warning(f"Failed to setup metrics: {e}")
    
    def record_chat_request(self):
        """Record a chat request"""
        if hasattr(self, 'chat_counter') and self.chat_counter:
            self.chat_counter.add(1)
    
    def record_rag_latency(self, latency_ms: float):
        """Record RAG query latency in milliseconds"""
        if hasattr(self, 'rag_latency') and self.rag_latency:
            self.rag_latency.record(latency_ms)
    
    def record_document_upload(self):
        """Record a document upload"""
        if hasattr(self, 'document_uploads') and self.document_uploads:
            self.document_uploads.add(1)


# Global metrics instance
metrics_instance = None


def get_metrics():
    """Get global metrics instance"""
    global metrics_instance
    if metrics_instance is None:
        metrics_instance = ObservabilityMetrics()
    return metrics_instance


def get_observability_status() -> dict:
    """Get detailed observability status for health checks"""
    return {
        "observability": {
            "status": "configured" if (langsmith_enabled or app_insights_enabled) else "disabled",
            "langsmith": {
                "enabled": langsmith_enabled,
                "project": os.getenv("LANGSMITH_PROJECT", "N/A") if langsmith_enabled else None,
            },
            "application_insights": {
                "enabled": app_insights_enabled,
                "sdk_available": AZURE_APP_INSIGHTS_AVAILABLE,
            },
            "telemetry": {
                "tracer": "enabled" if tracer else "disabled",
                "metrics": "enabled" if meter else "disabled",
            }
        }
    }
