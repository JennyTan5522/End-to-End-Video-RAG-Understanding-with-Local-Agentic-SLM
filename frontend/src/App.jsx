import React from 'react'
import Sidebar from './components/Sidebar'
import ChatBox from './components/ChatBox'
import { Routes, Route } from 'react-router-dom'

const App = () => {
  return (
    <div className='flex h-screen w-screen overflow-hidden'>
      {/* Sidebar - Fixed width, left side */}
      <Sidebar />
      
      {/* Main content area - Takes remaining space */}
      <div className='flex-1 min-h-0 flex flex-col overflow-hidden'>
        <Routes>
          {/* /: Defines the home path */}
          <Route path='/' element={<ChatBox />} />
        </Routes>
      </div>
    </div>
  )
}

export default App
