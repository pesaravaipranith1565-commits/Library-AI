// Book routes — catalog search, availability, details
const express = require('express');
const router = express.Router();
const { BookModel } = require('../models/database');

// GET /api/books — list/search books
router.get('/', (req, res) => {
  try {
    const { search, subject, available, sort } = req.query;
    const filters = {};
    if (search) filters.search = search;
    if (subject) filters.subject = subject;
    if (available === 'true') filters.available = true;

    let books = BookModel.findAll(filters);

    // Sorting
    if (sort === 'popular') {
      books = books.sort((a, b) => (b.borrowedCount || 0) - (a.borrowedCount || 0));
    } else if (sort === 'rating') {
      books = books.sort((a, b) => (b.rating || 0) - (a.rating || 0));
    } else if (sort === 'title') {
      books = books.sort((a, b) => a.title.localeCompare(b.title));
    }

    res.json({
      total: books.length,
      books,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/books/popular — most borrowed books
router.get('/popular', (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 10;
    res.json(BookModel.getPopular(limit));
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/books/subjects — distinct subjects
router.get('/subjects', (req, res) => {
  try {
    const books = BookModel.findAll();
    const subjects = [...new Set(books.map(b => b.subject))].sort();
    res.json(subjects);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/books/:id — single book details
router.get('/:id', (req, res) => {
  try {
    const book = BookModel.findById(req.params.id);
    if (!book) return res.status(404).json({ error: 'Book not found' });
    res.json(book);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/books — add a new book (admin)
router.post('/', (req, res) => {
  try {
    const { title, author, isbn, subject, category, description, tags, totalCopies } = req.body;
    if (!title || !author || !subject) {
      return res.status(400).json({ error: 'title, author, and subject are required' });
    }
    const book = BookModel.create({ title, author, isbn, subject, category, description, tags, totalCopies });
    res.status(201).json(book);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
