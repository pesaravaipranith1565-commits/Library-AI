import React, { useState, useEffect, useCallback } from 'react';
import { bookAPI, reservationAPI } from '../services/api';
import { useLibrary } from '../context/LibraryContext';
import { toast } from 'react-toastify';
import './CatalogPage.css';

function BookCard({ book, studentId, onReserved }) {
  const [reserving, setReserving] = useState(false);
  const [waitlisting, setWaitlisting] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const avail = book.availableCopies;
  const availClass = avail === 0 ? 'badge-unavailable' : avail <= 2 ? 'badge-low' : 'badge-available';
  const availText = avail === 0 ? '📕 Unavailable' : avail === 1 ? '⚠️ 1 copy left' : `✅ ${avail} available`;

  const handleReserve = async () => {
    if (!studentId) { toast.warning('Select a student profile first'); return; }
    setReserving(true);
    try {
      const { data } = await reservationAPI.create(studentId, book.id);
      toast.success(data.message);
      onReserved?.();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Reservation failed');
    } finally { setReserving(false); }
  };

  const handleWaitlist = async () => {
    if (!studentId) { toast.warning('Select a student profile first'); return; }
    setWaitlisting(true);
    try {
      const { data } = await reservationAPI.joinWaitlist(studentId, book.id);
      toast.info(`Joined waitlist at position #${data.position} (est. ${data.estimatedWaitDays} days)`);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to join waitlist');
    } finally { setWaitlisting(false); }
  };

  return (
    <div className={`book-card ${expanded ? 'expanded' : ''}`}>
      <div className="book-card-header" onClick={() => setExpanded(!expanded)}>
        <div className="book-cover">
          <span className="book-cover-letter">{book.title[0]}</span>
        </div>
        <div className="book-info">
          <h3 className="book-title">{book.title}</h3>
          <p className="book-author">by {book.author}</p>
          {book.edition && <p className="book-edition">{book.edition} edition · {book.year}</p>}
        </div>
        <div className="book-status">
          <span className={`badge ${availClass}`}>{availText}</span>
          {book.rating && <span className="book-rating">⭐ {book.rating}</span>}
        </div>
      </div>

      <div className="book-tags">
        <span className="badge badge-subject">{book.subject}</span>
        {book.category && <span className="tag">{book.category}</span>}
        {book.level && <span className="badge badge-level">{book.level}</span>}
      </div>

      {expanded && (
        <div className="book-expanded">
          {book.description && <p className="book-description">{book.description}</p>}
          <div className="book-stats">
            <span>📦 {book.totalCopies} total copies</span>
            <span>📤 {book.borrowedCount || 0} times borrowed</span>
            {book.isbn && <span>📘 ISBN: {book.isbn}</span>}
          </div>
          {book.tags?.length > 0 && (
            <div className="book-tags-row">
              {book.tags.map(t => <span key={t} className="tag">{t}</span>)}
            </div>
          )}
        </div>
      )}

      <div className="book-actions">
        {avail > 0 ? (
          <button className="btn btn-primary btn-sm" onClick={handleReserve} disabled={reserving}>
            {reserving ? <span className="loading-spinner" /> : '📌 Reserve'}
          </button>
        ) : (
          <button className="btn btn-secondary btn-sm" onClick={handleWaitlist} disabled={waitlisting}>
            {waitlisting ? <span className="loading-spinner" /> : '📋 Join Waitlist'}
          </button>
        )}
        <button className="btn btn-ghost btn-sm" onClick={() => setExpanded(!expanded)}>
          {expanded ? '▲ Less' : '▼ Details'}
        </button>
      </div>
    </div>
  );
}

export default function CatalogPage() {
  const { currentStudent } = useLibrary();
  const [books, setBooks] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [subject, setSubject] = useState('');
  const [available, setAvailable] = useState(false);
  const [sort, setSort] = useState('');
  const [total, setTotal] = useState(0);

  const loadBooks = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (subject) params.subject = subject;
      if (available) params.available = 'true';
      if (sort) params.sort = sort;

      const { data } = await bookAPI.getAll(params);
      setBooks(data.books);
      setTotal(data.total);
    } catch (err) {
      toast.error('Failed to load books');
    } finally { setLoading(false); }
  }, [search, subject, available, sort]);

  useEffect(() => { loadBooks(); }, [loadBooks]);
  useEffect(() => {
    bookAPI.getSubjects().then(({ data }) => setSubjects(data));
  }, []);

  return (
    <div className="catalog-page">
      <div className="page-header">
        <h1>📖 Library Catalog</h1>
        <p>Browse and search {total} books · Use filters to narrow down results</p>
      </div>

      <div className="catalog-filters">
        <input
          className="search-input"
          type="text"
          placeholder="🔍 Search by title, author, subject, keyword..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select value={subject} onChange={e => setSubject(e.target.value)}>
          <option value="">All subjects</option>
          {subjects.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={sort} onChange={e => setSort(e.target.value)}>
          <option value="">Default sort</option>
          <option value="popular">Most Popular</option>
          <option value="rating">Highest Rated</option>
          <option value="title">A → Z</option>
        </select>
        <label className="filter-toggle">
          <input type="checkbox" checked={available} onChange={e => setAvailable(e.target.checked)} />
          Available only
        </label>
        <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setSubject(''); setAvailable(false); setSort(''); }}>
          ✕ Clear
        </button>
      </div>

      {loading ? (
        <div className="loading-state">
          <span className="loading-spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
          <p>Loading catalog...</p>
        </div>
      ) : books.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📚</div>
          <h3>No books found</h3>
          <p>Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="books-list">
          {books.map(book => (
            <BookCard
              key={book.id}
              book={book}
              studentId={currentStudent?.id}
              onReserved={loadBooks}
            />
          ))}
        </div>
      )}
    </div>
  );
}
