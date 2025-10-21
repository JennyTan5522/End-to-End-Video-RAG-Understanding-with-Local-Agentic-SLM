# Backend - FastAPI Server

High-performance Python backend using FastAPI with PostgreSQL database for AI chat application.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running](#running)
- [Project Structure](#project-structure)

---

## Overview

### Built With:

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-DC244C?logo=qdrant&logoColor=white)
![LangChain](https://img.shields.io/badge/🦜_LangChain-1C3C3C?logo=langchain&logoColor=white)
![LangGraph](https://img.shields.io/badge/🕸️_LangGraph-FF6B6B?logoColor=white)
![MCP](https://img.shields.io/badge/🔌_MCP-000000?logoColor=white)

### Key Features:
- The backend contains the core AI logic and implementation of a lightweight local language model capable of analyzing and querying short video files (🎥 Video RAG).

### Architecture & Components

| Component | Description |
|-----------|-------------|
| 🤖 **AI & Model Stack** | Built using Hugging Face 🤗 open-source local models for chat, embedding, and summarization |
| 🔗 **LangChain + LangGraph** | Core architecture orchestrated using LangChain and LangGraph with a multi-agent ReAct workflow for coordination and tool routing |
| ⚙️ **MCP Integration** | Integrated with MCP (Model Context Protocol) for extensible multi-tool capability and seamless communication between agents |
| ⚡ **FastAPI** | Provides REST endpoints for backend communication |
| 🗄️ **PostgreSQL** | Stores persistent chat history |
| 🗃️ **Qdrant Vector Database** | High-performance vector database for semantic search and retrieval-augmented generation (RAG) |

### Model Configuration

| Task | Model | Description |
|------|-------|-------------|
| **Transcript Audio Model** | `distil-whisper/distil-small.en` | Efficient local ASR model for transcribing audio from videos |
| **Frame & Transcript Summarization / RAG** | `yangjie-cv/WeThink-Qwen2.5VL-7B` | Vision-Language model used for multimodal understanding and RAG generation |
| **Embedding Model** | `BAAI/bge-small-en-v1.5` | Compact text embedding model for vector retrieval |
| **Supervisor Routing Model** | `Qwen/Qwen2.5-Coder-7B-Instruct` | Handles agent routing, reasoning, and code-based task generation |

### Multi-Agent Configuration

- **Local SLM Multi-Agent AI System with Supervisor Routing:**
The backend implements a multi-agent architecture using LangGraph and local LLMs, where a supervisor agent intelligently routes requests to specialized agents:
  1. **💬 General Agent** - Handles general questions and conversational queries

  2. **🎬 Video Frame Processing Agent** - Processes video files, extracts frames at specified intervals, and generates frame-level summaries (MCP tools integration)

  3. **🔊 Audio Processing Agent** - Extracts audio from videos, performs transcription chunking, and generates transcript summaries (MCP tools integration)

  4. **🔍 RAG Agent** - Retrieval-Augmented Generation for video and speech Q&A:
    - Implements hybrid search combining BM25 (keyword-based) and dense vector search
    - Integrates with Qdrant vector database for efficient semantic retrieval
    - Provides context-aware answers based on video content

  5. **📝 Summary Agent** - Generates comprehensive summaries from chunked transcripts

  6. **📄 Report Agent** - Automatically generates structured PDF reports combining video analysis, transcripts, and insights


💡 This setup uses small local models for experimental testing and performance benchmarking. You can easily replace these models with larger or custom variants in your configuration for improved accuracy or multimodal reasoning performance

---

## Prerequisites

| Software | Version | Purpose | Download |
|----------|---------|---------|----------|
| **Python** | 3.11 | Runtime environment | [python.org](https://www.python.org/downloads/) |
| **PostgreSQL** | 15+ | Database system | [postgresql.org](https://www.postgresql.org/download/) |
| **Qdrant** | Latest | Vector database | [qdrant.tech](https://qdrant.tech/documentation/guides/installation/) |
| **pip** | Latest | Package manager | Included with Python |

### System Requirements

- **GPU:** NVIDIA GPU with CUDA support (Compute Capability ≥ 7.0; e.g., RTX 20-series or newer)
- **VRAM:** 8 GB minimum, 16 GB+ recommended for large models
- **RAM:** 8 GB minimum, 16 GB recommended
- **Storage:** 10 GB+ free space for models and dependencies
- **Driver & Toolkit:** NVIDIA Driver ≥ 530 and CUDA ≥ 12.0 (cuDNN ≥ 8.9)

**Note:** This setup I was tested on [RunPod](https://www.runpod.io/) VM with RTX 4090

---

## Installation

### 1. Create Virtual Environment

**Option A: Using venv**
```bash
cd backend

# Create virtual environment
python -m venv env

# Activate virtual environment
# Windows PowerShell:
env\Scripts\activate

# Windows CMD:
env\Scripts\activate.bat

# macOS/Linux:
source env/bin/activate
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

---

## Configuration

### Database Setup

**1. Install PostgreSQL**

Download from [postgresql.org](https://www.postgresql.org/download/)

- **Windows:** Use installer (includes pgAdmin)
- **macOS:** `brew install postgresql`
- **Linux:** `sudo apt install postgresql postgresql-contrib`

**Or using apt:**
```bash
apt-get install -y postgresql postgresql-contrib
service postgresql start
```

**2. Create Database**

```bash
# Connect to PostgreSQL
su - postgres -c "psql"

# Set password for user `postgres` (default: admin)
\password postgres

# In psql shell:
CREATE DATABASE chatdb;

# Verify
\l  # List databases

# Exit
\q
```

---

### Qdrant Setup

**Option A: Using Docker (Recommended)**
```bash
docker run -d --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v ${PWD}/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

**Option B: Download Binary**
```bash
# Linux/macOS
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz | tar xz

# Run Qdrant
./qdrant
```

**Option C: Install via package manager**
```bash
# Using Homebrew (macOS)
brew install qdrant

# Or download from https://qdrant.tech/documentation/guides/installation/
```

---

## Running

### Development Mode

```bash
cd backend

# Activate virtual environment
env\Scripts\activate  # Windows
source env/bin/activate  # macOS/Linux

# Start backend server
python -m web.app
```

**Server runs on:** `http://localhost:8000`

### Quick Test

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","timestamp":"2025-10-15T14:30:45.123456"}
```

---

## Project Structure

```
backend/
├── web/
│   ├── agent/                          # Agent implementations
│   │   ├── agent_workflow_builder.py   # Workflow orchestration
│   │   ├── supervisor_agent.py         # Supervisor routing agent
│   │   ├── rag_agent.py                # RAG Q&A agent
│   │   ├── summary_agent.py            # Video summarization agent
│   │   ├── report_agent.py             # PDF report generation agent
│   │   ├── audio_extraction_agent.py   # Audio processing agent
│   │   ├── frame_extraction_agent.py   # Frame extraction agent
│   │   └── general_question_agent.py   # General Q&A agent
│   │
│   ├── mcp_tools/                      # MCP tool integrations
│   ├── app.py                          # Main FastAPI application
│   ├── database.py                     # SQLAlchemy models and DB config
│   └── model_manager.py                # LLM model management
│
├── src/
│   ├── llm/                            # LLM modules
│   │   ├── chat_model.py               # Chat model configuration
│   │   ├── embedding_model.py          # Embedding model setup
│   │   ├── model_loader.py             # Model loading utilities
│   │   └── inference.py                # Inference operations
│   │
│   ├── prompt_engineering/             # Prompt templates
│   │   ├── templates.py                # Prompt templates
│   │   └── schemas.py                  # Pydantic schemas
│   │
│   └── vector_database/                # Vector DB operations
│       ├── qdrant_client.py            # Qdrant client setup
│       ├── retriever.py                # Retrieval functions
│       ├── embeddings.py               # Embedding generation
│       └── utils.py                    # Utility functions
│
├── config/
│   └── service_config.py               # Service configuration
│
├── test/                               # Test files
├── data/                               # Data storage (videos, reports)
├── notebooks/                          # Jupyter notebooks
├── qdrant_storage/                     # Qdrant vector database storage
├── env/                                # Virtual environment
│
├── .env                                # Environment variables
├── .env_example                        # Environment template
├── Dockerfile                          # Docker container config
├── requirements.txt                    # Python dependencies
├── test.py                             # Test script
└── README.md                           # This file
```

---

**Backend powered by FastAPI + PostgreSQL + Qdrant**