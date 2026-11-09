// AI Agent routes — the core intelligence layer
// Handles: chat, NLP search, personalized recommendations, syllabus analysis

const express = require('express');
const router = express.Router();
const granite = require('../services/graniteService');
const { BookModel, StudentModel, WaitlistModel, ReservationModel, ChatModel } = require('../models/database');

/**
 * POST /api/agent/chat
 * Main conversational endpoint — understands intent and takes action
 */
router.post('/chat', async (req, res) => {
  try {
    const { message, studentId } = req.body;
    if (!message) return res.status(400).json({ error: 'message is required' });

    const student = studentId ? StudentModel.findById(studentId) : null;

    // Save user message
    if (studentId) {
      ChatModel.save(studentId, 'user', message);
    }

    // Step 1: Understand the query with IBM Granite NLP
    const understanding = await granite.understandQuery(message, student || {});
    console.log('[Granite NLP]', understanding);

    let responseData = {};
    let agentMessage = '';

    // Step 2: Route by intent
    switch (understanding.intent) {
      case 'search_book': {
        const books = BookModel.searchSemantic(understanding.keywords || [understanding.subject]);
        if (books.length > 0) {
          agentMessage = `I found ${books.length} book(s) matching your query about "${understanding.subject}". Here are the top results:`;
          responseData = { books: books.slice(0, 6), intent: 'search_book' };
        } else {
          agentMessage = `I couldn't find books specifically about "${understanding.subject}". Let me show you our full catalog — you might find something helpful!`;
          responseData = { books: BookModel.getPopular(6), intent: 'no_results' };
        }
        break;
      }

      case 'get_recommendation': {
        if (!student) {
          agentMessage = 'To give you personalized recommendations, please set up your student profile first. You can register using the Students tab!';
          responseData = { intent: 'get_recommendation', requiresProfile: true };
        } else {
          const allBooks = BookModel.findAll();
          const aiResponse = await granite.generateRecommendations(student, allBooks, understanding.summary);
          
          // Also find relevant books from DB
          const relatedBooks = BookModel.searchSemantic(
            [...(student.interests || []), ...(student.currentCourses || [])]
          );
          
          agentMessage = aiResponse;
          responseData = {
            intent: 'get_recommendation',
            suggestedBooks: relatedBooks.slice(0, 6),
            studentProfile: { name: student.name, major: student.major },
          };
        }
        break;
      }

      case 'check_availability': {
        const bookTitle = understanding.bookTitle || understanding.subject;
        const books = BookModel.searchSemantic([bookTitle, ...( understanding.keywords || [])]);
        if (books.length === 0) {
          agentMessage = `I couldn't find a book titled "${bookTitle}" in our catalog. Try a different title or check the full catalog.`;
          responseData = { intent: 'check_availability', found: false };
        } else {
          const book = books[0];
          if (book.availableCopies > 0) {
            agentMessage = `✅ Good news! "${book.title}" by ${book.author} is available — ${book.availableCopies} of ${book.totalCopies} copies are currently free.`;
          } else {
            const waitlistCount = WaitlistModel.getForBook(book.id).length;
            agentMessage = `📋 "${book.title}" is currently fully borrowed (${book.totalCopies} copies all out). There are ${waitlistCount} people on the waitlist. Would you like to join?`;
          }
          responseData = { intent: 'check_availability', books, canReserve: books[0].availableCopies > 0 };
        }
        break;
      }

      case 'reserve_book': {
        const bookTitle = understanding.bookTitle || understanding.subject;
        const books = BookModel.searchSemantic([bookTitle]);
        if (books.length > 0 && student) {
          const book = books[0];
          agentMessage = book.availableCopies > 0
            ? `"${book.title}" is available! Use the Reserve button below to complete your reservation.`
            : `"${book.title}" is fully borrowed right now. You can join the waitlist and be notified when it returns!`;
          responseData = {
            intent: 'reserve_book',
            book,
            canReserve: book.availableCopies > 0,
            canWaitlist: book.availableCopies === 0,
          };
        } else {
          agentMessage = 'To reserve a book, please tell me the exact title. Also make sure you have a student profile set up!';
          responseData = { intent: 'reserve_book', requiresTitle: true };
        }
        break;
      }

      case 'join_waitlist': {
        const bookTitle = understanding.bookTitle || understanding.subject;
        const books = BookModel.searchSemantic([bookTitle]);
        if (books.length > 0) {
          const book = books[0];
          const waitlist = WaitlistModel.getForBook(book.id);
          agentMessage = `The waitlist for "${book.title}" has ${waitlist.length} student(s). Joining now means an estimated wait of ${waitlist.length * 14} days.`;
          responseData = { intent: 'join_waitlist', book, waitlistSize: waitlist.length };
        } else {
          agentMessage = 'Please specify which book you\'d like to join the waitlist for.';
          responseData = { intent: 'join_waitlist', requiresTitle: true };
        }
        break;
      }

      case 'get_syllabus_books': {
        if (student && student.currentCourses?.length) {
          const relevantBooks = BookModel.searchSemantic(student.currentCourses);
          agentMessage = `Based on your courses (${student.currentCourses.join(', ')}), here are the books most relevant to your syllabus:`;
          responseData = { intent: 'get_syllabus_books', books: relevantBooks.slice(0, 8) };
        } else {
          agentMessage = 'To find books for your syllabus, please update your profile with your current courses, or paste your syllabus text for me to analyze!';
          responseData = { intent: 'get_syllabus_books', requiresCourses: true };
        }
        break;
      }

      default: {
        const context = student ? {
          'Student name': student.name,
          'Major': student.major,
          'Current courses': student.currentCourses?.join(', '),
        } : {};
        agentMessage = await granite.generateAgentResponse(message, context);
        responseData = {
          intent: 'general_help',
          suggestedBooks: BookModel.getPopular(4),
        };
      }
    }

    // Save agent response
    if (studentId) {
      ChatModel.save(studentId, 'assistant', agentMessage, { intent: understanding.intent });
    }

    res.json({
      message: agentMessage,
      understanding,
      ...responseData,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error('Agent chat error:', err);
    res.status(500).json({ error: 'The AI agent encountered an error. Please try again.', details: err.message });
  }
});

/**
 * POST /api/agent/recommend
 * Standalone recommendation endpoint for a student
 */
router.post('/recommend', async (req, res) => {
  try {
    const { studentId, query } = req.body;
    if (!studentId) return res.status(400).json({ error: 'studentId is required' });

    const student = StudentModel.findById(studentId);
    if (!student) return res.status(404).json({ error: 'Student not found' });

    const allBooks = BookModel.findAll();
    const aiResponse = await granite.generateRecommendations(student, allBooks, query || '');

    const keywords = [
      ...(student.interests || []),
      ...(student.currentCourses || []),
      student.major,
    ].filter(Boolean);
    const relatedBooks = BookModel.searchSemantic(keywords);

    res.json({
      studentName: student.name,
      aiRecommendation: aiResponse,
      suggestedBooks: relatedBooks.slice(0, 8),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * POST /api/agent/analyze-syllabus
 * Extract required/recommended books from a syllabus text
 */
router.post('/analyze-syllabus', async (req, res) => {
  try {
    const { syllabusText, studentId } = req.body;
    if (!syllabusText) return res.status(400).json({ error: 'syllabusText is required' });

    const analysis = await granite.analyzeSyllabus(syllabusText);

    // Try to find the books in our catalog
    const allMentioned = [...(analysis.required || []), ...(analysis.recommended || [])];
    const catalogMatches = allMentioned.map(mentioned => {
      const found = BookModel.searchSemantic([mentioned.title, mentioned.author].filter(Boolean));
      return { mentioned, catalogBook: found[0] || null };
    });

    res.json({
      analysis,
      catalogMatches,
      topicBooks: BookModel.searchSemantic(analysis.topics || []).slice(0, 6),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/agent/chat-history/:studentId
 * Fetch conversation history for a student
 */
router.get('/chat-history/:studentId', (req, res) => {
  try {
    const history = ChatModel.getHistory(req.params.studentId, 30);
    res.json(history);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/agent/search
 * AI-powered semantic search
 */
router.get('/search', async (req, res) => {
  try {
    const { q, studentId } = req.query;
    if (!q) return res.status(400).json({ error: 'q (query) is required' });

    const student = studentId ? StudentModel.findById(studentId) : null;
    const understanding = await granite.understandQuery(q, student || {});
    const books = BookModel.searchSemantic(understanding.keywords || [q]);

    res.json({
      query: q,
      understanding,
      results: books,
      total: books.length,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
