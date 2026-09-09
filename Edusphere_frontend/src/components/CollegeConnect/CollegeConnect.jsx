import React, { useState, useEffect } from 'react';
import './CollegeConnect.css';
import { FaUserGraduate, FaCalendarAlt, FaEnvelope } from 'react-icons/fa';

const CollegeConnect = () => {
  const [mentors, setMentors] = useState({});
  const [events, setEvents] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [mentorsRes, eventsRes] = await Promise.all([
          fetch('http://localhost:5001/mentors'),
          fetch('http://localhost:5001/events')
        ]);
        
        const mentorsData = await mentorsRes.json();
        const eventsData = await eventsRes.json();
        
        setMentors(mentorsData);
        setEvents(eventsData);
      } catch (error) {
        console.error('Error fetching College Connect data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div className="loading">Loading Community Hub...</div>;

  return (
    <div className="college-connect">
      <h2 className="section-title">College Connect Hub</h2>
      
      <div className="connect-grid">
        <section className="connect-section">
          <h3><FaUserGraduate /> Find a Mentor</h3>
          <div className="mentor-list">
            {Object.entries(mentors).map(([id, mentor]) => (
              <div key={id} className="mentor-card">
                <h4>{mentor.name}</h4>
                <p className="subject">{mentor.subject}</p>
                <a href={`mailto:${mentor.email}`} className="contact-btn">
                  <FaEnvelope /> Contact
                </a>
              </div>
            ))}
          </div>
        </section>

        <section className="connect-section">
          <h3><FaCalendarAlt /> Upcoming Events</h3>
          <div className="event-list">
            {Object.entries(events).map(([id, event]) => (
              <div key={id} className="event-card">
                <div className="event-date">{new Date(event.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
                <div className="event-info">
                  <h4>{event.title}</h4>
                  <p>{event.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default CollegeConnect;
