import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import './Feedback.css'; // Reuse the same CSS file

export default function FeedbackForm() {
  const { feedbackType } = useParams(); // Get the feedback type from the URL
  const navigate = useNavigate();
  const [feedbackText, setFeedbackText] = useState('');
  const [error, setError] = useState(''); // State to store error message

  // Utility function to capitalize the first letter of each word
  const capitalizeWords = (text) => {
    return text
      .split('-') // Split the string by dashes
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1)) // Capitalize the first letter of each word
      .join(' '); // Join the words with spaces
  };

  // Determine the text to display above the textarea based on the feedback type
  const getPromptText = () => {
    switch (feedbackType) {
      case 'give-feedback':
        return 'Tell us about your opinion (the more details you include, the better!)';
      case 'suggest-an-idea':
        return 'Tell us about your idea (the more details you include, the better!)';
      case 'report-an-issue':
        return 'Tell us about the issue you experienced (the more details you include, the better!)';
      case 'something-else':
        return 'Tell us about your feedback (the more details you include, the better!)';
      default:
        return 'Please provide your feedback below.';
    }
  };

  const handleInputChange = (e) => {
    const textarea = e.target;
    textarea.style.height = 'auto'; // Reset the height
    textarea.style.height = `${textarea.scrollHeight}px`; // Set the height to match the content
    setFeedbackText(textarea.value); // Update the feedback text state
  };

  const handleNextClick = () => {
    if (!feedbackText.trim()) {
      setError('Please provide your feedback before proceeding.');
      return;
    }

    setError(''); // Clear error if feedback is valid
    navigate('/feedback-email', { state: { feedbackType, feedbackText } }); // Pass feedback data to the next page
  };

  return (
    <div className="feedback-container">
      <div className="feedback-box">
        <h1 className="feedback-title">{capitalizeWords(feedbackType)}</h1>
        <p className="feedback-prompt">{getPromptText()}</p>
        <textarea
          className="feedback-textarea"
          placeholder="Write your feedback here..."
          value={feedbackText}
          onChange={handleInputChange} // Call the dynamic height adjustment function
        />
        {error && <p className="feedback-error">{error}</p>} {/* Display error message */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <button
            onClick={handleNextClick}
            className="feedback-next-button"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}