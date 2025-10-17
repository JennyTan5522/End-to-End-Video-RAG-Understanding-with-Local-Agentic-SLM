import React, { useState, useRef } from 'react'
import { useAppContext } from '../context/AppContext' 
import { uploadFile, getUploadedFiles, deleteFile } from '../services/api'

const Sidebar = () => {
    // Get context values for managing chats and user data
    const { chats, setSelectedChat, user } = useAppContext()

    // State for search functionality
    const [search, setSearch] = useState('')
    const [uploadedFiles, setUploadedFiles] = useState([])
    const [isUploading, setIsUploading] = useState(false)
    const [uploadMessage, setUploadMessage] = useState('')
    const fileInputRef = useRef(null)
    
    // Load uploaded files on component mount
    React.useEffect(() => {
        loadUploadedFiles()
    }, [])
    
    const loadUploadedFiles = async () => {
        try {
            const sessionId = localStorage.getItem('sessionId') || 'default'
            const data = await getUploadedFiles(sessionId)
            if (data.success) {
                setUploadedFiles(data.files)
            }
        } catch (error) {
            console.error('Failed to load uploaded files:', error)
        }
    }
    
    const handleFileUpload = async (event) => {
        const file = event.target.files?.[0]
        if (!file) return
        
        // Validate file type on frontend
        const fileName = file.name.toLowerCase()
        if (!fileName.endsWith('.mp3') && !fileName.endsWith('.mp4')) {
            setUploadMessage('❌ Only MP3 and MP4 files are allowed')
            setTimeout(() => setUploadMessage(''), 3000)
            if (fileInputRef.current) {
                fileInputRef.current.value = ''
            }
            return
        }
        
        setIsUploading(true)
        setUploadMessage('')
        
        try {
            const sessionId = localStorage.getItem('sessionId') || 'default'
            const result = await uploadFile(file, sessionId)
            
            if (result.success) {
                setUploadMessage(`✅ ${result.message}`)
                // Reload the file list
                await loadUploadedFiles()
                // Clear file input
                if (fileInputRef.current) {
                    fileInputRef.current.value = ''
                }
                // Clear success message after 3 seconds
                setTimeout(() => setUploadMessage(''), 3000)
            }
        } catch (error) {
            console.error('Upload failed:', error)
            // Try to extract error message from response
            const errorMessage = error.message || 'Upload failed. Please try again.'
            setUploadMessage(`❌ ${errorMessage}`)
            setTimeout(() => setUploadMessage(''), 5000)
            // Clear file input
            if (fileInputRef.current) {
                fileInputRef.current.value = ''
            }
        } finally {
            setIsUploading(false)
        }
    }
    
    const triggerFileInput = () => {
        fileInputRef.current?.click()
    }
    
    const handleDeleteFile = async (fileId, filename) => {
        // Confirm deletion
        if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) {
            return
        }
        
        try {
            const result = await deleteFile(fileId)
            
            if (result.success) {
                setUploadMessage(`✅ ${result.message}`)
                // Reload the file list
                await loadUploadedFiles()
                // Clear message after 3 seconds
                setTimeout(() => setUploadMessage(''), 3000)
            }
        } catch (error) {
            console.error('Delete failed:', error)
            setUploadMessage('❌ Failed to delete file. Please try again.')
            setTimeout(() => setUploadMessage(''), 3000)
        }
    }
    
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
                    {/* Hidden file input */}
                    <input 
                        ref={fileInputRef}
                        type="file"
                        onChange={handleFileUpload}
                        className='hidden'
                        accept=".mp3,.mp4,audio/mp3,video/mp4"
                    />
                    <button 
                        onClick={triggerFileInput}
                        disabled={isUploading}
                        className='mt-2 w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 hover:scale-105 hover:shadow-lg disabled:cursor-not-allowed'
                        title="Click to upload your video files"
                    >
                        <span className='text-sm'>📁</span>
                        {isUploading ? 'Uploading...' : 'Upload File'}
                    </button>
                    {/* Hover Tooltip */}
                    <div className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none whitespace-nowrap'>
                        Upload MP3 or MP4 files only
                        <div className='absolute top-full left-1/2 transform -translate-x-1/2 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900'></div>
                    </div>
                </div>
                
                {/* Upload message */}
                {uploadMessage && (
                    <div className='mt-2 text-sm text-center p-2 rounded bg-gray-100 dark:bg-gray-800'>
                        {uploadMessage}
                    </div>
                )}
                
                {/* Uploaded files list */}
                {uploadedFiles.length > 0 && (
                    <div className='mt-4'>
                        <h3 className='text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2'>
                            📂 Uploaded Files ({uploadedFiles.length})
                        </h3>
                        <div className='max-h-48 overflow-y-auto space-y-2'>
                            {uploadedFiles.map((file) => {
                                const isMP4 = file.filename.toLowerCase().endsWith('.mp4')
                                const fileIcon = isMP4 ? '🎬' : '🎵'
                                return (
                                    <div 
                                        key={file.id}
                                        className='p-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-xs group hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors'
                                    >
                                        <div className='flex items-center justify-between gap-2'>
                                            <div className='flex-1 min-w-0'>
                                                <div className='font-medium text-gray-800 dark:text-white truncate flex items-center gap-1'>
                                                    <span>{fileIcon}</span>
                                                    <span className='truncate'>{file.filename}</span>
                                                </div>
                                                <div className='text-gray-500 dark:text-gray-400 flex justify-between mt-1'>
                                                    <span>{(file.file_size / 1024).toFixed(1)} KB</span>
                                                    <span>{new Date(file.uploaded_at).toLocaleDateString()}</span>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => handleDeleteFile(file.id, file.filename)}
                                                className='opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded'
                                                title='Delete file'
                                            >
                                                🗑️
                                            </button>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default Sidebar
