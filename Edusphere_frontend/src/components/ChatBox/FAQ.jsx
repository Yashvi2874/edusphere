import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom'; // Import useNavigate
import './ChatBox.css';
import { getFAQs } from '../../api/chatbot';

export default function FAQ({ category, onFaqClick, listOnly = false }) {
  const [faqList, setFaqList] = useState([]);
  const navigate = useNavigate(); // Initialize navigate

  useEffect(() => {
    const fetchFaqs = async () => {
      try {
        if (category) {
          const categoryKey = category.toLowerCase().replace(/\s+/g, '_');
          const data = await getFAQs(categoryKey);
          setFaqList(data.faqs || []);
        } else {
          const data = await getFAQs(); // defaults to 'generic'
          setFaqList(data.faqs || []);
        }
      } catch (error) {
        console.error('Error fetching FAQs:', error);
        setFaqList([]);
      }
    };

    fetchFaqs();
  }, [category]);

  return (
    <div className="faq-container">
      <div className="faq-list">
        {faqList.length > 0 ? (
          faqList.slice(0, 4).map((faq, index) => (
            <div
              key={index}
              className="faq-item"
              onClick={() => onFaqClick(faq)}
            >
              <span className="faq-text">{faq}</span>
              <span className="faq-arrow">→</span>
            </div>
          ))
        ) : (
          <div className="no-faqs">
            <p>📝 No FAQs available for this category.</p>
            <p>Try asking your own question above!</p>
          </div>
        )}
      </div>

      {!listOnly && (
        <div className="info-box">
          <p>
            ⓘ The responses may contain inaccurate information, so please double-check.{" "}
            <span
              className="terms-link"
              onClick={() => navigate('/terms')}
            >
              Terms 🠦
            </span>
          </p>
        </div>
      )}
    </div>
  );
}