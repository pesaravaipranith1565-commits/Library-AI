// Student routes — profile management, reading history
const express = require('express');
const router = express.Router();
const { StudentModel, BookModel, ReservationModel, WaitlistModel } = require('../models/database');

// GET /api/students — list all students
router.get('/', (req, res) => {
  try {
    const students = StudentModel.findAll().map(s => {
      const { readingHistory, ...rest } = s;
      return rest;
    });
    res.json(students);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/students/:id — student profile
router.get('/:id', (req, res) => {
  try {
    const student = StudentModel.findById(req.params.id);
    if (!student) return res.status(404).json({ error: 'Student not found' });

    // Enrich with active reservations
    const reservations = ReservationModel.getActiveForStudent(student.id);
    const waitlists = WaitlistModel.getForStudent(student.id);

    res.json({
      ...student,
      activeReservations: reservations.length,
      waitlistCount: waitlists.length,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/students — register a student
router.post('/', (req, res) => {
  try {
    const { name, email, studentId, major, year, currentCourses, interests } = req.body;
    if (!name || !email) {
      return res.status(400).json({ error: 'name and email are required' });
    }
    const existing = StudentModel.findByEmail(email);
    if (existing) {
      return res.status(409).json({ error: 'A student with this email already exists', student: existing });
    }
    const student = StudentModel.create({ name, email, studentId, major, year: parseInt(year) || 1, currentCourses, interests });
    res.status(201).json(student);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/students/:id — update student profile
router.put('/:id', (req, res) => {
  try {
    const student = StudentModel.findById(req.params.id);
    if (!student) return res.status(404).json({ error: 'Student not found' });

    const { name, major, year, currentCourses, interests, preferences } = req.body;
    const updated = StudentModel.update(req.params.id, {
      ...(name && { name }),
      ...(major && { major }),
      ...(year && { year: parseInt(year) }),
      ...(currentCourses && { currentCourses }),
      ...(interests && { interests }),
      ...(preferences && { preferences }),
    });
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/students/:id/history — reading history
router.get('/:id/history', (req, res) => {
  try {
    const student = StudentModel.findById(req.params.id);
    if (!student) return res.status(404).json({ error: 'Student not found' });

    const history = (student.readingHistory || []).map(bookId => {
      const book = BookModel.findById(bookId);
      return book || { id: bookId, title: 'Unknown Book' };
    });
    res.json(history);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
