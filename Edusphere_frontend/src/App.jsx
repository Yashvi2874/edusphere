import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './components/MainLayout';
import AuthWrapper from './components/Auth/AuthWrapper';
import Feedback from './components/Feedback/Feedback';
import FeedbackForm from './components/Feedback/FeedbackForm';
import FeedbackRating from './components/Feedback/FeedbackRating';
import FeedbackEmail from './components/Feedback/FeedbackEmail';
import ThankYou from './components/Feedback/ThankYou';
import Terms from './components/ChatBox/Terms'; // Import the Terms component
import { GoogleOAuthProvider } from '@react-oauth/google';
import './App.css';

const App = () => {
  const [user, setUser] = useState(null);

  const handleAuthSuccess = (userId, userName) => {
    setUser({ userId, userName });
  };

  return (
    <div className="App">
      <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || "YOUR_GOOGLE_CLIENT_ID"}>
        <BrowserRouter>
          <AuthWrapper onAuthSuccess={handleAuthSuccess}>
            <Routes>
              <Route path="/" element={<MainLayout userId={user?.userId} userName={user?.userName} />} />
              <Route path="/feedback" element={<Feedback />} />
              <Route path="/feedback-rating/:feedbackType" element={<FeedbackRating />} />
              <Route path="/feedback-form/:feedbackType" element={<FeedbackForm />} />
              <Route path="/feedback-email" element={<FeedbackEmail />} />
              <Route path="/thank-you" element={<ThankYou />} />
              <Route path="/terms" element={<Terms />} />
            </Routes>
          </AuthWrapper>
        </BrowserRouter>
      </GoogleOAuthProvider>
    </div>
  );
};

export default App;