# Chat History Persistence Implementation

## Overview

Chat history is now **persistently stored in PostgreSQL** instead of in-memory. This means conversations are preserved across server restarts and can be retrieved at any time.

## What Changed

### 1. **Database Models** (`db/models.py`)

Added two new tables:

#### `conversations` Table
- Stores conversation/thread metadata
- Links to users (optional - for future user-specific conversations)
- Tracks when conversations were created and updated

#### `checkpoints` Table  
- Stores LangGraph state snapshots (the actual chat history)
- Each checkpoint contains the full conversation state
- Linked to conversations via `thread_id`

### 2. **PostgreSQL Checkpointer** (`services/db_checkpointer.py`)

Created a custom `PostgresCheckpointer` class that:
- Implements LangGraph's `BaseCheckpointSaver` interface
- Saves conversation state to PostgreSQL after each interaction
- Retrieves conversation history from the database
- Handles serialization/deserialization of LangChain messages

### 3. **AI Service Update** (`services/ai_service.py`)

- Replaced `MemorySaver()` with `PostgresCheckpointer()`
- Now uses database for persistent storage instead of memory

### 4. **Database Configuration** (`db/base.py`)

- Added sync database engine (needed for checkpointer)
- Added `SessionLocal` for synchronous database operations
- Kept async engine for FastAPI endpoints

### 5. **Dependencies** (`pyproject.toml`)

- Added `psycopg2-binary` for synchronous PostgreSQL connections

## How It Works

```
User sends message
       ↓
AI Agent processes
       ↓
PostgresCheckpointer saves state to DB
       ↓
Response sent to user
       ↓
[Server restarts]
       ↓
User sends another message
       ↓
PostgresCheckpointer loads previous state from DB
       ↓
Agent continues conversation with full context!
```

## Database Schema

```sql
-- Conversations table
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Checkpoints table
CREATE TABLE checkpoints (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR NOT NULL REFERENCES conversations(thread_id) ON DELETE CASCADE,
    checkpoint_id VARCHAR NOT NULL,
    parent_checkpoint_id VARCHAR,
    checkpoint_data TEXT NOT NULL,  -- JSON serialized state
    checkpoint_metadata TEXT,        -- JSON serialized metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_thread_checkpoint ON checkpoints(thread_id, checkpoint_id);
```

## Setup Instructions

### 1. Start Docker Services

```bash
cd /Users/ashutosh/Works/personal/TPA
docker-compose up -d
```

This will start:
- PostgreSQL database
- Backend API

### 2. Tables Are Auto-Created

The tables will be automatically created when the backend starts via `init_db()` in `main.py`. No manual migration needed!

### 3. Verify It's Working

```bash
# Check backend logs
docker-compose logs -f api

# You should see:
# ✅ PostgresCheckpointer initialized
# 🗄️ Using PostgreSQL checkpointer for persistent chat history
```

## Testing Persistence

### Test 1: Basic Conversation
```bash
# Send a message
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "My name is John", "thread_id": "test-123"}'

# Response: "Nice to meet you, John!"
```

### Test 2: Restart Server
```bash
# Restart the backend
docker-compose restart api
```

### Test 3: Continue Conversation
```bash
# Send another message with same thread_id
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my name?", "thread_id": "test-123"}'

# Response: "Your name is John!" ✅
# (It remembered from before the restart!)
```

### Test 4: Check Database
```bash
# Connect to PostgreSQL
docker exec -it tpa_postgres psql -U tpa_user -d tpa_db

# View conversations
SELECT * FROM conversations;

# View checkpoints
SELECT id, thread_id, checkpoint_id, created_at FROM checkpoints;
```

## Key Features

✅ **Persistent Storage**: Conversations survive server restarts
✅ **Full Context**: Complete message history maintained
✅ **Scalable**: Can handle multiple concurrent conversations
✅ **User Linkage**: Ready for user-specific conversation history
✅ **Automatic**: No manual intervention needed

## Benefits Over In-Memory Storage

| Feature | In-Memory (Old) | PostgreSQL (New) |
|---------|----------------|------------------|
| Survives restart | ❌ No | ✅ Yes |
| Scalable | ❌ Limited by RAM | ✅ Database capacity |
| Multi-server | ❌ Each server isolated | ✅ Shared state |
| Historical queries | ❌ Not possible | ✅ Full SQL access |
| User conversations | ❌ Not trackable | ✅ Per-user history |

## Future Enhancements

- **User-specific conversations**: Link conversations to authenticated users
- **Conversation titles**: Auto-generate titles from first message
- **Search**: Full-text search across conversation history
- **Analytics**: Track conversation metrics and patterns
- **Export**: Export conversations to JSON/PDF
- **Cleanup**: Automatic deletion of old conversations

## Troubleshooting

### Issue: "No checkpoint found"
- **Cause**: New thread_id or database was reset
- **Solution**: This is normal for first messages

### Issue: "Database connection error"
- **Cause**: PostgreSQL not running
- **Solution**: `docker-compose up -d postgres`

### Issue: "Tables don't exist"
- **Cause**: Database initialization failed
- **Solution**: Check backend logs, restart API service

## Files Modified

1. `db/models.py` - Added Conversation and Checkpoint models
2. `db/base.py` - Added sync engine and SessionLocal
3. `db/__init__.py` - Exported new models
4. `services/db_checkpointer.py` - New PostgreSQL checkpointer
5. `services/ai_service.py` - Use PostgresCheckpointer instead of MemorySaver
6. `pyproject.toml` - Added psycopg2-binary dependency

---

**Implementation Complete!** 🎉

Chat history is now fully persistent in PostgreSQL.

