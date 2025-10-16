# 🎨 Frontend - React Application

React-based frontend for AI Chat application with Vite, Tailwind CSS, and Tauri desktop support.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Development](#development)
- [Building](#building)
- [Project Structure](#project-structure)
- [Components](#components)
- [API Integration](#api-integration)
- [Tauri Desktop](#tauri-desktop)
- [Troubleshooting](#troubleshooting)

---

## 🌟 Overview

Modern React application featuring:
- ⚡ **Vite** - Lightning-fast dev server and build tool
- 🎨 **Tailwind CSS** - Utility-first CSS framework
- 🔄 **React Router** - Client-side routing
- 🖥️ **Tauri Support** - Native desktop application capability
- 📡 **API Service Layer** - Clean backend communication abstraction

---

## 🔧 Prerequisites

| Software | Version | Download |
|----------|---------|----------|
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **npm** | 9+ | Included with Node.js |
| **Rust** | 1.70+ (for Tauri) | [rustup.rs](https://rustup.rs/) |

### Verify Installation

```bash
node --version    # Should show v18.0.0 or higher
npm --version     # Should show 9.0.0 or higher
rustc --version   # Should show 1.70.0 or higher (for Tauri)
```

---

## 📦 Installation

### 1. Install Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

This will install:
- React 19.2.0
- Vite 7.1.9
- Tailwind CSS 4.1.14
- React Router 7.9.4
- Tauri API (for desktop mode)

### 2. Verify Backend Connection

Ensure backend is running on `http://localhost:8000`:

```bash
# Test backend health
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-15T14:30:45.123456"
}
```

---

## 💻 Development

### Start Development Server

```bash
# Start Vite dev server
npm run dev
```

**Output:**
```
VITE v7.1.9  ready in 1909 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

### Development Features

- ⚡ **Hot Module Replacement (HMR)** - Instant updates without page reload
- 🔍 **Source Maps** - Easy debugging with original source code
- 📊 **React DevTools** - Component inspection and profiling
- 🎯 **Auto Port Selection** - Falls back to 5174, 5175 if 5173 is busy

### Available Scripts

```bash
# Development
npm run dev              # Start dev server on port 5173

# Building
npm run build            # Production build to 'dist' folder
npm run preview          # Preview production build locally

# Tauri Desktop
npm run tauri            # Run Tauri CLI commands
npm run tauri:dev        # Run desktop app in dev mode
npm run tauri:build      # Build desktop installer
npm run tauri:init       # Initialize Tauri project

# Code Quality
npm run lint             # Run ESLint (if configured)
```

---

## 🏗️ Building

### Web Application

```bash
# Create production build
npm run build

# Output location: dist/
# Contains optimized HTML, CSS, JS, and assets

# Preview production build
npm run preview
# Serves the 'dist' folder at http://localhost:4173
```

**Build Output:**
```
dist/
├── index.html              # Entry HTML file
├── assets/
│   ├── index-[hash].js    # Bundled JavaScript
│   ├── index-[hash].css   # Bundled CSS
│   └── ...                # Other assets
└── favicon.ico            # Favicon
```

### Desktop Application (Tauri)

```bash
# Build desktop installer
npm run tauri:build

# This will:
# 1. Build React app (npm run build)
# 2. Compile Rust backend
# 3. Create native installer
```

**Installer Locations:**
```
src-tauri/target/release/bundle/
├── msi/                   # Windows installer (.msi)
├── nsis/                  # Alternative Windows installer
├── deb/                   # Linux Debian package
├── appimage/              # Linux AppImage
└── dmg/                   # macOS disk image
```

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/              # React components
│   │   ├── ChatBox.jsx         # Main chat interface
│   │   ├── Message.jsx         # Individual message display
│   │   └── Sidebar.jsx         # Navigation sidebar
│   │
│   ├── services/               # API service layer
│   │   └── api.js             # Backend communication
│   │
│   ├── context/                # React Context
│   │   └── AppContext.jsx     # Global state management
│   │
│   ├── assets/                 # Static assets
│   │   ├── assets.js          # Asset exports
│   │   └── prism.css          # Code syntax highlighting
│   │
│   ├── App.jsx                 # Root component
│   ├── main.jsx                # Application entry point
│   └── index.css               # Global styles
│
├── src-tauri/                   # Tauri desktop wrapper
│   ├── src/
│   │   ├── main.rs            # Rust entry point
│   │   └── lib.rs             # Tauri commands (IPC)
│   │
│   ├── Cargo.toml             # Rust dependencies
│   ├── tauri.conf.json        # Tauri configuration
│   └── icons/                 # App icons
│
├── public/                      # Static files (served as-is)
│   └── favicon.ico
│
├── index.html                   # HTML template
├── package.json                 # Node.js dependencies
├── vite.config.js              # Vite configuration
├── eslint.config.js            # ESLint rules
├── tailwind.config.js          # Tailwind CSS config (if exists)
└── README.md                    # This file
```

---

## 🧩 Components

### ChatBox Component

**Location:** `src/components/ChatBox.jsx`

Main chat interface component.

**Features:**
- Message input and send functionality
- Real-time message display
- Loading state indicator
- Connection status display
- Auto-scroll to latest message
- Session management
- Clear chat functionality

**State:**
```javascript
const [messages, setMessages] = useState([])      // Chat messages array
const [inputMessage, setInputMessage] = useState('') // Current input
const [isLoading, setIsLoading] = useState(false)   // Loading state
const [sessionId, setSessionId] = useState('default') // Session ID
const [isConnected, setIsConnected] = useState(false) // API status
const [isTauriMode, setIsTauriMode] = useState(false) // Desktop mode
```

**Key Functions:**
- `sendMessage()` - Send message to backend
- `loadChatHistory()` - Load existing messages
- `checkApiConnection()` - Verify backend health
- `clearChat()` - Delete session and clear UI

### Message Component

**Location:** `src/components/Message.jsx`

Individual message display component.

**Props:**
```javascript
{
  message: {
    id: number,
    type: 'user' | 'ai',
    message: string,
    timestamp: string
  }
}
```

**Features:**
- Different styling for user vs AI messages
- Avatar icons (👤 for user, 🤖 for AI)
- Timestamp display
- Responsive layout

### Sidebar Component

**Location:** `src/components/Sidebar.jsx`

Navigation sidebar (if implemented).

---

## 📡 API Integration

### API Service Layer

**Location:** `src/services/api.js`

Abstracts backend communication with automatic mode detection.

#### Key Functions

**1. Send Chat Message**
```javascript
import { sendChatMessage } from '../services/api'

const response = await sendChatMessage('Hello AI!', 'session_123')
// Returns: { success, user_message, ai_response, session_id }
```

**2. Get Chat History**
```javascript
import { getChatHistory } from '../services/api'

const history = await getChatHistory('session_123')
// Returns: { success, messages: [...], session_id }
```

**3. Check API Health**
```javascript
import { checkApiHealth } from '../services/api'

const isHealthy = await checkApiHealth()
// Returns: boolean
```

**4. Clear Session**
```javascript
import { clearChatSession } from '../services/api'

await clearChatSession('session_123')
// Deletes session and all messages from database
```

**5. Check Tauri Mode**
```javascript
import { isTauri } from '../services/api'

const isDesktop = isTauri()
// Returns: true if running in Tauri desktop app
```

### Mode Detection

The API service automatically detects the runtime environment:

```javascript
// Web Mode (Browser)
fetch('http://localhost:8000/api/chat', { ... })

// Tauri Mode (Desktop App)
invoke('send_chat_message', { message, sessionId })
```

### Configuration

**API Base URL:** `src/services/api.js`
```javascript
const API_BASE_URL = 'http://localhost:8000/api'
```

**CORS:** Backend must allow frontend origin:
```python
# backend/app.py
allow_origins=["http://localhost:5173", ...]
```

---

## 🖥️ Tauri Desktop

### Setup Tauri

**1. Install Rust**
```bash
# Download and install from: https://rustup.rs/
# Or use this command:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify installation
rustc --version
cargo --version
```

**2. Install Tauri Dependencies**
```bash
# Already included in package.json
npm install
```

### Development Mode

```bash
# Run desktop app with hot reload
npm run tauri:dev
```

**What happens:**
1. Starts Vite dev server (port 5173)
2. Compiles Rust backend
3. Opens native window with React app
4. Hot reload works for both React and Rust code

**Window should show:** `🟢 Connected to AI Local Model (Tauri Desktop)`

### Tauri Commands (IPC)

**Location:** `src-tauri/src/lib.rs`

Rust functions callable from JavaScript:

```rust
#[tauri::command]
async fn send_chat_message(message: String, session_id: String) -> Result<String, String>

#[tauri::command]
async fn get_chat_history(session_id: String) -> Result<String, String>

#[tauri::command]
async fn check_api_health() -> Result<String, String>
```

**Called from React:**
```javascript
import { invoke } from '@tauri-apps/api/core'

const response = await invoke('send_chat_message', {
  message: 'Hello!',
  sessionId: 'default'
})
```

### Building Installer

```bash
# Create production installer
npm run tauri:build

# Find installer at:
# src-tauri/target/release/bundle/msi/ai-chat-assistant_1.0.0_x64_en-US.msi
```

**Installer includes:**
- React frontend (bundled)
- Rust backend (compiled)
- All dependencies
- Application icon
- Auto-updater (if configured)

### Tauri Configuration

**Location:** `src-tauri/tauri.conf.json`

```json
{
  "build": {
    "devPath": "http://localhost:5173",  // Vite dev server
    "distDir": "../dist"                 // Production build
  },
  "package": {
    "productName": "AI Chat Assistant",
    "version": "0.1.0"
  },
  "tauri": {
    "windows": [{
      "title": "AI Chat Assistant",
      "width": 1200,
      "height": 800,
      "resizable": true,
      "minimizable": true
    }],
    "security": {
      "csp": "default-src 'self'; connect-src http://localhost:8000 http://localhost:5173"
    }
  }
}
```

---

## 🔍 Troubleshooting

### Common Issues

**Issue: "Port 5173 already in use"**
```bash
# Vite will automatically try next port (5174, 5175, etc.)
# Or kill the process:

# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:5173 | xargs kill -9
```

**Issue: "Failed to fetch" error in console**
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Check CORS settings in backend/app.py
# Ensure http://localhost:5173 is allowed
```

**Issue: Blank page after npm run dev**
```bash
# Clear Vite cache
rm -rf node_modules/.vite

# Clear dist folder
rm -rf dist

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Try again
npm run dev
```

**Issue: Tauri compilation fails**
```bash
# Update Rust
rustup update

# Clean Rust build cache
cd src-tauri
cargo clean
cd ..

# Try again
npm run tauri:dev
```

**Issue: "invoke is not defined" in Tauri**
```bash
# Ensure @tauri-apps/api is installed
npm install @tauri-apps/api

# Import correctly
import { invoke } from '@tauri-apps/api/core'
```

**Issue: Hot reload not working**
```bash
# Restart dev server
# Press Ctrl+C, then:
npm run dev

# Check Vite config (vite.config.js)
# Ensure HMR is enabled
```

### Debug Mode

**Browser DevTools:**
```
Press F12 (Chrome/Edge/Firefox)
- Console: View logs and errors
- Network: Monitor API requests
- React DevTools: Inspect components
```

**Tauri DevTools:**
```
In desktop app, press:
- Windows/Linux: Ctrl + Shift + I
- macOS: Cmd + Option + I
```

**Verbose Logging:**
```javascript
// Add to src/services/api.js
console.log('API Request:', url, body)
console.log('API Response:', response)
```

---

## 📚 Dependencies

### Production Dependencies

```json
{
  "react": "^19.2.0",           // UI library
  "react-dom": "^19.2.0",       // React DOM renderer
  "react-router-dom": "^7.9.4", // Client-side routing
  "@tauri-apps/api": "^2.3.0"   // Tauri IPC (desktop mode)
}
```

### Development Dependencies

```json
{
  "vite": "^7.1.9",                    // Build tool
  "@vitejs/plugin-react": "^4.3.4",   // React plugin for Vite
  "tailwindcss": "^4.1.14",           // CSS framework
  "@tauri-apps/cli": "^2.8.5",        // Tauri CLI
  "eslint": "^9.20.0"                 // Code linting
}
```

---

## 🔗 Useful Resources

- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS Docs](https://tailwindcss.com/)
- [Tauri Documentation](https://tauri.app/)
- [React Router Docs](https://reactrouter.com/)

---

## 📄 Environment Variables

Create `.env` file for configuration:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api

# Feature Flags
VITE_ENABLE_TAURI=true
VITE_ENABLE_ANALYTICS=false

# Access in code:
import.meta.env.VITE_API_BASE_URL
```

---

**Frontend built with ⚡ Vite + ⚛️ React**