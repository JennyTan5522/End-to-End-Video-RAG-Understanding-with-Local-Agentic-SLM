# 🐍 Backend - FastAPI Server

High-performance Python backend using FastAPI with PostgreSQL database for AI chat application.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running](#running)
- [API Documentation](#api-documentation)
- [Database](#database)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## 🌟 Overview

FastAPI-based REST API server featuring:
- ⚡ **Async/Await** - High-performance asynchronous request handling
- 🗄️ **PostgreSQL** - Robust relational database with async support
- 🔐 **CORS** - Configured for secure cross-origin requests
- 📝 **Auto Documentation** - Swagger UI and ReDoc built-in
- 🤖 **AI Integration** - Fallback AI response system (expandable)
- 🔍 **Logging** - Comprehensive logging for debugging

---

## 🔧 Prerequisites

| Software | Version | Purpose | Download |
|----------|---------|---------|----------|
| **Python** | 3.10+ | Runtime environment | [python.org](https://www.python.org/downloads/) |
| **PostgreSQL** | 15+ | Database system | [postgresql.org](https://www.postgresql.org/download/) |
| **pip** | Latest | Package manager | Included with Python |

### System Requirements

- **RAM:** 2GB minimum, 4GB recommended
- **Storage:** 500MB for dependencies
- **OS:** Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)

---

## 📦 Installation

### 1. Create Virtual Environment

**Option A: Using venv (Recommended)**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
venv\Scripts\activate

# Windows CMD:
venv\Scripts\activate.bat

# macOS/Linux:
source venv/bin/activate
```

**Option B: Using conda**
```bash
cd backend

# Create conda environment
conda create -p ./env python=3.11

# Activate environment
conda activate ./env
```

### 2. Install Dependencies

```bash
# Ensure virtual environment is activated
# You should see (venv) or (env) in your prompt

# Install all required packages
pip install -r requirements.txt
```

**Installed Packages:**
- `fastapi==0.104.1` - Web framework
- `uvicorn[standard]==0.24.0` - ASGI server
- `sqlalchemy==2.0.23` - ORM for database
- `asyncpg==0.29.0` - PostgreSQL async driver
- `pydantic==2.5.0` - Data validation
- `python-dotenv==1.0.0` - Environment variables

### 3. Verify Installation

```bash
# Check Python version
python --version
# Should show: Python 3.10.0 or higher

# Check installed packages
pip list | grep fastapi
pip list | grep sqlalchemy

# Test import
python -c "import fastapi, sqlalchemy; print('✅ All imports successful')"
```

---

## ⚙️ Configuration

### Database Setup

**1. Install PostgreSQL**

Download from [postgresql.org](https://www.postgresql.org/download/)

**Windows:** Use installer (includes pgAdmin)
**macOS:** `brew install postgresql`
**Linux:** `sudo apt install postgresql postgresql-contrib`

**2. Create Database**

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql shell:
CREATE DATABASE chatdb;

# Verify
\l  # List databases

# Exit
\q
```

**3. Configure Connection**

Edit `backend/database.py`:

```python
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/chatdb"
#                                    ^^^^^^  ^^^^^^^^        ^^^^  ^^^^^^^
#                                    user    password        host  database
```

**Default Credentials:**
- **User:** `postgres`
- **Password:** `password` (change this!)
- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `chatdb`

**Security Note:** Use environment variables in production!

```python
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
```

Create `.env` file:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/chatdb
```

### CORS Configuration

Edit `backend/app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Development
        "http://localhost:5173",   # Vite
        "https://yourdomain.com"   # Production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## 🚀 Running

### Development Mode

```bash
cd backend

# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Start server
python app.py
```

**Output:**
```
🚀 FastAPI AI Chat Server Starting...
✅ Database connection successful
📊 Database tables created successfully
🗄️ PostgreSQL database initialized

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Server runs on:** `http://localhost:8000`

### Production Mode

```bash
# Install production server
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000

# Or use uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Quick Test

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","timestamp":"2025-10-15T14:30:45.123456"}
```

---

## 📚 API Documentation

### Interactive Documentation

Once server is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Endpoints

#### 1. Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-15T14:30:45.123456"
}
```

**Status Codes:**
- `200 OK` - Server is healthy

---

#### 2. Send Chat Message

```http
POST /api/chat
Content-Type: application/json

{
  "message": "Hello AI!",
  "session_id": "default"
}
```

**Parameters:**
- `message` (string, required) - User's message (min 1 character)
- `session_id` (string, optional) - Session identifier (default: "default")

**Response:**
```json
{
  "success": true,
  "user_message": {
    "id": 1,
    "type": "user",
    "message": "Hello AI!",
    "timestamp": "2025-10-15T14:30:45.123456"
  },
  "ai_response": {
    "id": 2,
    "type": "ai",
    "message": "Hello! How can I help you today?",
    "timestamp": "2025-10-15T14:30:45.789012"
  },
  "session_id": "default"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid message (empty)
- `500 Internal Server Error` - Server error

**CURL Example:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello AI!", "session_id": "user123"}'
```

---

#### 3. Get Chat History

```http
GET /api/chat/{session_id}
```

**Parameters:**
- `session_id` (path parameter) - Session identifier

**Response:**
```json
{
  "success": true,
  "messages": [
    {
      "id": 1,
      "type": "user",
      "message": "Hello AI!",
      "timestamp": "2025-10-15T14:30:45.123456"
    },
    {
      "id": 2,
      "type": "ai",
      "message": "Hello! How can I help you today?",
      "timestamp": "2025-10-15T14:30:45.789012"
    }
  ],
  "session_id": "user123"
}
```

**Status Codes:**
- `200 OK` - Success (returns empty array if no messages)
- `500 Internal Server Error` - Database error

**CURL Example:**
```bash
curl http://localhost:8000/api/chat/user123
```

---

#### 4. Clear Chat Session

```http
DELETE /api/chat/{session_id}
```

**Parameters:**
- `session_id` (path parameter) - Session identifier

**Response:**
```json
{
  "success": true,
  "message": "Session user123 cleared"
}
```

**Status Codes:**
- `200 OK` - Session deleted
- `404 Not Found` - Session doesn't exist
- `500 Internal Server Error` - Database error

**Notes:**
- Deletes session and all associated messages (CASCADE)
- Safe to call even if session doesn't exist

**CURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/chat/user123
```

---

#### 5. List All Sessions

```http
GET /api/sessions
```

**Response:**
```json
{
  "success": true,
  "sessions": [
    {
      "id": "default",
      "created_at": "2025-10-15T14:00:00.000000",
      "message_count": 10
    },
    {
      "id": "user123",
      "created_at": "2025-10-15T15:30:00.000000",
      "message_count": 5
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Success
- `500 Internal Server Error` - Database error

**CURL Example:**
```bash
curl http://localhost:8000/api/sessions
```

---

## 🗄️ Database

### Schema

**Table: chat_sessions**
```sql
CREATE TABLE chat_sessions (
    id VARCHAR PRIMARY KEY,              -- Session identifier
    created_at TIMESTAMP DEFAULT NOW(),  -- Creation timestamp
    updated_at TIMESTAMP DEFAULT NOW(),  -- Last update
    user_id VARCHAR,                     -- Optional user identifier
    is_active BOOLEAN DEFAULT TRUE       -- Session status
);

-- Indexes
CREATE INDEX idx_session_created ON chat_sessions(created_at);
CREATE INDEX idx_session_user ON chat_sessions(user_id);
```

**Table: chat_messages**
```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,                  -- Auto-increment ID
    session_id VARCHAR REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(10),               -- 'user' or 'ai'
    content TEXT,                           -- Message content
    timestamp TIMESTAMP DEFAULT NOW(),      -- Message timestamp
    tokens_used INTEGER,                    -- AI tokens (optional)
    model_name VARCHAR(50),                 -- AI model used (optional)
    response_time INTEGER                   -- Response time in ms (optional)
);

-- Indexes
CREATE INDEX idx_message_session ON chat_messages(session_id);
CREATE INDEX idx_message_timestamp ON chat_messages(timestamp);
CREATE INDEX idx_message_type ON chat_messages(message_type);
```

### Database Operations

**Connect to Database:**
```bash
# Using psql
psql -U postgres -d chatdb

# Using pgAdmin
# Open pgAdmin → Servers → PostgreSQL → Databases → chatdb
```

**View Data:**
```sql
-- List all sessions
SELECT * FROM chat_sessions ORDER BY created_at DESC;

-- View messages for a session
SELECT * FROM chat_messages WHERE session_id = 'default' ORDER BY timestamp;

-- Count messages per session
SELECT session_id, COUNT(*) as message_count
FROM chat_messages
GROUP BY session_id;

-- Get recent activity
SELECT s.id, s.created_at, COUNT(m.id) as messages
FROM chat_sessions s
LEFT JOIN chat_messages m ON s.id = m.session_id
GROUP BY s.id, s.created_at
ORDER BY s.created_at DESC;
```

**Clear Data:**
```sql
-- Delete specific session (CASCADE deletes messages)
DELETE FROM chat_sessions WHERE id = 'default';

-- Clear all messages (keep sessions)
TRUNCATE TABLE chat_messages;

-- Clear all data
TRUNCATE TABLE chat_sessions CASCADE;

-- Drop and recreate tables
DROP TABLE chat_messages CASCADE;
DROP TABLE chat_sessions CASCADE;
-- Restart app.py to recreate tables
```

### Backup & Restore

**Backup:**
```bash
# Full database backup
pg_dump -U postgres chatdb > chatdb_backup.sql

# Table-specific backup
pg_dump -U postgres -t chat_messages chatdb > messages_backup.sql
```

**Restore:**
```bash
# Restore full database
psql -U postgres chatdb < chatdb_backup.sql

# Restore specific table
psql -U postgres chatdb < messages_backup.sql
```

---

## 💻 Development

### File Structure

```
backend/
├── app.py              # Main FastAPI application
├── database.py         # SQLAlchemy models and DB config
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Key Files

**app.py** - Main Application
- FastAPI app initialization
- CORS middleware configuration
- API endpoints
- AI response generation
- Error handling

**database.py** - Database Layer
- SQLAlchemy models (ChatSession, ChatMessage)
- Database connection management
- Async session handling
- Connection pooling

### Adding New Endpoints

```python
# In app.py

@app.get("/api/your-endpoint")
async def your_endpoint(db: AsyncSession = Depends(get_database)):
    """
    Your endpoint description
    """
    try:
        # Your logic here
        result = await db.execute(select(ChatSession))
        sessions = result.scalars().all()
        
        return {"success": True, "data": sessions}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### AI Integration

Current implementation uses **fallback responses**. To integrate real AI:

**Option 1: OpenAI API**
```python
pip install openai

# In app.py
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

async def generate_ai_response(user_message: str) -> str:
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content
```

**Option 2: Hugging Face Models**
```python
pip install transformers torch

from transformers import pipeline

generator = pipeline('text-generation', model='gpt2')

def generate_ai_response(user_message: str) -> str:
    result = generator(user_message, max_length=100)
    return result[0]['generated_text']
```

### Logging

```python
# View logs in terminal
# Default level: INFO

# Change log level in app.py:
logging.basicConfig(level=logging.DEBUG)

# Add custom logs:
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Change database password
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/SSL
- [ ] Configure proper CORS origins
- [ ] Set up database backups
- [ ] Configure logging to file
- [ ] Set up monitoring (e.g., Sentry)
- [ ] Use production ASGI server (gunicorn/uvicorn)

### Using Docker

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and Run:**
```bash
# Build image
docker build -t chat-backend .

# Run container
docker run -p 8000:8000 -e DATABASE_URL="..." chat-backend
```

### Environment Variables

Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/chatdb

# API Keys
OPENAI_API_KEY=sk-...

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

Load in `app.py`:
```python
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

---

## 🔍 Troubleshooting

### Common Issues

**Issue: "Connection refused" to PostgreSQL**
```bash
# Check PostgreSQL is running
# Windows: Services → postgresql-x64-15
# Linux: sudo systemctl status postgresql
# macOS: brew services list

# Check connection parameters
psql -U postgres -h localhost -p 5432

# Verify DATABASE_URL in database.py
```

**Issue: "Module not found"**
```bash
# Ensure virtual environment is activated
# You should see (venv) in prompt

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

**Issue: "Port 8000 already in use"**
```bash
# Find process using port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS:
lsof -ti:8000 | xargs kill -9

# Or use different port:
uvicorn app:app --port 8001
```

**Issue: "Table does not exist"**
```bash
# Tables are auto-created on startup
# If missing, drop and restart:

# In psql:
DROP TABLE chat_messages CASCADE;
DROP TABLE chat_sessions CASCADE;

# Restart app.py
python app.py
```

**Issue: "Async/await errors"**
```bash
# Ensure Python 3.10+
python --version

# Check all async functions use await
# Check database session is async

# Verify asyncpg is installed
pip list | grep asyncpg
```

### Debug Mode

Enable verbose logging:
```python
# In app.py
logging.basicConfig(level=logging.DEBUG)

# In database.py
engine = create_async_engine(
    DATABASE_URL,
    echo=True  # Shows all SQL queries
)
```

### Testing

**Manual Testing:**
```bash
# Health check
curl http://localhost:8000/api/health

# Send message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "session_id": "test123"}'

# Get history
curl http://localhost:8000/api/chat/test123

# Delete session
curl -X DELETE http://localhost:8000/api/chat/test123
```

**Using Python:**
```python
import requests

# Health check
r = requests.get("http://localhost:8000/api/health")
print(r.json())

# Send message
r = requests.post("http://localhost:8000/api/chat", json={
    "message": "Hello!",
    "session_id": "test"
})
print(r.json())
```

---

## 📦 Dependencies

```
fastapi==0.104.1          # Web framework
uvicorn[standard]==0.24.0 # ASGI server
sqlalchemy==2.0.23        # ORM
asyncpg==0.29.0          # PostgreSQL async driver
pydantic==2.5.0          # Data validation
python-dotenv==1.0.0     # Environment variables
```

---

## 📖 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

---

**Backend powered by ⚡ FastAPI + 🐘 PostgreSQL**
