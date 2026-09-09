import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Feedback.css'; // Import the CSS file

export default function Feedback() {
  const navigate = useNavigate();

  const handleOptionClick = (option) => {
    if (option === 'Give feedback') {
      navigate(`/feedback-rating/${option.toLowerCase().replace(/\s+/g, '-')}`); // Redirect to the rating page
    } else {
      navigate(`/feedback-form/${option.toLowerCase().replace(/\s+/g, '-')}`); // Redirect to the feedback form page
    }
  };

  return (
    <div className="feedback-container">
      <div className="feedback-box">
        <h1 className="feedback-title">Help us improve!</h1>
        <div className="feedback-options">
          <button
            onClick={() => handleOptionClick('Give feedback')}
            className="feedback-option-button"
          >
            Give feedback 💬
          </button>
          <button
            onClick={() => handleOptionClick('Suggest an idea')}
            className="feedback-option-button"
          >
            Suggest an idea 💡
          </button>
          <button
            onClick={() => handleOptionClick('Report an issue')}
            className="feedback-option-button"
          >
            Report an issue 🐞
          </button>
          <button
            onClick={() => handleOptionClick('Something else')}
            className="feedback-option-button"
          >
            Something else (please specify)
          </button>
        </div>
      </div>
    </div>
  );
}
