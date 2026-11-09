require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');

const bookRoutes = require('./routes/bookRoutes');
const studentRoutes = require('./routes/studentRoutes');
const agentRoutes = require('./routes/agentRoutes');
const reservationRoutes = require('./routes/reservationRoutes');

const app = express();
const PORT = process.env.PORT || 5000;

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,
  message: { error: 'Too many requests, please try again later.' },
});
app.use('/api/', limiter);

// Logging & parsing
app.use(morgan('dev'));
app.use(express.json({ limit: '10kb' }));
app.use(express.urlencoded({ extended: true }));

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'Library AI Agent',
    timestamp: new Date().toISOString(),
    ibmGranite: process.env.WATSONX_API_KEY ? 'configured' : 'missing credentials',
  });
});

// API routes
app.use('/api/books', bookRoutes);
app.use('/api/students', studentRoutes);
app.use('/api/agent', agentRoutes);
app.use('/api/reservations', reservationRoutes);

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
  });
});

app.listen(PORT, () => {
  console.log(`\n🚀 Library AI Agent Server running on http://localhost:${PORT}`);
  console.log(`📚 IBM Granite integration: ${process.env.WATSONX_API_KEY ? '✅ Ready' : '⚠️  Missing credentials'}`);
  console.log(`🌐 Frontend: ${process.env.FRONTEND_URL || 'http://localhost:3000'}\n`);
});

module.exports = app;
