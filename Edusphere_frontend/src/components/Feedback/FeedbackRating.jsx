import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import './Feedback.css'; // Reuse the same CSS file

export default function FeedbackRating() {
  const { feedbackType } = useParams(); // Get the feedback type from the URL
  const navigate = useNavigate();
  const [rating, setRating] = useState(null); // State to store the selected rating

  const handleNextClick = () => {
    if (rating === null) {
      alert('Please select a rating before proceeding.');
      return;
    }

    if (rating < 3) {
      // Redirect to the feedback form page if the rating is below 4
      navigate(`/feedback-form/${feedbackType}`);
    } else {
      // Redirect to the Thank You page if the rating is 4 or 5
      navigate('/thank-you');
    }
  };

  return (
    <div className="feedback-container">
      <div className="feedback-box">
        <h1 className="feedback-title">How would you rate your experience?</h1>
        <div className="rating-options">
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              key={value}
              className={`rating-button ${rating === value ? 'selected' : ''}`}
              onClick={() => setRating(value)}
            >
              {value}
            </button>
          ))}
        </div>
        <div className="rating-messages-inline">
          <span className="rating-message">Awful, I hate it</span>
          <span className="rating-message">Great, I love it</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <button onClick={handleNextClick} className="feedback-next-button">
            Next
          </button>
        </div>
      </div>
    </div>
  );
}