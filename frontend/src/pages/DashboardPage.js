import React, { useState, useEffect } from 'react';
import { bookAPI, reservationAPI } from '../services/api';
import { useLibrary } from '../context/LibraryContext';
import { useNavigate } from 'react-router-dom';
import './DashboardPage.css';

function StatCard({ icon, label, value, color }) {
  return (
    <div className="stat-card" style={{ borderTopColor: color }}>
      <div className="stat-icon" style={{ color }}>{icon}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const { currentStudent } = useLibrary();
  const navigate = useNavigate();
  const [popular, setPopular] = useState([]);
  const [stats, setStats] = useState({ total: 0, available: 0, subjects: 0 });
  const [reservations, setReservations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [popRes, allRes, subsRes] = await Promise.all([
          bookAPI.getPopular(6),
          bookAPI.getAll(),
          bookAPI.getSubjects(),
        ]);
        setPopular(popRes.data);
        setStats({
          total: allRes.data.total,
          available: allRes.data.books.filter(b => b.availableCopies > 0).length,
          subjects: subsRes.data.length,
        });
        if (currentStudent) {
          const { data } = await reservationAPI.getForStudent(currentStudent.id);
          setReservations(data.filter(r => r.status === 'active'));
        }
      } catch (err) { /* silent */ }
      finally { setLoading(false); }
    }
    load();
  }, [currentStudent]);

  return (
    <div className="dashboard-page">
      {/* Hero */}
      <div className="dashboard-hero">
        <div className="hero-content">
          <div className="hero-badge">
            <span>🤖</span> Powered by IBM Granite · watsonx.ai
          </div>
          <h1 className="hero-title">
            {currentStudent ? `Welcome back, ${currentStudent.name.split(' ')[0]}!` : 'Welcome to Library AI Agent'}
          </h1>
          <p className="hero-sub">
            {currentStudent
              ? `${currentStudent.major} · Year ${currentStudent.year} · Find your next great read below`
              : 'Your intelligent academic library assistant — powered by IBM Granite on IBM Cloud'}
          </p>
          <div className="hero-actions">
            <button className="btn btn-primary" onClick={() => navigate('/chat')}>
              🤖 Ask AI Agent
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/catalog')}>
              📖 Browse Catalog
            </button>
            {!currentStudent && (
              <button className="btn btn-ghost" onClick={() => navigate('/students')}>
                👤 Set Up Profile
              </button>
            )}
          </div>
        </div>
        <div className="hero-visual">
          <div className="ibm-logo-block">
            <div className="granite-badge">
              <span className="granite-label">IBM</span>
              <span className="granite-model">Granite</span>
              <span className="granite-sub">watsonx.ai</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <StatCard icon="📚" label="Total Books" value={stats.total} color="var(--ibm-blue)" />
        <StatCard icon="✅" label="Available Now" value={stats.available} color="var(--ibm-green)" />
        <StatCard icon="🎓" label="Subjects" value={stats.subjects} color="var(--ibm-purple)" />
        {currentStudent && (
          <StatCard icon="📌" label="My Reservations" value={reservations.length} color="var(--ibm-orange)" />
        )}
      </div>

      {/* Active reservations for current student */}
      {currentStudent && reservations.length > 0 && (
        <div className="dashboard-section">
          <div className="section-header">
            <h2>📌 My Active Reservations</h2>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/reservations')}>View all →</button>
          </div>
          <div className="res-mini-list">
            {reservations.map(r => (
              <div key={r.id} className="res-mini-card">
                <div className="rmc-cover">{(r.book?.title || r.bookTitle || '?')[0]}</div>
                <div className="rmc-info">
                  <strong>{r.book?.title || r.bookTitle}</strong>
                  <span>Due: {new Date(r.dueDate).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Popular books */}
      <div className="dashboard-section">
        <div className="section-header">
          <h2>🔥 Most Popular Books</h2>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/catalog')}>See catalog →</button>
        </div>
        {loading ? (
          <div style={{ padding: 32, textAlign: 'center' }}><span className="loading-spinner" style={{ width: 28, height: 28 }} /></div>
        ) : (
          <div className="popular-grid">
            {popular.map(book => {
              const avail = book.availableCopies;
              const cls = avail === 0 ? 'badge-unavailable' : avail <= 2 ? 'badge-low' : 'badge-available';
              return (
                <div key={book.id} className="popular-book-card" onClick={() => navigate('/catalog')}>
                  <div className="pbc-cover">{book.title[0]}</div>
                  <div className="pbc-info">
                    <strong className="pbc-title">{book.title}</strong>
                    <span className="pbc-author">{book.author}</span>
                    <div className="pbc-meta">
                      <span className={`badge ${cls}`}>
                        {avail === 0 ? 'Unavailable' : `${avail} available`}
                      </span>
                      <span className="pbc-borrows">📤 {book.borrowedCount} borrows</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Feature cards */}
      <div className="dashboard-section">
        <h2>✨ What can Library AI Agent do?</h2>
        <div className="features-grid">
          {[
            { icon: '🔍', title: 'Semantic Search', desc: 'Natural language queries understood by IBM Granite NLP — ask in plain English' },
            { icon: '⭐', title: 'Personalized Picks', desc: 'Recommendations tailored to your major, courses, and reading interests' },
            { icon: '📊', title: 'Real-time Availability', desc: 'Instant checks on all copies — reserve immediately or join the waitlist' },
            { icon: '📋', title: 'Smart Reservations', desc: 'Reserve books or join priority waitlists with automated position tracking' },
            { icon: '🎓', title: 'Syllabus Analysis', desc: 'Paste your course syllabus — AI finds every book in the library catalog' },
            { icon: '🤖', title: 'IBM Granite Powered', desc: 'Enterprise-grade LLM on IBM watsonx.ai (IBM Cloud Lite) for all AI features' },
          ].map(f => (
            <div key={f.title} className="feature-card">
              <span className="feature-icon">{f.icon}</span>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
