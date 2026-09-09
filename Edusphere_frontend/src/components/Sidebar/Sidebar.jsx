import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaTrash, FaBars, FaTimes, FaUserCircle, FaSignOutAlt } from 'react-icons/fa';
import './Sidebar.css';
import { AuthContext } from '../Auth/AuthContext';

const Sidebar = ({ chats, selectChat, deleteConversation, startNewConversation, selectedChatIndex, onCategorySelect, activeCategory}) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const { user, logout } = useContext(AuthContext);
  const categories = [
    'Student Projects',
    'Faculty Dashboards',
    'Admissions Info',
    'Training and Placement Office (TPO)',
    'College Connect',
  ];
  const navigate = useNavigate();

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleCategoryClick = (category) => {
    onCategorySelect(category);
  };

  const handleLogout = () => {
    setShowProfileMenu(false);
    logout();
  };

  return (
    <div className="relative">
      <button
        onClick={toggleSidebar}
        className="md:hidden p-2 bg-[#ECDFCC] text-gray-800 rounded hover:bg-[#e2d9cc] fixed top-4 right-4 z-50"
      >
        {isSidebarOpen ? <FaTimes /> : <FaBars />}
      </button>
      <div className={`sidebar glass-panel animate-slide w-2/3 sm:w-full h-full fixed md:relative md:block ${isSidebarOpen ? 'block' : 'hidden'}`}>
        <h2>EduSphere</h2>
        <div className="categories">
         {categories.map((cat, index) => (
          <div key={index} className='category'>
            <div 
              className={`category-header ${activeCategory === cat ? 'active' : ''}`}
              onClick={() => handleCategoryClick(cat)}
            >
              {cat}
            </div>
          </div>
        ))}
      </div>

        <div className="bottom-actions">
          <div style={{ position: 'relative' }} onMouseEnter={() => setShowProfileMenu(true)} onMouseLeave={() => setShowProfileMenu(false)}>
            <button className="profile-button">
              <FaUserCircle size={18} />
              {user?.name || 'Profile'}
            </button>
            {showProfileMenu && (
              <div className="profile-menu">
                <button onClick={handleLogout}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                    <FaSignOutAlt /> Logout
                  </span>
                </button>
              </div>
            )}
          </div>
          <button
            onClick={startNewConversation}
            className="new-button p-2 rounded hover:bg-[#1b3841]"
          >
            New Chat
          </button>
        </div>

        <button className="feedback-button" onClick={() => navigate('/feedback')}>
         Give Feedback
       </button>
      </div>
    </div>
  );
};

export default Sidebar;
