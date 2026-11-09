import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { LibraryProvider, useLibrary } from './context/LibraryContext';
import ChatPage from './pages/ChatPage';
import CatalogPage from './pages/CatalogPage';
import StudentsPage from './pages/StudentsPage';
import ReservationsPage from './pages/ReservationsPage';
import DashboardPage from './pages/DashboardPage';
import './App.css';

function NavBar() {
  const { currentStudent } = useLibrary();

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="brand-icon">📚</span>
        <div>
          <span className="brand-name">Library AI</span>
          <span className="brand-sub">Powered by IBM Granite</span>
        </div>
      </div>

      <div className="navbar-links">
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          🏠 Dashboard
        </NavLink>
        <NavLink to="/chat" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          🤖 AI Agent
        </NavLink>
        <NavLink to="/catalog" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          📖 Catalog
        </NavLink>
        <NavLink to="/reservations" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          📋 Reservations
        </NavLink>
        <NavLink to="/students" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          👥 Students
        </NavLink>
      </div>

      <div className="navbar-profile">
        {currentStudent ? (
          <div className="student-pill">
            <span className="student-avatar">{currentStudent.name[0]}</span>
            <span className="student-name">{currentStudent.name.split(' ')[0]}</span>
          </div>
        ) : (
          <NavLink to="/students" className="btn btn-secondary btn-sm">
            Select Profile
          </NavLink>
        )}
      </div>
    </nav>
  );
}

function App() {
  return (
    <LibraryProvider>
      <BrowserRouter>
        <div className="app-layout">
          <NavBar />
          <main className="app-content">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/catalog" element={<CatalogPage />} />
              <Route path="/reservations" element={<ReservationsPage />} />
              <Route path="/students" element={<StudentsPage />} />
            </Routes>
          </main>
          <footer className="app-footer">
            <span>Library AI Agent</span>
            <span className="footer-sep">·</span>
            <span>Powered by <strong>IBM Granite</strong> on watsonx.ai</span>
            <span className="footer-sep">·</span>
            <span>IBM Cloud Lite</span>
          </footer>
        </div>
      </BrowserRouter>
    </LibraryProvider>
  );
}

export default App;
