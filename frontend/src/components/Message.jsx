import React from 'react'

const Message = ({ message }) => {
  const isAI = message.type === 'ai'
  
  return (
    <div className={`flex ${isAI ? 'justify-start' : 'justify-end'} mb-4`}>
      <div className={`flex max-w-[70%] ${isAI ? 'flex-row' : 'flex-row-reverse'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${isAI ? 'bg-blue-500 mr-2' : 'bg-gray-500 ml-2'}`}>
          {isAI ? '🤖' : '👤'}
        </div>
        
        {/* Message bubble */}
        <div className={`px-4 py-2 rounded-lg ${isAI ? 'bg-gray-100 text-gray-800' : 'bg-blue-500 text-white'}`}>
          <p className="text-sm leading-relaxed">{message.message}</p>
          {message.timestamp && (
            <p className={`text-xs mt-1 ${isAI ? 'text-gray-500' : 'text-blue-100'}`}>
              {new Date(message.timestamp).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default Message
