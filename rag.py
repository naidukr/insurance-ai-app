"""
RAG (Retrieval Augmented Generation) Module
Handles document storage, vector embeddings, and LLM-powered retrieval
Free LLM model: Groq (no license required) - https://console.groq.com
Free Embeddings: HuggingFace (offline, no API key needed)
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import logging
from datetime import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from langsmith.client import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Langsmith client for tracing (optional)
os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("LANGSMITH_PROJECT", "insurance-ai-app")

class RAGVectorStore:
    """Vector store and RAG system with FREE Groq LLM"""
    
    def __init__(self, groq_api_key: str = None):
        """
        Initialize RAG system with FREE Groq LLM
        
        Args:
            groq_api_key: Groq API key (free from groq.com)
        """
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.vector_store = None
        self.embeddings = None
        self.llm = None
        self.retriever = None
        self.documents: Dict[str, Any] = {}
        
        # Initialize embeddings - using HuggingFace (free, no API key needed)
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            logger.info("HuggingFace embeddings initialized (free, offline)")
        except Exception as e:
            logger.warning(f"HuggingFace embeddings failed: {e}. Using mock mode.")
            self.embeddings = None
        
        # Initialize Groq LLM (FREE model)
        if self.groq_api_key:
            try:
                self.llm = ChatGroq(
                    temperature=0.7,
                    groq_api_key=self.groq_api_key,
                    model_name="mixtral-8x7b-32768",  # Free Groq model
                    max_tokens=1024
                )
                logger.info("✅ Groq LLM initialized successfully (FREE)")
            except Exception as e:
                logger.warning(f"Groq initialization failed: {e}. Using mock mode.")
                logger.info("Get free Groq API key: https://console.groq.com")
                self.llm = None
        else:
            logger.warning("⚠️  No Groq API key provided. Get free key from: https://console.groq.com")
            self.llm = None
    
    @traceable(name="add_document_to_rag", tags=["rag", "document"])
    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Add a document to the vector store
        
        Args:
            doc_id: Unique document identifier
            content: Document content
            metadata: Additional metadata (filename, type, etc.)
        
        Returns:
            bool: Success status
        """
        try:
            if not content or not content.strip():
                logger.error(f"Empty content for document {doc_id}")
                return False
            
            logger.info(f"Adding document to RAG: {doc_id}")
            
            # Store document
            self.documents[doc_id] = {
                "content": content,
                "metadata": metadata or {},
                "added_at": str(datetime.now().isoformat())
            }
            
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )
            chunks = text_splitter.split_text(content)
            
            # Create documents with metadata
            docs = [
                Document(
                    page_content=chunk,
                    metadata={
                        "doc_id": doc_id,
                        "source": metadata.get("filename", "unknown") if metadata else "unknown",
                        "chunk_index": i,
                        **(metadata or {})
                    }
                )
                for i, chunk in enumerate(chunks)
            ]
            
            # Update vector store
            if self.embeddings and self.vector_store is None:
                self.vector_store = FAISS.from_documents(docs, self.embeddings)
                self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                self._create_qa_chain()
                logger.info(f"Created new vector store with {len(docs)} chunks")
            elif self.embeddings and self.vector_store is not None:
                self.vector_store.add_documents(docs)
                logger.info(f"Added {len(docs)} chunks to existing vector store")
            
            return True
        
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            return False
    
    def _create_qa_chain(self):
        """Create QA chain for RAG - simplified without RetrievalQA"""
        # We'll handle retrieval and generation in retrieve_and_answer method
        logger.info("QA chain preparation complete")
        return True
    
    @traceable(name="retrieve_and_generate", tags=["rag", "query"])
    def retrieve_and_answer(self, query: str) -> Dict[str, Any]:
        """
        Retrieve documents and generate answer using RAG
        
        Args:
            query: User question
        
        Returns:
            dict: Answer and source documents
        """
        try:
            if self.retriever is None or self.llm is None:
                # Fallback to mock response if no OpenAI API key
                return self._mock_retrieve(query)
            
            logger.info(f"Processing query: {query}")
            
            # Retrieve similar documents
            retrieved_docs = self.retriever.invoke(query)
            
            # Prepare context from retrieved documents
            context = "\n\n".join([f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}" 
                                   for doc in retrieved_docs])
            
            # Create prompt for LLM
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an insurance expert assistant. Answer the question based on the provided context from uploaded documents."),
                ("human", "Context from documents:\n{context}\n\nQuestion: {query}\n\nProvide a helpful answer based on the context.")
            ])
            
            # Build and invoke chain
            try:
                chain = prompt | self.llm
                response = chain.invoke({"context": context, "query": query})
                answer = response.content
            except Exception as e:
                logger.warning(f"LLM call failed: {e}. Using context only.")
                answer = f"Based on the documents: {context[:300]}..."
            
            return {
                "answer": answer,
                "sources": [
                    {
                        "content": doc.page_content[:500],
                        "metadata": dict(doc.metadata)
                    }
                    for doc in retrieved_docs
                ],
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"Error in retrieve_and_answer: {str(e)}")
            return self._mock_retrieve(query)
    
    def _mock_retrieve(self, query: str) -> Dict[str, Any]:
        """Mock retrieval when OpenAI is not available"""
        # Search in stored documents by keyword matching
        relevant_docs = []
        query_lower = query.lower()
        
        for doc_id, doc_data in self.documents.items():
            content = doc_data["content"]
            if any(word in content.lower() for word in query_lower.split()):
                relevant_docs.append({
                    "content": content[:500],
                    "metadata": {
                        "doc_id": doc_id,
                        **doc_data["metadata"]
                    }
                })
        
        answer = (
            f"Based on the uploaded documents, I found {len(relevant_docs)} relevant sections. "
            f"Your question was about: {query}. "
            f"Please ensure you have set up your OpenAI API key for full RAG capabilities."
        )
        
        return {
            "answer": answer,
            "sources": relevant_docs[:3],
            "status": "mock"
        }
    
    @traceable(name="search_documents", tags=["rag", "search"])
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query: Search query
            top_k: Number of top results
        
        Returns:
            list: Similar documents
        """
        try:
            if self.vector_store is None or self.embeddings is None:
                return self._mock_search(query, top_k)
            
            logger.info(f"Searching documents for: {query}")
            
            results = self.vector_store.similarity_search(query, k=top_k)
            
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": "N/A"
                }
                for doc in results
            ]
        
        except Exception as e:
            logger.error(f"Error in search_documents: {str(e)}")
            return []
    
    def _mock_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Mock search when embeddings not available"""
        results = []
        query_lower = query.lower()
        
        for doc_id, doc_data in self.documents.items():
            content = doc_data["content"]
            if any(word in content.lower() for word in query_lower.split()):
                results.append({
                    "content": content[:500],
                    "metadata": {
                        "doc_id": doc_id,
                        **doc_data["metadata"]
                    }
                })
        
        return results[:top_k]
    
    def get_document_summary(self, doc_id: str) -> Dict[str, Any]:
        """Get summary of a stored document"""
        if doc_id not in self.documents:
            return {"error": f"Document {doc_id} not found"}
        
        doc = self.documents[doc_id]
        content = doc["content"]
        
        return {
            "doc_id": doc_id,
            "size_bytes": len(content),
            "metadata": doc["metadata"],
            "added_at": doc["added_at"],
            "preview": content[:200] + "..." if len(content) > 200 else content
        }


# Global RAG instance
rag_system = None

def init_rag_system(groq_api_key: str = None) -> RAGVectorStore:
    """Initialize global RAG system with FREE Groq LLM"""
    global rag_system
    rag_system = RAGVectorStore(groq_api_key=groq_api_key)
    return rag_system

def get_rag_system() -> RAGVectorStore:
    """Get global RAG system instance"""
    global rag_system
    if rag_system is None:
        rag_system = RAGVectorStore()
    return rag_system
