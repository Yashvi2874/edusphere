import React, { useState } from 'react';
import { login } from '../../api/chatbot';
import { useGoogleLogin } from '@react-oauth/google';
import axios from 'axios';
import './Auth.css';

/**
 * Whether Google sign-in is actually usable.
 *
 * The client id defaults to the literal string "YOUR_GOOGLE_CLIENT_ID" when the
 * environment variable is unset, which Google rejects - so the button appears
 * and then fails with nothing to explain why. Treat the placeholder, and an
 * empty value, as "not configured".
 */
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const hasGoogleAuth = Boolean(
  GOOGLE_CLIENT_ID &&
  GOOGLE_CLIENT_ID !== 'YOUR_GOOGLE_CLIENT_ID' &&
  GOOGLE_CLIENT_ID.endsWith('.apps.googleusercontent.com')
);

const Login = ({ onLogin, onSwitchToSignup }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await login(formData.email, formData.password);
      if (response.success) {
        onLogin(response.user_id, response.name);
      } else {
        setError(response.message || 'Login failed. Please try again.');
      }
    } catch (error) {
      console.error('Login error:', error);
      if (error.response && error.response.data && error.response.data.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        // Get user info from Google
        const userInfo = await axios.get(
          'https://www.googleapis.com/oauth2/v3/userinfo',
          { headers: { Authorization: `Bearer ${tokenResponse.access_token}` } }
        );
        
        // Send to our backend for authentication/registration
        const response = await axios.post('/api/google-login', {
          email: userInfo.data.email,
          name: userInfo.data.name,
          googleId: userInfo.data.sub,
          accessToken: tokenResponse.access_token
        });
        
        if (response.data.success) {
          onLogin(response.data.user_id, response.data.name);
        } else {
          setError(response.data.message || 'Google login failed. Please try again.');
        }
      } catch (error) {
        console.error('Google login error:', error);
        setError('Google login failed. Please try again.');
      }
    },
    onError: () => {
      setError('Google login failed. Please try again.');
    }
  });

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h2>Welcome Back</h2>
          <p>Sign in to continue to Edusphere</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Enter your email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        {/* Google sign-in is shown only when a real OAuth client ID is
            configured. Without one the button renders but Google rejects the
            request, so it looks broken with no explanation - which is worse
            than not offering it. See DEPLOY.md to set VITE_GOOGLE_CLIENT_ID. */}
        {hasGoogleAuth && (
          <>
            <div className="divider">
              <span>or</span>
            </div>

            <button
              onClick={handleGoogleLogin}
              className="google-login-button"
              disabled={loading}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                <path d="M12.24 10.285V14.4h6.806c-.275 1.765-2.056 5.174-6.806 5.174-4.095 0-7.439-3.389-7.439-7.574s3.345-7.574 7.439-7.574c2.33 0 3.891.989 4.785 1.849l3.254-3.138C18.189 1.186 15.479 0 12.24 0c-6.635 0-12 5.365-12 12s5.365 12 12 12c6.926 0 11.52-4.869 11.52-11.726 0-.788-.085-1.39-.189-1.989H12.24z"/>
              </svg>
              Sign in with Google
            </button>
          </>
        )}

        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <span className="auth-link" onClick={onSwitchToSignup}>
              Sign up
            </span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;