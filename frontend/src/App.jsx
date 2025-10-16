import React from 'react'
import Sidebar from './components/Sidebar'
import ChatBox from './components/ChatBox'
import { Routes, Route } from 'react-router-dom'

const App = () => {
  return (
    <>
      <div className='flex h-screen w-screen'>
        <Sidebar />
        <Routes>
          {/* /: Defines the home path */}
          <Route path ='/' element ={<ChatBox />} />
        </Routes>
      </div>
    
    </>
  )
}

export default App
