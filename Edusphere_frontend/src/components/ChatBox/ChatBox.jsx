import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './ChatBox.css';
import ResultSources from '../ResultSources';
import FAQ from './FAQ';
import { AiFillLike, AiFillDislike } from 'react-icons/ai';
import { submitFeedback } from '../../api/chatbot';

const ChatBox = ({ chat = [], onSendMessage, conversationId, selectedCategory }) => {
  const [message, setMessage] = useState('');
  const [feedback, setFeedback] = useState({});
  const [notification, setNotification] = useState(''); // State for feedback notification
  const [showPopup, setShowPopup] = useState(false); // State to show/hide popup
  const [dislikeReason, setDislikeReason] = useState(''); // State for dislike reason
  const [currentDislikeMessageId, setCurrentDislikeMessageId] = useState(null); // Track which message is disliked
  const messagesEndRef = useRef(null);
  // const userId = "user124"; // Replace with actual user ID logic

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!conversationId) {
      console.error('Conversation ID is missing!');
      return;
    }
    if (message.trim()) {
      onSendMessage(message);
      setMessage('');
    }
  };
  //   if (!message.trim() || !conversationId) return;
  
  //   try {

  //     setResponses((prev) => [...prev, { from: 'user', text: message }]);

  //     const response = await fetch('http://localhost:5001/chat', {
  //       method: 'POST',
  //       headers: { 'Content-Type': 'application/json' },
  //       body: JSON.stringify({
  //         message,
  //         user_id: userId, // or dynamic user ID
  //         conversation_id: conversationId
  //       }),
  //     });
      
  //   if (!response.ok) {
  //     console.error("Failed to get response from server");
  //     return;
  //   }
  
  //     const data = await response.json();
  //     const botMessage = data[0]?.text || "No response";
  
  //     setResponses((prev) => [...prev, { from: 'bot', text: botMessage }]);
  //   onSendMessage(message); // Update parent if needed
  //   setMessage(''); // Clear input
  // } catch (err) {
  //   console.error("Error while sending chat message:", err);
  // }

  // };  

  const handleFaqClick = async (faq) => {
  
    if (faq.trim()) {
      onSendMessage(faq);
      setMessage('');  // Optional: clear the input if needed
    }
  };
//   const handleFaqClick = async (faq) => {
//   // Show user's FAQ click immediately
//   setResponses((prev) => [...prev, { from: 'user', text: faq }]);

//   try {
//     const response = await fetch('http://localhost:5001/chat', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({
//         message: faq,
//         user_id: userId,
//         conversation_id: conversationId,
//       }),
//     });

//     if (!response.ok) {
//       console.error("Failed to get response from server");
//       return;
//     }

//     const data = await response.json();
//     const botMessage = data[0]?.text || "No response";

//     setResponses((prev) => [...prev, { from: 'bot', text: botMessage }]);
//   } catch (err) {
//     console.error("Error while handling FAQ:", err);
//   }
// };

const handleFeedback = async (messageId, type) => {
  console.log('Feedback clicked:', { messageId, type, messageIdType: typeof messageId }); // Debug log
  
  // Ensure we have a valid message ID
  if (!messageId || messageId === undefined) {
    console.error('No message ID provided for feedback');
    setNotification('❌ Error: No message ID');
    setTimeout(() => setNotification(''), 2000);
    return;
  }
  
  // Convert to string if it's a number (fallback case)
  const messageIdStr = String(messageId);
  
  if (type === 'dislike') {
    // Show the popup for dislike feedback
    setCurrentDislikeMessageId(messageIdStr);
    setShowPopup(true);
  } else {
    // Handle like feedback
    try {
      // Send like feedback to the backend
      await submitFeedback(messageIdStr, 'like');

      // Update feedback state
      setFeedback((prev) => {
        const updatedFeedback = {
          ...prev,
          [messageIdStr]: type,
        };
        return updatedFeedback;
      });

      // Show feedback notification
      setNotification('Feedback sent successfully!');
      setTimeout(() => setNotification(''), 2000);
    } catch (error) {
      console.error('Error sending like feedback:', error);
      setNotification('❌ Failed to send feedback');
      setTimeout(() => setNotification(''), 2000);
    }
  }
};

const handleDislikeSubmit = async () => {
  if (!dislikeReason.trim()) {
    alert('Please provide a reason for your dislike.');
    return;
  }

  if (!currentDislikeMessageId) {
    console.error('No message ID for dislike feedback');
    setNotification('❌ Error: No message ID');
    setTimeout(() => setNotification(''), 2000);
    return;
  }

  // Send dislike feedback to the backend
  try {
    await submitFeedback(currentDislikeMessageId, 'dislike', dislikeReason);

    // Update feedback state
    setFeedback((prev) => {
      const updatedFeedback = {
        ...prev,
        [currentDislikeMessageId]: 'dislike',
      };
      return updatedFeedback;
    });

    // Close the popup and reset the reason
    setShowPopup(false);
    setDislikeReason('');
    setNotification('Feedback sent successfully');
    setTimeout(() => setNotification(''), 2000);
  } catch (error) {
    console.error('Error sending feedback:', error);
    setNotification('❌ Failed to send feedback');
    setTimeout(() => setNotification(''), 2000);
  }
};

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    const messagesContainer = document.querySelector('.chatbox-messages');
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }, [chat]);

  // Also use the ref for smooth scrolling
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chat]);

  return (
    <div className="chatbox">
      <div className="chatbox-tabs">
        {/* Chat Tab */}
        <div className="chatbox-tab chat">
          <h2 className="chatbox-tab-heading">AI Virtual Assistant</h2>

          {/* Feedback Notification */}
          {notification && <div className="feedback-notification">{notification}</div>}

          <div className="chatbox-messages">
            {chat.map((msg, index) => (
              <div key={index} className="message-container">
                {msg.user && (
                  <div className="message user-message">
                    <p>
                      <strong>You:</strong> {msg.user}
                    </p>
                  </div>
                )}
                {msg.bot && (
                  <>
                    <div className="message ai-message markdown-body">
                      <div className="markdown-content-wrapper">
                        <strong style={{ display: 'block', marginBottom: '8px', color: '#9fd0dc' }}>Edusphere:</strong>
                        <ReactMarkdown>{msg.bot}</ReactMarkdown>
                      </div>
                    </div>
                    {/* ratings */}
                    <div className="message-ratings-container">
                      <div
                        className={`message-ratings ${
                          feedback[msg.messageId || index] === 'like' ? 'message-ratings-selected' : ''
                        }`}
                      >
                        <AiFillLike
                          className={`message-rating-button like-button ${
                            feedback[msg.messageId || index] === 'like' ? 'active' : ''
                          }`}
                          size={20}
                          color={feedback[msg.messageId || index] === 'like' ? '#4c8898' : '#173138'}
                          onClick={() => {
                            console.log('Like button clicked for message:', { msg, messageId: msg.messageId, index });
                            handleFeedback(msg.messageId || index, 'like');
                          }}
                        />
                      </div>
                      <div
                        className={`message-ratings ${
                          feedback[msg.messageId || index] === 'dislike' ? 'message-ratings-selected' : ''
                        }`}
                      >
                        <AiFillDislike
                          className={`message-rating-button dislike-button ${
                            feedback[msg.messageId || index] === 'dislike' ? 'active' : ''
                          }`}
                          size={20}
                          color={feedback[msg.messageId || index] === 'dislike' ? '#4c8898' : '#173138'}
                          onClick={() => {
                            console.log('Dislike button clicked for message:', { msg, messageId: msg.messageId, index });
                            handleFeedback(msg.messageId || index, 'dislike');
                          }}
                        />
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* FAQ above input */}
          <div className="faq-section">
            <FAQ category={selectedCategory} onFaqClick={handleFaqClick} listOnly={true} />
          </div>

          {/* fixed input - stays visible */}
          <form className="chatbox-input-container" onSubmit={handleSubmit}>
            <input
              type="text"
              value={message}
              className="chatbox-input"
              onChange={(e) => setMessage(e.target.value)}
              placeholder="How can I help you?"
            />
            <button type="submit" className="chatbox-send">
              ➤
            </button>
          </form>

          {/* Info box below input */}
          <div className="info-box">
            <p>
              ⓘ The responses may contain inaccurate information, so please double-check.{" "}
              <span
                className="terms-link"
                onClick={() => window.location.assign('/terms')}
              >
                Terms 🠦
              </span>
            </p>
          </div>
        </div>

        {/* Right tab - Sources (sibling of Chat tab) */}
        <div className="chatbox-tab sources">
          <h2 className="chatbox-tab-heading">Sources</h2>
          <div className="chatbox-result-sources">
            {chat.length > 0 && <ResultSources sources={chat[chat.length - 1].sources} />}
          </div>
        </div>
      </div>

      {/* Dislike Feedback Popup */}
      {showPopup && (
        <div className="popup-overlay">
          <div className="popup">
            <h3>How can we improve?</h3>
            <textarea
              value={dislikeReason}
              onChange={(e) => setDislikeReason(e.target.value)}
              placeholder="Type your feedback here..."
            />
            <button onClick={handleDislikeSubmit}>Submit</button>
            <button onClick={() => setShowPopup(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatBox;
