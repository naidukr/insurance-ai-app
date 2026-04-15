# Redis Short-Term Conversation Memory

This document describes the Redis-based conversation memory system for the Insurance AI application.

## Overview

The application now stores conversation history in Redis by default, with automatic fallback to in-memory storage if Redis is unavailable. This enables:

- **Context-aware chat**: Each chat request uses recent conversation history for better context
- **Multi-turn conversations**: Users can have extended conversations with persistent context
- **Session management**: Conversations are isolated by `conversation_id`
- **Auto-expiration**: Conversations expire after 24 hours (configurable)

## Architecture

### Memory Module (`memory.py`)

The `ConversationMemory` class handles all memory operations:

```python
from memory import init_memory, get_memory

# Initialize Redis connection at startup
memory = init_memory(redis_host="localhost", redis_port=6379, ttl_hours=24)

# Get the global memory instance
memory = get_memory()

# Save user/assistant messages
memory.save_message(conversation_id="conv-123", role="user", message="What's my policy?")
memory.save_message(conversation_id="conv-123", role="assistant", message="Your policy...")

# Retrieve conversation history
messages = memory.get_conversation(conversation_id="conv-123", max_messages=10)

# Get formatted context for RAG
context = memory.get_recent_context(conversation_id="conv-123", max_messages=5)
```

### Key Features

- **Graceful Fallback**: If Redis is unavailable, the system automatically uses in-memory storage
- **TTL Management**: Old conversations automatically expire to prevent unbounded memory growth
- **Metadata Support**: Store arbitrary metadata with each message (sources, confidence, etc.)
- **Health Checks**: Monitor Redis connection status via `/api/memory/health`

## API Endpoints

### Chat Endpoints (Now Memory-Aware)

#### `POST /api/chat`
Chat with RAG-powered AI. Now stores conversation history.

**Request:**
```json
{
  "message": "What are my policy limits?",
  "conversation_id": "conv-user-123"  // optional, auto-generated if omitted
}
```

**Response:**
```json
{
  "conversation_id": "conv-user-123",
  "user_message": "What are my policy limits?",
  "ai_response": "Your policy covers...",
  "sources": [...],
  "context_from_history": true,
  "confidence": 0.85,
  "timestamp": "2026-04-14T..."
}
```

#### `POST /api/chat-with-record`
Chat with record context. Stores messages and uses recent conversation history.

### Memory Management Endpoints

#### `GET /api/memory/health`
Check the status of the memory system (Redis or fallback).

**Response:**
```json
{
  "status": "ok",
  "memory": {
    "status": "connected",
    "backend": "redis",
    "host": "localhost",
    "db": 0
  }
}
```

#### `GET /api/conversations/{conversation_id}/history`
Retrieve full conversation history.

**Query Parameters:**
- `limit` (int, default=20): Maximum messages to return

**Response:**
```json
{
  "conversation_id": "conv-123",
  "messages": [
    {
      "role": "user",
      "message": "What's my coverage?",
      "timestamp": "2026-04-14T..."
    },
    {
      "role": "assistant",
      "message": "Your coverage includes...",
      "timestamp": "2026-04-14T..."
    }
  ],
  "summary": {
    "message_count": 2,
    "user_messages": 1,
    "assistant_messages": 1,
    "first_message": "2026-04-14T...",
    "last_message": "2026-04-14T..."
  }
}
```

#### `GET /api/conversations/{conversation_id}/summary`
Get conversation metadata without full message history.

#### `DELETE /api/conversations/{conversation_id}`
Clear conversation history.

**Response:**
```json
{
  "conversation_id": "conv-123",
  "cleared": true
}
```

## Setup & Configuration

### Option 1: Local Redis (Recommended for Development)

```bash
# Install Redis (Windows: use WSL, Mac/Linux: brew/apt)
# Then start Redis:
redis-server

# Update .env
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Option 2: Docker Compose (Production-Ready)

```bash
# Use provided docker-compose-redis.yml
docker-compose -f docker-compose-redis.yml up -d

# Update .env
REDIS_HOST=redis
REDIS_PORT=6379
```

### Option 3: In-Memory Fallback (No Redis)

If Redis is not available, the system automatically uses in-memory storage:
- Messages stored in Python dictionaries
- No persistence between app restarts
- Good for testing/development

## Usage Examples

### Example 1: Simple Chat with History

```bash
# First message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my deductible?",
    "conversation_id": "user-john-001"
  }'

# Second message (uses first message as context)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can I change it?",
    "conversation_id": "user-john-001"
  }'
```

### Example 2: Retrieve Conversation History

```bash
curl http://localhost:8000/api/conversations/user-john-001/history
```

### Example 3: Check Memory System Status

```bash
curl http://localhost:8000/api/memory/health
```

## Configuration

Update these environment variables in `.env`:

```env
# Redis connection
REDIS_HOST=localhost          # Redis server host
REDIS_PORT=6379              # Redis server port
REDIS_DB=0                    # Redis database number
REDIS_PASSWORD=               # Password if needed

# Memory behavior
CONVERSATION_TTL_HOURS=24     # Auto-delete conversations after 24 hours
```

## Performance Considerations

### Memory Usage
- **Per message**: ~200-500 bytes (depends on message length)
- **Per conversation**: ~1-10 KB for typical conversations
- **Redis max memory**: Set to ~256 MB (configurable)
- **Expiration policy**: LRU (least recently used) when max memory exceeded

### Response Time
- **Save message**: ~1-2 ms (Redis) or <1 ms (in-memory)
- **Retrieve 10 messages**: ~3-5 ms (Redis) or <1 ms (in-memory)
- **No impact on RAG query latency** (async operations)

## Troubleshooting

### Redis Connection Issues

**Symptom**: "Redis connection failed"

**Solution**:
1. Verify Redis is running: `redis-cli ping` (should return "PONG")
2. Check host/port in `.env`
3. Allow fallback to in-memory storage (automatic)

### Memory Growing Too Large

**Symptom**: High memory usage

**Solutions**:
1. Reduce `CONVERSATION_TTL_HOURS` in `.env`
2. Manually clear old conversations: `DELETE /api/conversations/{id}`
3. Use Redis with configured maxmemory policies (see docker-compose-redis.yml)

### Conversations Not Persisting

**Symptom**: Messages lost after restart

**Explanation**: In-memory fallback is being used (not persistent by design)

**Solution**: Set up Redis with persistent storage (docker-compose-redis.yml uses AOF)

## Future Enhancements

- [ ] Conversation analytics (topic extraction, sentiment analysis)
- [ ] Conversation search/indexing
- [ ] Export conversations to PDF/JSON
- [ ] Conversation tagging and organization
- [ ] Multi-user conversation sharing
- [ ] Async message persistence for high-throughput scenarios
