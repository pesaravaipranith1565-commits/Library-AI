// Reservation & Waitlist routes
const express = require('express');
const router = express.Router();
const { BookModel, StudentModel, ReservationModel, WaitlistModel } = require('../models/database');

// POST /api/reservations — reserve a book
router.post('/', (req, res) => {
  try {
    const { studentId, bookId } = req.body;
    if (!studentId || !bookId) {
      return res.status(400).json({ error: 'studentId and bookId are required' });
    }

    const student = StudentModel.findById(studentId);
    if (!student) return res.status(404).json({ error: 'Student not found' });

    const book = BookModel.findById(bookId);
    if (!book) return res.status(404).json({ error: 'Book not found' });

    // Check if already reserved
    const existing = ReservationModel.findAll({ studentId, bookId, status: 'active' });
    if (existing.length > 0) {
      return res.status(409).json({ error: 'You already have an active reservation for this book' });
    }

    if (book.availableCopies <= 0) {
      return res.status(409).json({
        error: 'No copies available. Would you like to join the waitlist?',
        canWaitlist: true,
        bookId: book.id,
      });
    }

    // Decrement available copies
    const success = BookModel.decrementAvailable(bookId);
    if (!success) {
      return res.status(409).json({ error: 'Book became unavailable, please try again' });
    }

    const reservation = ReservationModel.create({ studentId, bookId, bookTitle: book.title, studentName: student.name });

    // Update student's reservedBooks
    const reservedBooks = [...(student.reservedBooks || []), bookId];
    StudentModel.update(studentId, { reservedBooks });
    StudentModel.addToReadingHistory(studentId, bookId);

    res.status(201).json({
      message: `"${book.title}" reserved successfully!`,
      reservation,
      dueDate: reservation.dueDate,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/reservations/student/:studentId — student's reservations
router.get('/student/:studentId', (req, res) => {
  try {
    const reservations = ReservationModel.findAll({ studentId: req.params.studentId });
    const enriched = reservations.map(r => ({
      ...r,
      book: BookModel.findById(r.bookId),
    }));
    res.json(enriched);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/reservations/:id — cancel reservation
router.delete('/:id', (req, res) => {
  try {
    const reservation = ReservationModel.findById(req.params.id);
    if (!reservation) return res.status(404).json({ error: 'Reservation not found' });
    if (reservation.status === 'cancelled') {
      return res.status(400).json({ error: 'Reservation is already cancelled' });
    }

    ReservationModel.cancel(req.params.id);
    BookModel.incrementAvailable(reservation.bookId);

    // Check waitlist and notify
    const waitlist = WaitlistModel.getForBook(reservation.bookId);
    let waitlistNotice = null;
    if (waitlist.length > 0) {
      const nextInLine = waitlist[0];
      const nextStudent = StudentModel.findById(nextInLine.studentId);
      waitlistNotice = `${nextStudent?.name || 'Next student'} on the waitlist has been notified.`;
    }

    res.json({
      message: 'Reservation cancelled',
      ...(waitlistNotice && { waitlistNotice }),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/reservations/waitlist — join waitlist
router.post('/waitlist', (req, res) => {
  try {
    const { studentId, bookId } = req.body;
    if (!studentId || !bookId) {
      return res.status(400).json({ error: 'studentId and bookId are required' });
    }

    const student = StudentModel.findById(studentId);
    if (!student) return res.status(404).json({ error: 'Student not found' });

    const book = BookModel.findById(bookId);
    if (!book) return res.status(404).json({ error: 'Book not found' });

    if (book.availableCopies > 0) {
      return res.status(400).json({ error: 'Book is currently available — you can reserve it directly' });
    }

    if (WaitlistModel.isOnWaitlist(bookId, studentId)) {
      const position = WaitlistModel.getPosition(bookId, studentId);
      return res.status(409).json({ error: `You are already on the waitlist at position #${position}` });
    }

    const entry = WaitlistModel.join(bookId, studentId);
    const waitlistSize = WaitlistModel.getForBook(bookId).length;
    const estimatedWait = waitlistSize * 14; // ~14 days per person

    res.status(201).json({
      message: `Added to waitlist for "${book.title}"`,
      position: entry.position,
      estimatedWaitDays: estimatedWait,
      entry,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/reservations/waitlist/:bookId — book's waitlist
router.get('/waitlist/:bookId', (req, res) => {
  try {
    const book = BookModel.findById(req.params.bookId);
    if (!book) return res.status(404).json({ error: 'Book not found' });

    const waitlist = WaitlistModel.getForBook(req.params.bookId);
    res.json({ book: book.title, waitlistSize: waitlist.length, waitlist });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/reservations/waitlist/:bookId/:studentId — leave waitlist
router.delete('/waitlist/:bookId/:studentId', (req, res) => {
  try {
    const { bookId, studentId } = req.params;
    if (!WaitlistModel.isOnWaitlist(bookId, studentId)) {
      return res.status(404).json({ error: 'You are not on the waitlist for this book' });
    }
    WaitlistModel.remove(bookId, studentId);
    res.json({ message: 'Removed from waitlist' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
