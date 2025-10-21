# Frontend - React Application

React-based frontend for AI Video Assistant with real-time chat, video upload, and processing capabilities.

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)

---

## Overview

**Built With:**

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=FFD62E)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Tauri](https://img.shields.io/badge/Tauri-FFC131?style=for-the-badge&logo=tauri&logoColor=white)
![Axios](https://img.shields.io/badge/Axios-5A29E4?style=for-the-badge&logo=axios&logoColor=white)

**Key Features:**
- Real-time chat interface with AI responses
- Video upload (drag-drop, MP4/AVI/MOV/MKV)
- Live progress tracking for video processing
- Session-based chat history
- Web & desktop app support (Tauri)

---

## Prerequisites

| Software | Version | Download |
|----------|---------|----------|
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **npm** | 9+ | Included with Node.js |
| **Rust** | 1.70+ | [rustup.rs](https://rustup.rs/) (for Tauri only) |

---

## Installation

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install the Required NPM Packages

- Run the following command inside the `frontent` directory:
    ```bash
    npm install
    ```

- Optional (for Tauri setup):
    ```bash
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    ```

- **Verify Installation:**
```bash
node --version    # v18.0.0 or higher
npm --version     # 9.0.0 or higher
rustc --version   # 1.70.0 or higher (for Tauri only)
cargo --version   # (for Tauri only)
```

### 3. Configure Environment Variables

- Create a .env file inside the `frontend/` directory:
    - VITE_API_BASE_URL defines the backend API endpoint that your frontend will communicate with.
    ```env
    VITE_API_BASE_URL=http://localhost:8000
    ```

- Or copy from the example env file:
    ```bash
    cp .env_example .env
    ```

### 4. Start Development Server

- You can start your application in either `Web Browser` or `Desktop App (Tauri)` mode:

    **Option A: Web Browser (Local)**
    ```bash
    npm run dev
    # Application runs at http://localhost:5173
    ```

- **Option B: Web Browser (Network Access)**
    ```bash
    npm run dev -- --host 0.0.0.0 --port 5173 --strictPort
    # Access from any device on your network at http://<your-ip>:5173
    ```

- **Option C: Desktop App (Tauri)**
    ```bash
    # Run desktop app
    npm run tauri dev
    ```

---

## Tauri Desktop Application

### Setup

**1. Install Rust**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**2. Verify Installation**
```bash
rustc --version
cargo --version
```

### Development

**Run in Development Mode:**
```bash
npm run tauri dev
```
Launches desktop app with hot-reload for testing.

### Production

**Build Desktop App:**
```bash
npm run tauri build
```
Creates installable application for distribution.

**Generate App Icons:**
```bash
npm run tauri icon
```

---

## Project Structure

```
frontend/
├── src/
│   ├── components/             # React components
│   │   ├── ChatBox.jsx         # Main chat interface
│   │   ├── Message.jsx         # Message display
│   │   ├── ProgressBar.jsx     # Upload progress
│   │   └── Sidebar.jsx         # Navigation
│   │
│   ├── services/               # API layer
│   │   └── api.js              # Backend communication
│   │
│   ├── context/                # State management
│   │   └── AppContext.jsx      # Global state
│   │
│   ├── assets/                 # Static files
│   │   ├── *.svg               # Icons
│   │   ├── *.jpg               # Images
│   │   └── prism.css           # Code highlighting
│   │
│   ├── App.jsx                 # Root component
│   ├── main.jsx                # Entry point
│   └── index.css               # Global styles
│
├── src-tauri/                  # Tauri desktop
│   ├── src/
│   ├── Cargo.toml
│   └── tauri.conf.json
│
├── public/                     # Static assets
├── dist/                       # Build output
├── .env                        # Environment config
├── .env_example                # Environment template
├── package.json                # Dependencies
├── vite.config.js              # Vite config
└── README.md
```
---

**Note:** This guide covers development setup only. Production builds are not included.

---

**Built with Vite + React + Tauri**