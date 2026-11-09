import axios from 'axios';

const API = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000, // 30s for AI calls
});

// Book API
export const bookAPI = {
  getAll: (params = {}) => API.get('/books', { params }),
  getById: (id) => API.get(`/books/${id}`),
  getPopular: (limit = 10) => API.get('/books/popular', { params: { limit } }),
  getSubjects: () => API.get('/books/subjects'),
  create: (data) => API.post('/books', data),
};

// Student API
export const studentAPI = {
  getAll: () => API.get('/students'),
  getById: (id) => API.get(`/students/${id}`),
  create: (data) => API.post('/students', data),
  update: (id, data) => API.put(`/students/${id}`, data),
  getHistory: (id) => API.get(`/students/${id}/history`),
};

// Reservation API
export const reservationAPI = {
  create: (studentId, bookId) => API.post('/reservations', { studentId, bookId }),
  getForStudent: (studentId) => API.get(`/reservations/student/${studentId}`),
  cancel: (id) => API.delete(`/reservations/${id}`),
  joinWaitlist: (studentId, bookId) => API.post('/reservations/waitlist', { studentId, bookId }),
  getWaitlist: (bookId) => API.get(`/reservations/waitlist/${bookId}`),
  leaveWaitlist: (bookId, studentId) => API.delete(`/reservations/waitlist/${bookId}/${studentId}`),
};

// AI Agent API
export const agentAPI = {
  chat: (message, studentId) => API.post('/agent/chat', { message, studentId }),
  recommend: (studentId, query) => API.post('/agent/recommend', { studentId, query }),
  analyzeSyllabus: (syllabusText, studentId) => API.post('/agent/analyze-syllabus', { syllabusText, studentId }),
  getChatHistory: (studentId) => API.get(`/agent/chat-history/${studentId}`),
  search: (q, studentId) => API.get('/agent/search', { params: { q, studentId } }),
};

// Health check
export const healthCheck = () => API.get('/health'.replace('/api', ''));

export default API;
