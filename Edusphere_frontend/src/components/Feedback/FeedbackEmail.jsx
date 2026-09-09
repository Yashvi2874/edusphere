import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Feedback.css'; // Reuse the same CSS file

export default function FeedbackEmail() {
  const navigate = useNavigate();
  const location = useLocation();
  const { feedbackType, feedbackText } = location.state || {}; // Get feedback data from the previous page
  const [email, setEmail] = useState('');
  const [error, setError] = useState(''); // State to store error message

  const validateEmail = (email) => {
    // Regular expression to validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSubmit = () => {
    if (!email.trim()) {
      setError('Please provide your email address.');
      return;
    }
    if (!validateEmail(email)) {
      setError('Please enter a valid email address.');
      return;
    }
    setError(''); // Clear error if email is valid
    console.log('Feedback Type:', feedbackType);
    console.log('Feedback Text:', feedbackText);
    console.log('Email:', email);
    navigate('/thank-you'); // Redirect to the thank-you page
  };

  return (
    <div className="feedback-container">
      <div className="feedback-box">
        <h1 className="feedback-title">Your Email</h1>
        <p className="feedback-prompt">
          Please provide your email so we can follow up on your feedback if needed.
        </p>
        <input
          type="email"
          className="feedback-textarea"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        {error && <p className="feedback-error">{error}</p>} {/* Display error message */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <button
            onClick={handleSubmit}
            className="feedback-next-button"
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}