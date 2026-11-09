// In-memory library database with LowDB persistence
// Acts as the library catalog, student registry, reservations, and waitlists

const low = require('lowdb');
const FileSync = require('lowdb/adapters/FileSync');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const adapter = new FileSync(path.join(__dirname, '../data/db.json'));
const db = low(adapter);

// Default schema
db.defaults({
  books: [],
  students: [],
  reservations: [],
  waitlists: [],
  chatHistory: [],
}).write();

// ─── BOOK OPERATIONS ──────────────────────────────────────────────────────────

const BookModel = {
  findAll(filters = {}) {
    let chain = db.get('books');
    if (filters.subject) {
      chain = chain.filter(b =>
        b.subject.toLowerCase().includes(filters.subject.toLowerCase())
      );
    }
    if (filters.available) {
      chain = chain.filter(b => b.availableCopies > 0);
    }
    if (filters.search) {
      const q = filters.search.toLowerCase();
      chain = chain.filter(b =>
        b.title.toLowerCase().includes(q) ||
        b.author.toLowerCase().includes(q) ||
        b.subject.toLowerCase().includes(q) ||
        (b.tags || []).some(t => t.toLowerCase().includes(q)) ||
        (b.description || '').toLowerCase().includes(q)
      );
    }
    return chain.value();
  },

  findById(id) {
    return db.get('books').find({ id }).value();
  },

  findByISBN(isbn) {
    return db.get('books').find({ isbn }).value();
  },

  create(bookData) {
    const book = {
      id: uuidv4(),
      ...bookData,
      totalCopies: bookData.totalCopies || 1,
      availableCopies: bookData.availableCopies ?? bookData.totalCopies ?? 1,
      borrowedCount: 0,
      reservationCount: 0,
      createdAt: new Date().toISOString(),
    };
    db.get('books').push(book).write();
    return book;
  },

  update(id, updates) {
    db.get('books').find({ id }).assign(updates).write();
    return db.get('books').find({ id }).value();
  },

  decrementAvailable(id) {
    const book = db.get('books').find({ id }).value();
    if (book && book.availableCopies > 0) {
      db.get('books').find({ id }).assign({
        availableCopies: book.availableCopies - 1,
        borrowedCount: (book.borrowedCount || 0) + 1,
      }).write();
      return true;
    }
    return false;
  },

  incrementAvailable(id) {
    const book = db.get('books').find({ id }).value();
    if (book) {
      db.get('books').find({ id }).assign({
        availableCopies: Math.min(book.availableCopies + 1, book.totalCopies),
      }).write();
    }
  },

  getPopular(limit = 10) {
    return db.get('books')
      .sortBy('borrowedCount')
      .reverse()
      .take(limit)
      .value();
  },

  getBySubject(subject) {
    return db.get('books')
      .filter(b => b.subject.toLowerCase() === subject.toLowerCase())
      .value();
  },

  searchSemantic(keywords = []) {
    if (!keywords.length) return [];
    return db.get('books').filter(book => {
      const text = `${book.title} ${book.author} ${book.subject} ${(book.tags || []).join(' ')} ${book.description || ''}`.toLowerCase();
      return keywords.some(kw => text.includes(kw.toLowerCase()));
    }).value();
  },
};

// ─── STUDENT OPERATIONS ───────────────────────────────────────────────────────

const StudentModel = {
  findAll() {
    return db.get('students').value();
  },

  findById(id) {
    return db.get('students').find({ id }).value();
  },

  findByEmail(email) {
    return db.get('students').find({ email: email.toLowerCase() }).value();
  },

  create(studentData) {
    const student = {
      id: uuidv4(),
      ...studentData,
      email: studentData.email.toLowerCase(),
      borrowedBooks: [],
      reservedBooks: [],
      waitlistBooks: [],
      readingHistory: [],
      preferences: studentData.preferences || {},
      createdAt: new Date().toISOString(),
    };
    db.get('students').push(student).write();
    return student;
  },

  update(id, updates) {
    db.get('students').find({ id }).assign(updates).write();
    return db.get('students').find({ id }).value();
  },

  addToReadingHistory(studentId, bookId) {
    const student = db.get('students').find({ id: studentId }).value();
    if (student) {
      const history = student.readingHistory || [];
      if (!history.includes(bookId)) {
        db.get('students').find({ id: studentId }).assign({
          readingHistory: [...history, bookId],
        }).write();
      }
    }
  },
};

// ─── RESERVATION OPERATIONS ───────────────────────────────────────────────────

const ReservationModel = {
  findAll(filters = {}) {
    let chain = db.get('reservations');
    if (filters.studentId) chain = chain.filter({ studentId: filters.studentId });
    if (filters.bookId) chain = chain.filter({ bookId: filters.bookId });
    if (filters.status) chain = chain.filter({ status: filters.status });
    return chain.value();
  },

  findById(id) {
    return db.get('reservations').find({ id }).value();
  },

  create(data) {
    const reservation = {
      id: uuidv4(),
      ...data,
      status: 'active',
      reservedAt: new Date().toISOString(),
      dueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(), // 14 days
    };
    db.get('reservations').push(reservation).write();
    return reservation;
  },

  update(id, updates) {
    db.get('reservations').find({ id }).assign(updates).write();
    return db.get('reservations').find({ id }).value();
  },

  cancel(id) {
    db.get('reservations').find({ id }).assign({ status: 'cancelled', cancelledAt: new Date().toISOString() }).write();
  },

  getActiveForStudent(studentId) {
    return db.get('reservations').filter({ studentId, status: 'active' }).value();
  },
};

// ─── WAITLIST OPERATIONS ──────────────────────────────────────────────────────

const WaitlistModel = {
  getForBook(bookId) {
    return db.get('waitlists').filter({ bookId }).sortBy('joinedAt').value();
  },

  getForStudent(studentId) {
    return db.get('waitlists').filter({ studentId }).value();
  },

  isOnWaitlist(bookId, studentId) {
    return !!db.get('waitlists').find({ bookId, studentId }).value();
  },

  join(bookId, studentId) {
    const existing = db.get('waitlists').find({ bookId, studentId }).value();
    if (existing) return existing;

    const currentList = db.get('waitlists').filter({ bookId }).value();
    const entry = {
      id: uuidv4(),
      bookId,
      studentId,
      position: currentList.length + 1,
      joinedAt: new Date().toISOString(),
      status: 'waiting',
    };
    db.get('waitlists').push(entry).write();
    return entry;
  },

  remove(bookId, studentId) {
    db.get('waitlists').remove({ bookId, studentId }).write();
    // Re-number positions
    const remaining = db.get('waitlists').filter({ bookId }).sortBy('joinedAt').value();
    remaining.forEach((entry, i) => {
      db.get('waitlists').find({ id: entry.id }).assign({ position: i + 1 }).write();
    });
  },

  getPosition(bookId, studentId) {
    const entry = db.get('waitlists').find({ bookId, studentId }).value();
    return entry ? entry.position : null;
  },
};

// ─── CHAT HISTORY ─────────────────────────────────────────────────────────────

const ChatModel = {
  getHistory(studentId, limit = 20) {
    return db.get('chatHistory')
      .filter({ studentId })
      .sortBy('timestamp')
      .reverse()
      .take(limit)
      .reverse()
      .value();
  },

  save(studentId, role, content, metadata = {}) {
    db.get('chatHistory').push({
      id: uuidv4(),
      studentId,
      role,
      content,
      metadata,
      timestamp: new Date().toISOString(),
    }).write();
  },
};

module.exports = { db, BookModel, StudentModel, ReservationModel, WaitlistModel, ChatModel };
