import React, { useState, useEffect } from 'react';
import { studentAPI } from '../services/api';
import { useLibrary } from '../context/LibraryContext';
import { toast } from 'react-toastify';
import './StudentsPage.css';

const MAJORS = ['Computer Science', 'Data Science', 'Artificial Intelligence', 'Mathematics', 'Physics', 'Electrical Engineering', 'Business Administration', 'Economics', 'Information Technology', 'Other'];

export default function StudentsPage() {
  const { currentStudent, setCurrentStudent, allStudents, refreshStudents } = useLibrary();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: '', email: '', studentId: '', major: 'Computer Science', year: 1,
    currentCourses: '', interests: '',
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => { refreshStudents(); }, [refreshStudents]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email) { toast.error('Name and email are required'); return; }
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        year: parseInt(form.year),
        currentCourses: form.currentCourses.split(',').map(c => c.trim()).filter(Boolean),
        interests: form.interests.split(',').map(i => i.trim()).filter(Boolean),
      };
      const { data } = await studentAPI.create(payload);
      toast.success(`Welcome, ${data.name}! 🎉`);
      setCurrentStudent(data);
      setShowForm(false);
      refreshStudents();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create profile');
    } finally { setSubmitting(false); }
  };

  return (
    <div className="students-page">
      <div className="page-header">
        <div>
          <h1>👥 Student Profiles</h1>
          <p>Select your profile to get personalized book recommendations</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Cancel' : '+ New Profile'}
        </button>
      </div>

      {showForm && (
        <form className="student-form" onSubmit={handleSubmit}>
          <h2>Create Student Profile</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>Full Name *</label>
              <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Jane Smith" required />
            </div>
            <div className="form-group">
              <label>Email *</label>
              <input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} placeholder="jane@university.edu" required />
            </div>
            <div className="form-group">
              <label>Student ID</label>
              <input value={form.studentId} onChange={e => setForm({...form, studentId: e.target.value})} placeholder="STU12345" />
            </div>
            <div className="form-group">
              <label>Major</label>
              <select value={form.major} onChange={e => setForm({...form, major: e.target.value})}>
                {MAJORS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Academic Year</label>
              <select value={form.year} onChange={e => setForm({...form, year: e.target.value})}>
                {[1,2,3,4,5].map(y => <option key={y} value={y}>Year {y}</option>)}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label>Current Courses <span className="hint">(comma-separated)</span></label>
            <input value={form.currentCourses} onChange={e => setForm({...form, currentCourses: e.target.value})} placeholder="Algorithms, Database Systems, Operating Systems" />
          </div>
          <div className="form-group">
            <label>Study Interests <span className="hint">(comma-separated, for better recommendations)</span></label>
            <input value={form.interests} onChange={e => setForm({...form, interests: e.target.value})} placeholder="machine learning, web development, data visualization" />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? <span className="loading-spinner" /> : '✓ Create Profile'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </form>
      )}

      <div className="students-grid">
        {allStudents.map(student => (
          <div
            key={student.id}
            className={`student-card ${currentStudent?.id === student.id ? 'selected' : ''}`}
            onClick={() => setCurrentStudent(currentStudent?.id === student.id ? null : student)}
          >
            <div className="sc-avatar">{student.name[0]}</div>
            <div className="sc-info">
              <h3>{student.name}</h3>
              <p>{student.major} · Year {student.year}</p>
              {student.studentId && <p className="sc-sid">ID: {student.studentId}</p>}
              {student.currentCourses?.length > 0 && (
                <div className="sc-courses">
                  {student.currentCourses.slice(0, 3).map(c => <span key={c} className="tag">{c}</span>)}
                </div>
              )}
            </div>
            {currentStudent?.id === student.id && (
              <div className="sc-active-badge">✓ Active</div>
            )}
          </div>
        ))}
        {allStudents.length === 0 && (
          <div className="empty-state" style={{ gridColumn: '1/-1' }}>
            <div className="empty-icon">👤</div>
            <h3>No profiles yet</h3>
            <p>Create your student profile to get started with personalized recommendations</p>
          </div>
        )}
      </div>
    </div>
  );
}
