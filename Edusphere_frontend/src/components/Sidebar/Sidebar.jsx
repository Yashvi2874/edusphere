import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaTrash, FaBars, FaTimes, FaUserCircle, FaSignOutAlt } from 'react-icons/fa';
import './Sidebar.css';
import { AuthContext } from '../Auth/AuthContext';

/**
 * Only views that actually render something belong here.
 *
 * Four of the five old links — Student Projects, Faculty Dashboards, Admissions
 * Info and TPO — called setSelectedCategory and a console.log, and nothing else.
 * Nothing was behind them. Dead navigation is worse than none: the first thing
 * anyone does in a demo is click it.
 *
 * College Connect stays because it is real: it loads mentors and events from
 * the API and renders them.
 */
const VIEWS = [
  { id: null, label: 'Assistant' },
  { id: 'College Connect', label: 'College Connect' },
];

const Sidebar = ({ chats, selectChat, deleteConversation, startNewConversation, selectedChatIndex, onCategorySelect, activeCategory }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
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
        <p className="sidebar-tagline">
          Ask about admissions, scholarships, fees and programmes. Every answer
          cites the page it came from.
        </p>

        <nav className="views" aria-label="Sections">
          {VIEWS.map((view) => (
            <button
              key={view.label}
              type="button"
              className={`view-link ${activeCategory === view.id ? 'active' : ''}`}
              aria-current={activeCategory === view.id ? 'page' : undefined}
              onClick={() => onCategorySelect(view.id)}
            >
              {view.label}
            </button>
          ))}
        </nav>

        <div className="bottom-actions">
          <div
            className="profile-wrap"
            onMouseEnter={() => setShowProfileMenu(true)}
            onMouseLeave={() => setShowProfileMenu(false)}
          >
            {/* First name only: the sidebar half is ~118px, and "Yashasvi Gupta"
                truncates to "Yashasvi..." there, which reads worse than just
                "Yashasvi". The full name is on the tooltip, and the ellipsis
                rule below still catches unusually long first names. */}
            <button className="profile-button" title={user?.name || 'Profile'}>
              <FaUserCircle size={18} className="profile-icon" />
              <span className="profile-name">
                {(user?.name || 'Profile').trim().split(/\s+/)[0]}
              </span>
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
          <button onClick={startNewConversation} className="new-button">
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
