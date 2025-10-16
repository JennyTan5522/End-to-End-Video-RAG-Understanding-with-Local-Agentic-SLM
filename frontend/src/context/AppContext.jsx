import { createContext, useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { dummyChats, dummyUserData } from "../assets/assets";

// Create a context to share app state globally across components
const AppContext = createContext()

// Context Provider component that wraps the entire app
export const AppContextProvider = ({children}) => {
    const navigate = useNavigate()

    // State Management: Core application states
    const [user, setUser] = useState(null);
    const [chats, setChats] = useState([]); // Array of all user's chat conversations
    const [selectedChat, setSelectedChat] = useState(null); // Currently active/selected chat

    // Function to simulate fetching user data from API
    const fetchUser = async () => {
        setUser(dummyUserData)
    }

    // Function to simulate fetching user's chat conversations from API
    const fetchUsersChats = async () => {
        setChats(dummyChats)
    }

    useEffect(() => {
        if (user){
            fetchUsersChats()
        }
        else{
            setChats([])
            setSelectedChat(null)
        }
    }, [user])

    useEffect(()=> {
        fetchUser()
    }, [])

    const value = {
        navigate,
        user,
        chats,
        selectedChat,
        setUser,
        setChats,
        setSelectedChat
    }

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    )
}

export const useAppContext = () => useContext(AppContext)