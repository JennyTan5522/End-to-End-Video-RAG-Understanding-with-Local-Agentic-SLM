# 🤖 AI Chat Application

A full-stack AI chat application with React frontend, FastAPI backend, PostgreSQL database, and Tauri desktop support.

![React](https://img.shields.io/badge/React-19.0.0-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)
![Tauri](https://img.shields.io/badge/Tauri-2.0.5-FFC131?logo=tauri)

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### Core Functionality
- 💬 **Real-time Chat Interface** - Modern, responsive chat UI with message history
- 🤖 **AI Response Generation** - Intelligent AI responses with fallback system
- 💾 **Persistent Storage** - PostgreSQL database for chat history and sessions
- 🔄 **Session Management** - Multiple chat sessions with unique identifiers
- 🌐 **Dual Mode Support** - Run as web app or native desktop application
- 🔌 **Connection Monitoring** - Visual API health status indicator

### Technical Features
- ⚡ **Async Architecture** - FastAPI with async/await for high performance
- 🔐 **CORS Security** - Configured for secure cross-origin requests
- 🎨 **Modern UI/UX** - Tailwind CSS with smooth animations
- 🖥️ **Desktop App** - Tauri wrapper for native desktop experience
- 📊 **Database Indexing** - Optimized PostgreSQL queries
- 🔍 **Error Handling** - Comprehensive error handling and logging

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│  ┌─────────────────────┐      ┌─────────────────────┐     │
│  │   Web Browser       │      │  Desktop App        │     │
│  │   (localhost:5173)  │      │  (Tauri)            │     │
│  └──────────┬──────────┘      └──────────┬──────────┘     │
└─────────────┼─────────────────────────────┼────────────────┘
              │                             │
              │ HTTP/Fetch                  │ IPC/HTTP
              │                             │
┌─────────────┴─────────────────────────────┴────────────────┐
│              React Frontend (Vite)                          │
│  • Components: ChatBox, Message, Sidebar                    │
│  • Services: API abstraction layer                          │
│  • Context: Global state management                         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              │ REST API
                              │ (JSON)
┌─────────────────────────────┴───────────────────────────────┐
│              FastAPI Backend                                 │
│  • Endpoints: /api/chat, /api/health                        │
│  • AI Logic: Fallback response system                       │
│  • Database: SQLAlchemy ORM with async support              │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              │ SQL Queries
                              │ (async)
┌─────────────────────────────┴───────────────────────────────┐
│              PostgreSQL Database                             │
│  • Tables: chat_sessions, chat_messages                     │
│  • Indexes: Optimized for performance                       │
│  • Constraints: Foreign keys with CASCADE delete            │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 Prerequisites

### Required Software

| Software | Version | Purpose | Download |
|----------|---------|---------|----------|
| **Python** | 3.10+ | Backend runtime | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | Frontend build tool | [nodejs.org](https://nodejs.org/) |
| **PostgreSQL** | 15+ | Database | [postgresql.org](https://www.postgresql.org/download/) |
| **Rust** | 1.70+ | Tauri desktop (optional) | [rustup.rs](https://rustup.rs/) |

### Optional Tools
- **pgAdmin** - PostgreSQL GUI management
- **Postman** - API testing
- **VS Code** - Recommended IDE

---

## 🚀 Quick Start

### 🐋 **Option 1: Docker (Recommended - Fastest Setup)**

**Prerequisites:** Install [Docker Desktop](https://www.docker.com/products/docker-desktop)

#### **Windows:**
```bash
# Clone repository
git clone <repository-url>
cd genai_video

# Run setup script
docker-start.bat
```

#### **Linux/macOS:**
```bash
# Clone repository
git clone <repository-url>
cd genai_video

# Make script executable
chmod +x docker-start.sh

# Run setup script
./docker-start.sh
```

#### **Or manually:**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**That's it!** 🎉
- Frontend: http://localhost
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### 💻 **Option 2: Manual Setup (Development)**

### 1️⃣ Clone Repository

```bash
git clone <repository-url>
cd genai_video
```

### 2️⃣ Setup PostgreSQL

```bash
# Install PostgreSQL from official website
# Create database and user

# Open pgAdmin or psql
psql -U postgres

# Create database
CREATE DATABASE chatdb;

# Verify connection (default credentials in backend/database.py):
# postgresql+asyncpg://postgres:password@localhost:5432/chatdb
```

### 3️⃣ Setup Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python app.py
```

**Backend should start on:** `http://localhost:8000`

### 4️⃣ Setup Frontend

```bash
# Open new terminal
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend should start on:** `http://localhost:5173`

### 5️⃣ Test the Application

1. Open browser: `http://localhost:5173`
2. Check connection status: Should show "🟢 Connected"
3. Send a message: "Hello AI!"
4. Verify response appears
5. Refresh page - messages should persist

---

## 📁 Project Structure

```
genai_video/
├── backend/                      # FastAPI backend
│   ├── app.py                   # Main application entry point
│   ├── database.py              # SQLAlchemy models and DB config
│   ├── requirements.txt         # Python dependencies
│   └── README.md                # Backend documentation
│
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── ChatBox.jsx     # Main chat interface
│   │   │   ├── Message.jsx     # Message display component
│   │   │   └── Sidebar.jsx     # Navigation sidebar
│   │   ├── services/           # API service layer
│   │   │   └── api.js          # Backend communication
│   │   ├── context/            # React Context
│   │   │   └── AppContext.jsx  # Global state
│   │   ├── assets/             # Static files
│   │   ├── App.jsx             # Root component
│   │   └── main.jsx            # Entry point
│   ├── src-tauri/              # Tauri desktop wrapper
│   │   ├── src/
│   │   │   ├── main.rs         # Rust entry point
│   │   │   └── lib.rs          # Tauri commands
│   │   ├── Cargo.toml          # Rust dependencies
│   │   └── tauri.conf.json     # Tauri configuration
│   ├── package.json            # Node.js dependencies
│   ├── vite.config.js          # Vite configuration
│   └── README.md               # Frontend documentation
│
└── README.md                    # This file
```

---

## 💻 Development

### Backend Development

```bash
cd backend

# Activate environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run with auto-reload
python app.py

# Access API docs
http://localhost:8000/docs       # Swagger UI
http://localhost:8000/redoc      # ReDoc
```

**Common Backend Tasks:**
```bash
# Test database connection
python -c "from database import test_connection; import asyncio; asyncio.run(test_connection())"

# View logs
# Check terminal output for INFO/ERROR logs

# Reset database
# Drop and recreate tables (in psql)
DROP TABLE chat_messages CASCADE;
DROP TABLE chat_sessions CASCADE;
# Restart app.py to recreate tables
```

### Frontend Development

```bash
cd frontend

# Development mode (with hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

**Common Frontend Tasks:**
```bash
# Clear npm cache
rm -rf node_modules package-lock.json
npm install

# Update dependencies
npm update

# Check for outdated packages
npm outdated
```

### Tauri Desktop Development

```bash
cd frontend

# Install Tauri CLI (first time only)
cargo install tauri-cli

# Run desktop app in dev mode
npm run tauri:dev

# Build desktop installer
npm run tauri:build

# Find installer at:
# frontend/src-tauri/target/release/bundle/msi/  (Windows)
```

---

## 🐋 Docker Deployment

### Quick Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Stop all services
docker-compose stop

# Restart services
docker-compose restart

# Remove all containers and volumes
docker-compose down -v

# Rebuild containers
docker-compose build --no-cache

# Check service status
docker-compose ps
```

### Docker Architecture

```
┌─────────────────────────────────────────────────────┐
│  Docker Compose Orchestration                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Frontend    │  │   Backend    │  │ Postgres │ │
│  │  (Nginx)     │→ │  (FastAPI)   │→ │   DB     │ │
│  │  Port: 80    │  │  Port: 8000  │  │Port: 5432│ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                      │
│  Network: ai-chat-network (bridge)                  │
│  Volume: postgres_data (persistent)                 │
└─────────────────────────────────────────────────────┘
```

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# Database
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql+asyncpg://postgres:your_secure_password@postgres:5432/chatdb

# Optional: Add API keys
OPENAI_API_KEY=your_key_here
```

### Docker Production Deployment

**Deploy to Cloud:**
```bash
# AWS ECS, Azure Container Instances, Google Cloud Run
docker-compose up -d

# Or build and push to registry
docker build -t your-registry/ai-chat-backend:latest ./backend
docker build -t your-registry/ai-chat-frontend:latest ./frontend
docker push your-registry/ai-chat-backend:latest
docker push your-registry/ai-chat-frontend:latest
```

**Docker Swarm:**
```bash
docker stack deploy -c docker-compose.yml ai-chat
```

**Kubernetes:**
```bash
# Generate k8s manifests
kompose convert

# Deploy
kubectl apply -f .
```

### Exposed Ports

| Port | Service | Protocol | Purpose |
|------|---------|----------|---------|
| **80** | Frontend (Nginx) | HTTP | Web interface |
| **8000** | Backend (FastAPI) | HTTP | REST API |
| **5432** | PostgreSQL | TCP | Database |

---

## 🌐 Traditional Deployment

### Backend Deployment

**Option 1: Traditional Server (Ubuntu/Debian)**
```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip postgresql

# Setup application
cd backend
pip install -r requirements.txt

# Use production server
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000
```

**Option 2: Docker**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Deployment

**Option 1: Static Hosting (Vercel/Netlify)**
```bash
cd frontend
npm run build
# Upload 'dist' folder to hosting service
```

**Option 2: Nginx**
```nginx
# /etc/nginx/sites-available/chat-app
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /var/www/chat-app/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

### Desktop App Distribution

```bash
# Build installers
cd frontend
npm run tauri:build

# Distribute:
# Windows: .msi installer
# macOS: .dmg installer
# Linux: .deb or .AppImage
```

---

## 📚 API Documentation

### Authentication
Currently no authentication required (add JWT for production)

### Base URL
- **Development:** `http://localhost:8000/api`
- **Production:** Update in `frontend/src/services/api.js`

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

#### 2. Send Chat Message
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Hello AI!",
  "session_id": "default"
}
```

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
    "timestamp": "2025-10-15T14:30:45.456789"
  },
  "session_id": "default"
}
```

#### 3. Get Chat History
```http
GET /api/chat/{session_id}
```

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
      "timestamp": "2025-10-15T14:30:45.456789"
    }
  ],
  "session_id": "default"
}
```

#### 4. Clear Session
```http
DELETE /api/chat/{session_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Session default cleared"
}
```

#### 5. List Sessions
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
    }
  ]
}
```

---

## 🔍 Troubleshooting

### Backend Issues

**Issue: "Connection refused" to PostgreSQL**
```bash
# Check PostgreSQL is running
# Windows: Services → postgresql-x64-15
# Linux: sudo systemctl status postgresql

# Verify connection details in backend/database.py
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/chatdb"
```

**Issue: "Module not found"**
```bash
# Ensure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

**Issue: "Port 8000 already in use"**
```bash
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:8000 | xargs kill -9
```

### Frontend Issues

**Issue: "npm ERR! code ECONNREFUSED"**
```bash
# Check backend is running on port 8000
curl http://localhost:8000/api/health

# Check CORS settings in backend/app.py
```

**Issue: Blank page after npm run dev**
```bash
# Clear cache and rebuild
rm -rf node_modules dist .vite
npm install
npm run dev
```

**Issue: "Failed to fetch" in browser console**
```bash
# Check API URL in frontend/src/services/api.js
const API_BASE_URL = 'http://localhost:8000/api'

# Verify backend CORS allows frontend origin
```

### Tauri Issues

**Issue: "Rust not installed"**
```bash
# Install Rust from https://rustup.rs/
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify installation
rustc --version
cargo --version
```

**Issue: "Failed to compile"**
```bash
# Clean and rebuild
cd frontend/src-tauri
cargo clean
cd ..
npm run tauri:dev
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **React** - UI library
- **Tauri** - Desktop app framework
- **PostgreSQL** - Database system
- **Tailwind CSS** - Styling framework

---

## 📞 Support

For questions or issues:
- Create an issue in the repository
- Check existing documentation
- Review API docs at `http://localhost:8000/docs`

---

**Built with ❤️ for Intel Interview Project**