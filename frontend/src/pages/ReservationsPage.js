import React, { useState, useEffect, useCallback } from 'react';
import { reservationAPI } from '../services/api';
import { useLibrary } from '../context/LibraryContext';
import { toast } from 'react-toastify';
import './ReservationsPage.css';

export default function ReservationsPage() {
  const { currentStudent } = useLibrary();
  const [reservations, setReservations] = useState([]);
  const [waitlists, setWaitlists] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState('reservations');

  const load = useCallback(async () => {
    if (!currentStudent) return;
    setLoading(true);
    try {
      const { data } = await reservationAPI.getForStudent(currentStudent.id);
      const active = data.filter(r => r.status === 'active');
      const all = data;
      setReservations(all);

      // Fetch waitlist entries
      const wData = [];
      for (const r of active) {
        if (r.bookId) {
          const { data: wl } = await reservationAPI.getWaitlist(r.bookId);
          const myPos = wl.waitlist.find(e => e.studentId === currentStudent.id);
          if (myPos) wData.push({ ...myPos, book: r.book });
        }
      }
      setWaitlists(wData);
    } catch (err) {
      toast.error('Failed to load reservations');
    } finally { setLoading(false); }
  }, [currentStudent]);

  useEffect(() => { load(); }, [load]);

  const cancelReservation = async (id) => {
    if (!window.confirm('Cancel this reservation?')) return;
    try {
      await reservationAPI.cancel(id);
      toast.success('Reservation cancelled');
      load();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to cancel');
    }
  };

  const leaveWaitlist = async (bookId) => {
    try {
      await reservationAPI.leaveWaitlist(bookId, currentStudent.id);
      toast.success('Removed from waitlist');
      load();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to leave waitlist');
    }
  };

  if (!currentStudent) {
    return (
      <div className="res-page">
        <div className="page-header">
          <h1>📋 My Reservations</h1>
        </div>
        <div className="empty-state">
          <div className="empty-icon">👤</div>
          <h3>No profile selected</h3>
          <p>Go to the Students tab and select your profile to view reservations</p>
        </div>
      </div>
    );
  }

  const active = reservations.filter(r => r.status === 'active');
  const history = reservations.filter(r => r.status !== 'active');

  return (
    <div className="res-page">
      <div className="page-header">
        <h1>📋 My Reservations</h1>
        <p>{currentStudent.name} · {active.length} active reservation(s)</p>
      </div>

      <div className="res-tabs">
        <button className={`tab-btn ${tab === 'reservations' ? 'active' : ''}`} onClick={() => setTab('reservations')}>
          Active ({active.length})
        </button>
        <button className={`tab-btn ${tab === 'waitlists' ? 'active' : ''}`} onClick={() => setTab('waitlists')}>
          Waitlists ({waitlists.length})
        </button>
        <button className={`tab-btn ${tab === 'history' ? 'active' : ''}`} onClick={() => setTab('history')}>
          History ({history.length})
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 48 }}><span className="loading-spinner" style={{ width: 32, height: 32 }} /></div>
      ) : tab === 'reservations' ? (
        active.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>No active reservations</h3>
            <p>Browse the catalog and reserve a book to get started</p>
          </div>
        ) : (
          <div className="res-list">
            {active.map(r => (
              <div key={r.id} className="res-card">
                <div className="res-book-info">
                  <div className="res-book-cover">{(r.book?.title || r.bookTitle || '?')[0]}</div>
                  <div>
                    <h3>{r.book?.title || r.bookTitle}</h3>
                    <p>{r.book?.author}</p>
                    <p className="res-meta">Reserved: {new Date(r.reservedAt).toLocaleDateString()}</p>
                  </div>
                </div>
                <div className="res-right">
                  <div className="due-date">
                    <span className="due-label">Due date</span>
                    <span className="due-value">{new Date(r.dueDate).toLocaleDateString()}</span>
                  </div>
                  <button className="btn btn-danger btn-sm" onClick={() => cancelReservation(r.id)}>
                    ✕ Cancel
                  </button>
                </div>
              </div>
            ))}
          </div>
        )
      ) : tab === 'waitlists' ? (
        waitlists.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">⏳</div>
            <h3>Not on any waitlists</h3>
            <p>When you join a waitlist for an unavailable book, it will appear here</p>
          </div>
        ) : (
          <div className="res-list">
            {waitlists.map(w => (
              <div key={w.id} className="res-card">
                <div className="res-book-info">
                  <div className="res-book-cover">{(w.book?.title || '?')[0]}</div>
                  <div>
                    <h3>{w.book?.title}</h3>
                    <p className="res-meta">Joined: {new Date(w.joinedAt).toLocaleDateString()}</p>
                  </div>
                </div>
                <div className="res-right">
                  <div className="due-date">
                    <span className="due-label">Position</span>
                    <span className="due-value" style={{ fontSize: 22, color: 'var(--ibm-orange)' }}>#{w.position}</span>
                  </div>
                  <button className="btn btn-ghost btn-sm" onClick={() => leaveWaitlist(w.bookId)}>
                    Leave
                  </button>
                </div>
              </div>
            ))}
          </div>
        )
      ) : (
        history.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📜</div>
            <h3>No history yet</h3>
          </div>
        ) : (
          <div className="res-list">
            {history.map(r => (
              <div key={r.id} className="res-card res-card-muted">
                <div className="res-book-info">
                  <div className="res-book-cover">{(r.book?.title || r.bookTitle || '?')[0]}</div>
                  <div>
                    <h3>{r.book?.title || r.bookTitle}</h3>
                    <p className="res-meta">
                      {r.status === 'cancelled' ? '🚫 Cancelled' : '✅ Returned'} · {new Date(r.reservedAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  );
}
