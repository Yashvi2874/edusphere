import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Feedback.css';

export default function ThankYou() {
  const navigate = useNavigate();

  const handleBackToChat = () => {
    navigate('/');
  };

  const handleMoreFeedback = () => {
    navigate('/feedback');
  };

  return (
    <div className="feedback-container">
      <div className="feedback-box">
        <h1 className="feedback-title">Thank You!</h1>
        <p className="thank-you-prompt">
          We appreciate your feedback and will use it to improve our platform.
        </p>
        <div className="feedback-options" style={{ marginTop: '1rem' }}>
          <button className="feedback-option-button" onClick={handleBackToChat}>
            Back to Chat
          </button>
          <button className="feedback-option-button" onClick={handleMoreFeedback}>
            Give More Feedback
          </button>
        </div>
      </div>
    </div>
  );
}