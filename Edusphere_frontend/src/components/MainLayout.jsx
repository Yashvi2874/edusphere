import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Sidebar from './Sidebar/Sidebar';
import ChatBox from './ChatBox/ChatBox';
import { askBot, createNewConversation, getChatHistory, deleteConversation } from '../api/chatbot';
import CollegeConnect from './CollegeConnect/CollegeConnect';
import './MainLayout.css';

//   // useEffect(() => {
//   //   fetch("http://localhost:5000/chatbot")
//   //     .then(res => {
//   //       if (!res.ok) {
//   //         throw new Error("Network response was not ok");
//   //       }
//   //       return res.json();  // This only works if Flask returns JSON
//   //     })
//   //     .then(data => {
//   //       console.log(data);
//   //     })
//   //     .catch(err => {
//   //       console.error("Fetch error:", err);
//   //     });
//   // }, []);  

//   return (
//     <div style={{ background: '#02242e' }}>
//       <div style={{ display: 'flex', height: '100vh' }}>
//         {/* Sidebar on the left */}
//         <div style={{ width: '20vw' }}>
//           <Sidebar onCategorySelect={handleCategorySelect} />
//         </div>
//         <div> {(typeof data.chatbot === 'undefined') ? (
//           <p>Loading...</p>) : (
//             data.chatbot.map((chatbot, i) => (
//               <p key={i}>{chatbot}</p>
//             ))
//           )}
//         </div>
//         {/* Chatbox on the right */}
//         <div style={{ flex: 1, padding: '10px' }}>
//           <ChatBox selectedCategory={selectedCategory} />
//         </div>
//       </div>
//     </div>
//   );
// }

const MainLayout = ({ userId, userName }) => {
  const [chats, setChats] = useState(() => {
    const storedChats = localStorage.getItem('chats');
    return storedChats ? JSON.parse(storedChats) : [];
  });
  const [selectedChatIndex, setSelectedChatIndex] = useState(() => {
    const storedIndex = localStorage.getItem('selectedChatIndex');
    return storedIndex ? parseInt(storedIndex, 10) : 0;
  });
  const [conversations, setConversations] = useState(() => {
    const storedConversations = localStorage.getItem('conversations');
    return storedConversations ? JSON.parse(storedConversations) : [];
  });

    const [selectedCategory, setSelectedCategory] = useState(null);
  // const [data, setData] = useState([{}]);

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    console.log(`Selected category updated to: ${category}`);
  };
  
  useEffect(() => {
    console.log(`Selected category: ${selectedCategory}`);
  }, [selectedCategory]);

  useEffect(() => {
    const ensureConversation = async () => {
      try {
        if (userId && conversations.length === 0) {
          await startNewConversation();
        }
      } catch (e) {
        console.error('Failed to start initial conversation:', e);
      }
    };
    ensureConversation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const currentConversationId = conversations[selectedChatIndex]?.conversationId;
        if (currentConversationId) {
          const data = await getChatHistory(userId, currentConversationId);

          const formattedData = data.map(chat => ({
            user: chat.user_message,
            bot: chat.bot_response,
            sources: chat.sources || [],
            messageId: chat.message_id
          }));

          const updatedChats = [...chats];
          updatedChats[selectedChatIndex] = formattedData;
          setChats(updatedChats);
          localStorage.setItem('chats', JSON.stringify(updatedChats)); // Store chats in localStorage
        }
      } catch (error) {
        console.error("Error fetching chat history:", error);
      }
    };

    fetchChatHistory();
  }, [userId, conversations, selectedChatIndex]);

  const handleSendMessage = async (message) => {
    const updatedChats = [...chats];

    if (!updatedChats[selectedChatIndex]) {
        updatedChats[selectedChatIndex] = [];
    }
    updatedChats[selectedChatIndex].push({ user: message });
    setChats([...updatedChats]);
    localStorage.setItem('chats', JSON.stringify(updatedChats)); // Store chats in localStorage

    const currentConversationId = conversations[selectedChatIndex]?.conversationId;

    if (!currentConversationId) {
        console.error("Conversation ID is missing!");
        return;
    }

    try {
        const response = await askBot(message, userId, currentConversationId);
        const botResponse = response[0]?.text || 'No response';
        const sources = response[0]?.sources || [];
        const messageId = response[0]?.message_id;
        
        updatedChats[selectedChatIndex].push({ 
          bot: botResponse,
          sources: sources,
          messageId: messageId
        });
        setChats([...updatedChats]);
        localStorage.setItem('chats', JSON.stringify(updatedChats)); // Store chats in localStorage

    } catch (error) {
        console.error('Error sending message:', error);
    }
  };

  const startNewConversation = async () => {
    try {
        const response = await createNewConversation(userId);
        const newConversationId = response.conversation_id;  // Save the conversation ID
        const newConversations = [...conversations, { conversationId: newConversationId }];
        setConversations(newConversations);  // Update the conversations state
        localStorage.setItem('conversations', JSON.stringify(newConversations));  // Store conversations in localStorage
        const newChats = [...chats, []]; // Add a new empty chat array
        setChats(newChats);
        localStorage.setItem('chats', JSON.stringify(newChats)); // Store chats in localStorage
        const newIndex = newConversations.length - 1;
        setSelectedChatIndex(newIndex); // Select the new conversation
        localStorage.setItem('selectedChatIndex', newIndex); // Store selectedChatIndex in localStorage
        console.log('New conversation started:', newConversationId);
    } catch (error) {
        console.error('Error starting a new conversation:', error);
    }
  };

  const deleteConversationHandler = async (index) => {
    const conversationId = conversations[index]?.conversationId;

    if (!conversationId) {
        console.error("Conversation ID is missing!");
        return;
    }

    try {
        await deleteConversation(userId, conversationId);

        const newConversations = conversations.filter((_, i) => i !== index);
        const newChats = chats.filter((_, i) => i !== index);

        setConversations(newConversations);
        setChats(newChats);

        localStorage.setItem('conversations', JSON.stringify(newConversations));
        localStorage.setItem('chats', JSON.stringify(newChats));

        if (selectedChatIndex >= newConversations.length) {
            setSelectedChatIndex(newConversations.length - 1);
            localStorage.setItem('selectedChatIndex', newConversations.length - 1);
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
    }
  };

  const selectChat = (index) => {
    setSelectedChatIndex(index);
    localStorage.setItem('selectedChatIndex', index); // Store selectedChatIndex in localStorage
  };

  return (
    <div className="main-layout-container">
      <div className="main-layout-flex">
        {/* Sidebar on the left */}
        <div className="main-layout-sidebar">
          <Sidebar 
            onCategorySelect={handleCategorySelect} 
            chats={chats}
            selectChat={selectChat}
            startNewConversation={startNewConversation}
            deleteConversation={deleteConversationHandler}
            selectedChatIndex={selectedChatIndex}
            activeCategory={selectedCategory}
        />
        </div>
        {/* <div> {(typeof data.chatbot === 'undefined') ? (
          <p>Loading...</p>) : (
            data.chatbot.map((chatbot, i) => (
              <p key={i}>{chatbot}</p>
            ))
          )}
        </div> */}
        {/* Chatbox on the right */}
        <div className="main-layout-chatbox animate-fade">
          {selectedCategory === 'College Connect' ? (
            <CollegeConnect />
          ) : (
            <ChatBox 
                selectedCategory={selectedCategory} 
                chat={chats[selectedChatIndex] || []}
                onSendMessage={handleSendMessage}
                conversationId={conversations[selectedChatIndex]?.conversationId}
            />
          )}
        </div>
      </div>
    </div>  
  );
};

export default MainLayout;