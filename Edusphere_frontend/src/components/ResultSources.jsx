import React from 'react';
import ReactMarkdown from 'react-markdown';

export default function ResultSources({ sources }) {
  if (!Array.isArray(sources) || sources.length === 0) {
    return (
      <div className="result-sources">
        <p>No sources available for this response.</p>
      </div>
    );
  }

  return (
    <div className="result-sources">
      <div className="sources-list">
        {sources.map((source, index) => (
          <div key={index} className="source-item">
            <div className="source-header">
              <h4>{source.title || `Source ${index + 1}`}</h4>
              <span className="source-score">Relevance: {(source.score * 100).toFixed(1)}%</span>
            </div>
            <div className="source-content markdown-body" style={{ fontSize: '0.9rem', opacity: 0.9 }}>
              <ReactMarkdown>{source.content}</ReactMarkdown>
              {source.path && (
                <div style={{ marginTop: '0.8rem', color: '#9db9c1', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ backgroundColor: '#0b1a1f', padding: '2px 6px', borderRadius: '4px' }}>📂 PATH</span>
                  {source.path}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
