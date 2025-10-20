// Service to communicate with FastAPI backend via Tauri
import { invoke } from '@tauri-apps/api/core';

const API_BASE_URL=import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
console.log('🔗 API Base URL:', API_BASE_URL); 

// Check if running in Tauri
export const isTauri = () => {
  return '__TAURI__' in window;
};

/**
 * Send a chat message to the AI
 * @param {string} message - The user's message
 * @param {string} sessionId - The session identifier
 * @returns {Promise<Object>} The API response
 */
export async function sendChatMessage(message, sessionId = 'default') {
  try {
    if (isTauri()) {
      // Use Tauri IPC (more secure)
      const response = await invoke('send_chat_message', {
        message,
        sessionId
      });
      return JSON.parse(response);
    } else {
      // Fallback to direct HTTP (web mode)
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: sessionId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    }
  } catch (error) {
    console.error('Failed to send message:', error);
    throw error;
  }
}

/**
 * Get chat history for a session
 * @param {string} sessionId - The session identifier
 * @returns {Promise<Object>} The chat history
 */
export async function getChatHistory(sessionId = 'default') {
  try {
    if (isTauri()) {
      // Use Tauri IPC
      const response = await invoke('get_chat_history', { sessionId });
      return JSON.parse(response);
    } else {
      // Fallback to direct HTTP
      const response = await fetch(`${API_BASE_URL}/chat/${sessionId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    }
  } catch (error) {
    console.error('Failed to get chat history:', error);
    throw error;
  }
}

/**
 * Check if the FastAPI backend is healthy
 * @returns {Promise<boolean>} True if healthy
 */
export async function checkApiHealth() {
  try {
    if (isTauri()) {
      // Use Tauri IPC
      const response = await invoke('check_api_health');
      const data = JSON.parse(response);
      return data.status === 'healthy';
    } else {
      // Fallback to direct HTTP
      const response = await fetch(`${API_BASE_URL}/health`);
      
      if (!response.ok) {
        return false;
      }
      
      const data = await response.json();
      return data.status === 'healthy';
    }
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
}

/**
 * Clear a chat session
 * @param {string} sessionId - The session identifier
 * @returns {Promise<Object>} The API response
 */
export async function clearChatSession(sessionId = 'default') {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/${sessionId}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to clear session:', error);
    throw error;
  }
}

/**
 * Upload a file to the backend
 * @param {File} file - The file to upload
 * @param {string} sessionId - The session identifier
 * @returns {Promise<Object>} The upload response
 */
export async function uploadFile(file, sessionId = 'default') {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/upload?session_id=${sessionId}`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to upload file:', error);
    throw error;
  }
}

/**
 * Get list of uploaded files for a session
 * @param {string} sessionId - The session identifier
 * @returns {Promise<Object>} The files list
 */
export async function getUploadedFiles(sessionId = 'default') {
  try {
    const response = await fetch(`${API_BASE_URL}/files/${sessionId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to get uploaded files:', error);
    throw error;
  }
}

/**
 * Delete an uploaded file
 * @param {number} fileId - The file ID to delete
 * @returns {Promise<Object>} The delete response
 */
export async function deleteFile(fileId) {
  try {
    const response = await fetch(`${API_BASE_URL}/files/${fileId}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to delete file:', error);
    throw error;
  }
}

/**
 * Get workflow processing status
 * @param {string} workflowId - The workflow ID
 * @returns {Promise<Object>} The workflow status
 */
export async function getWorkflowStatus(workflowId) {
  try {
    const response = await fetch(`${API_BASE_URL}/workflow/${workflowId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to get workflow status:', error);
    throw error;
  }
}

export default {
  sendChatMessage,
  getChatHistory,
  checkApiHealth,
  clearChatSession,
  uploadFile,
  getUploadedFiles,
  deleteFile,
  getWorkflowStatus,
  isTauri
};
