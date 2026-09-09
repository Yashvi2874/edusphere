import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';

/**
 * The sources behind an answer.
 *
 * Each card shows where the answer came from and how well it matched. The
 * excerpt is collapsed by default: three expanded walls of crawled markdown
 * push the actual answer off the screen, and most people only want to know
 * WHICH page was used, not to read it here.
 *
 * The raw folder path is deliberately not shown — it is debug output, not
 * something a student can act on.
 */

function confidence(score) {
  if (score >= 0.55) return { label: 'Strong match', className: 'strong' };
  if (score >= 0.45) return { label: 'Partial match', className: 'partial' };
  return { label: 'Weak match', className: 'weak' };
}

function SourceCard({ source, index }) {
  const [open, setOpen] = useState(false);
  const score = typeof source.score === 'number' ? source.score : 0;
  const { label, className } = confidence(score);
  const excerpt = (source.content || '').trim();

  return (
    <div className="source-item">
      <div className="source-header">
        <span className="source-index">{index + 1}</span>
        <h4>{source.title || `Source ${index + 1}`}</h4>
      </div>

      {source.breadcrumb ? (
        <div className="source-breadcrumb">{source.breadcrumb}</div>
      ) : null}

      <div className="source-meta">
        <span className={`source-score ${className}`}>{label}</span>
        <span className="source-score-value">{(score * 100).toFixed(0)}%</span>
      </div>

      {excerpt ? (
        <>
          <button
            type="button"
            className="source-toggle"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? 'Hide excerpt' : 'Show excerpt'}
          </button>
          {open ? (
            <div className="source-content markdown-body">
              <ReactMarkdown>{excerpt}</ReactMarkdown>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

export default function ResultSources({ sources }) {
  if (!Array.isArray(sources) || sources.length === 0) {
    return (
      <div className="result-sources">
        <p className="sources-empty">
          No sources for this reply — it wasn&apos;t answered from the college
          content.
        </p>
      </div>
    );
  }

  return (
    <div className="result-sources">
      <div className="sources-list">
        {sources.map((source, index) => (
          <SourceCard key={index} source={source} index={index} />
        ))}
      </div>
    </div>
  );
}
