"""
Redis-based Short-term Conversation Memory Module
Stores recent chat history for context-aware responses
"""

import redis
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Redis-based conversation memory for short-term chat history"""
    
    def __init__(self, 
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 ttl_hours: int = 24):
        """
        Initialize Redis conversation memory
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            ttl_hours: Time-to-live for conversation in hours
        """
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection
            self.redis_client.ping()
            self.connected = True
            logger.info(f"✅ Redis connected at {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {str(e)}. Running in memory-only mode.")
            self.redis_client = None
            self.connected = False
        
        self.ttl_seconds = ttl_hours * 3600
        self.memory_prefix = "conv:"  # Redis key prefix
        self.mem_store = {}  # Fallback in-memory store
    
    def save_message(self, conversation_id: str, role: str, message: str, metadata: Optional[Dict] = None) -> bool:
        """Save a message to conversation history"""
        try:
            message_obj = {
                "role": role,  # "user" or "assistant"
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            if self.connected and self.redis_client:
                # Save to Redis
                key = f"{self.memory_prefix}{conversation_id}"
                self.redis_client.lpush(key, json.dumps(message_obj))
                self.redis_client.expire(key, self.ttl_seconds)
                logger.info(f"💾 Saved message to conversation {conversation_id}")
            else:
                # Fallback to in-memory
                if conversation_id not in self.mem_store:
                    self.mem_store[conversation_id] = []
                self.mem_store[conversation_id].insert(0, message_obj)
                logger.info(f"💾 Saved message to memory {conversation_id} (in-memory mode)")
            
            return True
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            return False
    
    def get_conversation(self, conversation_id: str, max_messages: int = 10) -> List[Dict]:
        """Retrieve conversation history"""
        try:
            if self.connected and self.redis_client:
                # Retrieve from Redis
                key = f"{self.memory_prefix}{conversation_id}"
                messages_json = self.redis_client.lrange(key, 0, max_messages - 1)
                messages = [json.loads(msg) for msg in messages_json]
                # Reverse to get chronological order
                messages.reverse()
                logger.info(f"📖 Retrieved {len(messages)} messages from {conversation_id}")
                return messages
            else:
                # Retrieve from in-memory
                if conversation_id in self.mem_store:
                    messages = self.mem_store[conversation_id][:max_messages]
                    messages_copy = list(reversed(messages))
                    logger.info(f"📖 Retrieved {len(messages_copy)} messages from memory {conversation_id}")
                    return messages_copy
                return []
        except Exception as e:
            logger.error(f"Error retrieving conversation: {str(e)}")
            return []
    
    def get_recent_context(self, conversation_id: str, max_messages: int = 5) -> str:
        """Get formatted recent conversation context for RAG prompt"""
        messages = self.get_conversation(conversation_id, max_messages)
        if not messages:
            return ""
        
        context_lines = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            context_lines.append(f"{role}: {msg['message']}")
        
        return "\n".join(context_lines)
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history"""
        try:
            if self.connected and self.redis_client:
                key = f"{self.memory_prefix}{conversation_id}"
                self.redis_client.delete(key)
                logger.info(f"🗑️ Cleared conversation {conversation_id} from Redis")
            else:
                if conversation_id in self.mem_store:
                    del self.mem_store[conversation_id]
                    logger.info(f"🗑️ Cleared conversation {conversation_id} from memory")
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation: {str(e)}")
            return False
    
    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """Get metadata about a conversation"""
        messages = self.get_conversation(conversation_id, max_messages=100)
        if not messages:
            return {
                "conversation_id": conversation_id,
                "message_count": 0,
                "status": "empty"
            }
        
        user_msgs = [m for m in messages if m["role"] == "user"]
        assistant_msgs = [m for m in messages if m["role"] == "assistant"]
        
        return {
            "conversation_id": conversation_id,
            "message_count": len(messages),
            "user_messages": len(user_msgs),
            "assistant_messages": len(assistant_msgs),
            "status": "active",
            "first_message": messages[0]["timestamp"] if messages else None,
            "last_message": messages[-1]["timestamp"] if messages else None
        }
    
    def health_check(self) -> Dict:
        """Check Redis connection health"""
        if self.connected and self.redis_client:
            try:
                self.redis_client.ping()
                return {
                    "status": "connected",
                    "backend": "redis",
                    "host": self.redis_client.connection_pool.connection_kwargs.get("host"),
                    "db": self.redis_client.connection_pool.connection_kwargs.get("db")
                }
            except Exception as e:
                return {
                    "status": "disconnected",
                    "backend": "redis",
                    "error": str(e)
                }
        else:
            return {
                "status": "fallback",
                "backend": "in-memory",
                "conversations": len(self.mem_store),
                "warning": "Redis not available, using in-memory storage"
            }


# Global memory instance
_memory_instance = None

def init_memory(redis_host: str = None, redis_port: int = None, ttl_hours: int = 24) -> ConversationMemory:
    """Initialize global memory instance"""
    global _memory_instance
    
    host = redis_host or os.getenv("REDIS_HOST", "localhost")
    port = redis_port or int(os.getenv("REDIS_PORT", "6379"))
    
    _memory_instance = ConversationMemory(
        redis_host=host,
        redis_port=port,
        ttl_hours=ttl_hours
    )
    return _memory_instance

def get_memory() -> ConversationMemory:
    """Get global memory instance"""
    global _memory_instance
    if _memory_instance is None:
        init_memory()
    return _memory_instance
