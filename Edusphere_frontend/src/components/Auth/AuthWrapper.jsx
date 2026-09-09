import React, { useState, useEffect } from 'react';
import Login from './Login';
import Signup from './Signup';
import { AuthContext } from './AuthContext';
import { GoogleOAuthProvider } from '@react-oauth/google';

const AuthWrapper = ({ onAuthSuccess, children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if user is already logged in (from localStorage)
    const savedUser = localStorage.getItem('edusphere_user');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
      setIsAuthenticated(true);
      onAuthSuccess(userData.user_id, userData.name);
    }
  }, []);

  const handleLogin = (userId, name) => {
    const userData = { user_id: userId, name: name };
    setUser(userData);
    setIsAuthenticated(true);
    localStorage.setItem('edusphere_user', JSON.stringify(userData));
    onAuthSuccess(userId, name);
  };

  const handleSignup = (userId, name) => {
    const userData = { user_id: userId, name: name };
    setUser(userData);
    setIsAuthenticated(true);
    localStorage.setItem('edusphere_user', JSON.stringify(userData));
    onAuthSuccess(userId, name);
  };

  const handleLogout = () => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('edusphere_user');
    localStorage.removeItem('chats');
    localStorage.removeItem('conversations');
    localStorage.removeItem('selectedChatIndex');
    localStorage.removeItem('chatFeedback');
  };

  if (isAuthenticated) {
    return (
      <AuthContext.Provider value={{ user, logout: handleLogout }}>
        {children}
      </AuthContext.Provider>
    );
  }

  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || "YOUR_GOOGLE_CLIENT_ID"}>
      <div>
        {showSignup ? (
          <Signup 
            onSignup={handleSignup}
            onSwitchToLogin={() => setShowSignup(false)}
          />
        ) : (
          <Login 
            onLogin={handleLogin}
            onSwitchToSignup={() => setShowSignup(true)}
          />
        )}
      </div>
    </GoogleOAuthProvider>
  );
};

export default AuthWrapper;