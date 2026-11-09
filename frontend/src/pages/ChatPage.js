import React, { useState, useEffect, useRef, useCallback } from 'react';
import { agentAPI, reservationAPI } from '../services/api';
import { useLibrary } from '../context/LibraryContext';
import { toast } from 'react-toastify';
import './ChatPage.css';

const QUICK_PROMPTS = [
  { label: '📚 Recommend books for my major', text: 'Recommend books based on my major and current courses' },
  { label: '🔍 Search by topic', text: 'I need books about machine learning and neural networks' },
  { label: '📋 Check availability', text: 'Is Introduction to Algorithms available?' },
  { label: '🎓 Syllabus books', text: 'Find books for my current course syllabus' },
  { label: '⭐ Most popular books', text: 'What are the most popular books in the library right now?' },
  { label: '🐍 Python resources', text: 'I need beginner Python programming books' },
];

function BookCard({ book, studentId, compact }) {
  const [reserving, setReserving] = useState(false);

  const handleReserve = async () => {
    if (!studentId) { toast.warning('Please select a student profile first'); return; }
    setReserving(true);
    try {
      const { data } = await reservationAPI.create(studentId, book.id);
      toast.success(data.message);
    } catch (err) {
      const msg = err.response?.data?.error || 'Reservation failed';
      if (err.response?.data?.canWaitlist) {
        if (window.confirm(`${msg}\n\nJoin the waitlist instead?`)) {
          try {
            const { data: wdata } = await reservationAPI.joinWaitlist(studentId, book.id);
            toast.info(`Joined waitlist at position #${wdata.position}`);
          } catch (we) { toast.error(we.response?.data?.error || 'Failed to join waitlist'); }
        }
      } else {
        toast.error(msg);
      }
    } finally { setReserving(false); }
  };

  const avail = book.availableCopies;
  const availClass = avail === 0 ? 'badge-unavailable' : avail <= 2 ? 'badge-low' : 'badge-available';
  const availText = avail === 0 ? 'Unavailable' : avail === 1 ? '1 copy left' : `${avail} available`;

  if (compact) {
    return (
      <div className="chat-book-card-compact">
        <div className="cbc-info">
          <strong>{book.title}</strong>
          <span className="cbc-author">{book.author}</span>
          <span className={`badge ${availClass}`}>{availText}</span>
        </div>
        <button className="btn btn-primary btn-sm" onClick={handleReserve} disabled={reserving || avail === 0}>
          {reserving ? '...' : avail === 0 ? 'Waitlist' : 'Reserve'}
        </button>
      </div>
    );
  }

  return (
    <div className="chat-book-card">
      <div className="cbc-header">
        <div>
          <div className="cbc-title">{book.title}</div>
          <div className="cbc-author">{book.author}</div>
        </div>
        <span className={`badge ${availClass}`}>{availText}</span>
      </div>
      <div className="cbc-meta">
        <span className="badge badge-subject">{book.subject}</span>
        {book.level && <span className="badge badge-level">{book.level}</span>}
        {book.rating && <span className="cbc-rating">⭐ {book.rating}</span>}
      </div>
      {book.description && <p className="cbc-desc">{book.description.substring(0, 100)}...</p>}
      <div className="cbc-actions">
        <button
          className={`btn btn-sm ${avail === 0 ? 'btn-secondary' : 'btn-primary'}`}
          onClick={handleReserve}
          disabled={reserving}
        >
          {reserving ? <span className="loading-spinner" /> : null}
          {avail === 0 ? '📋 Join Waitlist' : '📌 Reserve'}
        </button>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const { currentStudent } = useLibrary();
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello${currentStudent ? `, ${currentStudent.name}` : ''}! 👋\n\nI'm your **Library AI Agent**, powered by **IBM Granite** on watsonx.ai.\n\nI can help you:\n• 🔍 Find books by topic, course, or keyword\n• ⭐ Get personalized recommendations\n• 📊 Check real-time book availability\n• 📌 Reserve books or join waitlists\n• 🎓 Find resources for your syllabus\n\nWhat are you looking for today?`,
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const [syllabusMode, setSyllabusMode] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = useCallback(async (text) => {
    const userMsg = text || input.trim();
    if (!userMsg || thinking) return;
    setInput('');

    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'user',
      content: userMsg,
      timestamp: new Date().toISOString(),
    }]);
    setThinking(true);

    try {
      const { data } = await agentAPI.chat(userMsg, currentStudent?.id);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.message,
        books: data.books || data.suggestedBooks,
        intent: data.intent,
        understanding: data.understanding,
        timestamp: data.timestamp,
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: `I encountered an error: ${err.response?.data?.error || err.message}. Please try again.`,
        timestamp: new Date().toISOString(),
        isError: true,
      }]);
    } finally {
      setThinking(false);
    }
  }, [input, thinking, currentStudent]);

  const handleSyllabus = async () => {
    const text = input.trim();
    if (!text) return;
    setInput('');
    setSyllabusMode(false);

    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'user',
      content: `[Syllabus Analysis]\n${text.substring(0, 200)}...`,
      timestamp: new Date().toISOString(),
    }]);
    setThinking(true);

    try {
      const { data } = await agentAPI.analyzeSyllabus(text, currentStudent?.id);
      const books = data.catalogMatches
        .filter(m => m.catalogBook)
        .map(m => m.catalogBook);

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: `📚 **Syllabus Analysis Complete!**\n\nFound **${data.analysis.required?.length || 0}** required and **${data.analysis.recommended?.length || 0}** recommended books.\n\nTopics covered: ${(data.analysis.topics || []).join(', ')}\n\nHere are the matching books in our catalog:`,
        books: books.length > 0 ? books : data.topicBooks,
        timestamp: new Date().toISOString(),
      }]);
    } catch (err) {
      toast.error('Syllabus analysis failed: ' + (err.response?.data?.error || err.message));
    } finally {
      setThinking(false); }
  };

  return (
    <div className="chat-page">
      <div className="chat-sidebar">
        <div className="sidebar-section">
          <h3>💡 Quick Prompts</h3>
          {QUICK_PROMPTS.map((p, i) => (
            <button key={i} className="quick-prompt-btn" onClick={() => sendMessage(p.text)}>
              {p.label}
            </button>
          ))}
        </div>
        <div className="sidebar-section">
          <h3>🎓 Syllabus Tool</h3>
          <p>Paste your course syllabus and I'll find all required books in our library!</p>
          <button className="btn btn-secondary btn-sm" style={{ marginTop: 8 }} onClick={() => setSyllabusMode(true)}>
            📄 Analyze Syllabus
          </button>
        </div>
        {currentStudent && (
          <div className="sidebar-section sidebar-profile">
            <h3>👤 Active Profile</h3>
            <p className="profile-name">{currentStudent.name}</p>
            <p className="profile-meta">{currentStudent.major} · Year {currentStudent.year}</p>
            {currentStudent.currentCourses?.length > 0 && (
              <p className="profile-courses">{currentStudent.currentCourses.slice(0,2).join(', ')}{currentStudent.currentCourses.length > 2 ? '...' : ''}</p>
            )}
          </div>
        )}
      </div>

      <div className="chat-main">
        <div className="chat-messages">
          {messages.map(msg => (
            <div key={msg.id} className={`message message-${msg.role} ${msg.isError ? 'message-error' : ''}`}>
              {msg.role === 'assistant' && (
                <div className="message-avatar ai-avatar">🤖</div>
              )}
              <div className="message-bubble">
                <div className="message-text" dangerouslySetInnerHTML={{
                  __html: msg.content
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\n/g, '<br/>')
                }} />
                {msg.books?.length > 0 && (
                  <div className="message-books">
                    <div className="books-grid">
                      {msg.books.slice(0, 6).map(book => (
                        <BookCard key={book.id} book={book} studentId={currentStudent?.id} compact />
                      ))}
                    </div>
                  </div>
                )}
                {msg.understanding && (
                  <div className="message-meta">
                    <span className="intent-badge">Intent: {msg.understanding.intent}</span>
                    {msg.understanding.subject && (
                      <span className="intent-badge">Topic: {msg.understanding.subject}</span>
                    )}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="message-avatar user-avatar">
                  {currentStudent ? currentStudent.name[0] : '👤'}
                </div>
              )}
            </div>
          ))}
          {thinking && (
            <div className="message message-assistant">
              <div className="message-avatar ai-avatar">🤖</div>
              <div className="message-bubble thinking">
                <span className="dot" /><span className="dot" /><span className="dot" />
                <span className="thinking-label">IBM Granite is thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          {syllabusMode && (
            <div className="syllabus-banner">
              📄 Syllabus mode active — paste your syllabus text below, then click Analyze
              <button className="btn btn-ghost btn-sm" onClick={() => setSyllabusMode(false)}>✕ Cancel</button>
            </div>
          )}
          <div className="chat-input-row">
            <textarea
              className="chat-textarea"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={syllabusMode
                ? 'Paste your course syllabus here...'
                : 'Ask me anything — find books, check availability, get recommendations...'}
              rows={syllabusMode ? 5 : 2}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey && !syllabusMode) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
            />
            <button
              className="btn btn-primary chat-send-btn"
              onClick={syllabusMode ? handleSyllabus : () => sendMessage()}
              disabled={!input.trim() || thinking}
            >
              {thinking ? <span className="loading-spinner" /> : syllabusMode ? '🔍' : '➤'}
            </button>
          </div>
          <p className="chat-hint">
            {syllabusMode ? 'Click 🔍 to analyze your syllabus' : 'Press Enter to send · Shift+Enter for new line'}
          </p>
        </div>
      </div>
    </div>
  );
}
