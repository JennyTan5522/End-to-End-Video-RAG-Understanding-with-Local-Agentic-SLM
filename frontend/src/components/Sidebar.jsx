import React, { useState } from 'react'
import { useAppContext } from '../context/AppContext' 

const Sidebar = () => {
    // Get context values for managing chats and user data
    const { chats, setSelectedChat, user } = useAppContext()

    // State for search functionality
    const [search, setSearch] = useState('')
    
    return (
        <div className='flex flex-col h-screen min-w-72 p-5 dark:bg-gradient-to-b from-[#242124]/30 to-[#000000]/30 border-r border-[#80609F]/30 backdrop-blur-3xl transition-all duration-500 max-md:absolute left-0 z-10'>
            {/* Header Section */}
            <div className='mb-6'>
                <div className='flex items-center gap-3 mb-4'>
                    <span className='text-2xl'>🤖</span>
                    <h2 className='text-xl font-semibold text-gray-800 dark:text-white'>
                        AI Video Assistant
                    </h2>
                </div>
                <div className='relative group'>
                    <button 
                        className='mt-2 w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 hover:scale-105 hover:shadow-lg'
                        title="Click to upload your video files"
                    >
                        <span className='text-sm'>📁</span>
                        Upload File
                    </button>
                    {/* Hover Tooltip */}
                    <div className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none whitespace-nowrap'>
                        Upload video files for AI analysis
                        <div className='absolute top-full left-1/2 transform -translate-x-1/2 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900'></div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Sidebar
