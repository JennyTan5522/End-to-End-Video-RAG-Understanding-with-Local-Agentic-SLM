import React, { useState, useEffect, useRef } from 'react'
import Message from './Message'
import { 
  sendChatMessage, 
  getChatHistory, 
  checkApiHealth, 
  clearChatSession, 
  isTauri 
} from '../services/api'

const ChatBox = () => {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(() => {
    // Get session ID from localStorage or create new one
    let storedSessionId = localStorage.getItem('sessionId')
    if (!storedSessionId) {
      storedSessionId = `session_${Date.now()}`
      localStorage.setItem('sessionId', storedSessionId)
    }
    return storedSessionId
  })
  const [isConnected, setIsConnected] = useState(false)
  const [isTauriMode, setIsTauriMode] = useState(false)
  const messagesEndRef = useRef(null)
  
  // Auto-scroll to bottom when new messages are added
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  // Check API connection and load chat history on component mount
  useEffect(() => {
    setIsTauriMode(isTauri())
    checkApiConnection()
    loadChatHistory()
    
    // Listen for video upload events to reload chat
    const handleVideoUpload = (event) => {
      console.log('Video uploaded, reloading chat history...', event.detail)
      // Delay reload to allow backend to process and store messages
      setTimeout(() => {
        loadChatHistory()
      }, 1000)
    }
    
    window.addEventListener('videoUploaded', handleVideoUpload)
    
    // Cleanup listener on unmount
    return () => {
      window.removeEventListener('videoUploaded', handleVideoUpload)
    }
  }, [])
  
  const checkApiConnection = async () => {
    try {
      const isHealthy = await checkApiHealth()
      setIsConnected(isHealthy)
    } catch (error) {
      console.error('API connection failed:', error)
      setIsConnected(false)
    }
  }
  
  const loadChatHistory = async () => {
    try {
      const data = await getChatHistory(sessionId)
      if (data.success && data.messages) {
        setMessages(data.messages)
      }
    } catch (error) {
      console.error('Failed to load chat history:', error)
    }
  }
  
  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading || !isConnected) return
    
    setIsLoading(true)
    
    try {
      const data = await sendChatMessage(inputMessage, sessionId)
      
      if (data.success) {
        // Add both user message and AI response to the messages
        setMessages(prevMessages => [
          ...prevMessages,
          data.user_message,
          data.ai_response
        ])
        setInputMessage('') // Clear input field
      } else {
        console.error('API Error:', data.error)
        alert('Failed to send message. Please try again.')
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      alert('Failed to connect to AI. Please make sure the backend is running.')
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }
  
  const clearChat = async () => {
    try {
      // Delete session from database
      await clearChatSession(sessionId)
      
      // Clear UI
      setMessages([])
      
      // Generate new session ID for fresh start
      const newSessionId = `session_${Date.now()}`
      setSessionId(newSessionId)
      localStorage.setItem('sessionId', newSessionId)
      
      console.log('Chat cleared successfully')
    } catch (error) {
      console.error('Failed to clear chat:', error)
      // Still clear UI even if database delete fails
      setMessages([])
      const newSessionId = `session_${Date.now()}`
      setSessionId(newSessionId)
      localStorage.setItem('sessionId', newSessionId)
    }
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b bg-gray-50">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">💬 AI Chat Interface</h1>
            <p className="text-sm text-gray-600">
              {isConnected ? 
                <span className="text-green-600">
                  🟢 Connected to AI Local Model {isTauriMode && '(Tauri Desktop)'}
                </span> : 
                <span className="text-red-600">🔴 Disconnected - Start backend server</span>
              }
            </p>
          </div>
          <button 
            onClick={clearChat}
            className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded-lg"
          >
            Clear Chat
          </button>
        </div>
      </div>
      
      {/* Messages Area */}
      <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p>👋 Welcome to the Video & Speech Assistant AI chat!</p>
            <p className="text-sm mt-2">Start a conversation by typing a message below.</p>
            {!isConnected && (
              <div className="mt-4 p-3 bg-yellow-100 rounded-lg text-yellow-800">
                ⚠️ Backend not connected. Please run: <code>python backend/web/app.py</code>
              </div>
            )}
          </div>
        ) : (
          messages.map((message) => (
            <Message key={message.id} message={message} />
          ))
        )}
        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="flex items-center max-w-[70%]">
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm mr-2">
                🤖
              </div>
              <div className="px-4 py-2 bg-gray-100 rounded-lg">
                <p className="text-sm text-gray-600">AI is thinking...</p>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Area */}
      <div className="p-4 border-t bg-white">
        <div className="flex space-x-2">
          <input 
            type="text" 
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..." 
            className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading || !isConnected}
          />
          <button 
            onClick={sendMessage}
            disabled={isLoading || !inputMessage.trim() || !isConnected}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? '...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatBox
