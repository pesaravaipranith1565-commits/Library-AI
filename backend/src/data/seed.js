// Seed script — populates the library database with sample books and students
// Run: npm run seed

require('dotenv').config({ path: require('path').join(__dirname, '../../.env') });
const { BookModel, StudentModel } = require('../models/database');

const sampleBooks = [
  // Computer Science
  {
    title: 'Introduction to Algorithms',
    author: 'Thomas H. Cormen',
    isbn: '978-0262033848',
    subject: 'Computer Science',
    category: 'Algorithms & Data Structures',
    description: 'Comprehensive introduction to algorithms, data structures, and computational theory.',
    tags: ['algorithms', 'data structures', 'computer science', 'programming'],
    totalCopies: 5,
    availableCopies: 3,
    year: 2022,
    edition: '4th',
    level: 'intermediate',
    rating: 4.8,
    borrowedCount: 47,
  },
  {
    title: 'Clean Code',
    author: 'Robert C. Martin',
    isbn: '978-0132350884',
    subject: 'Computer Science',
    category: 'Software Engineering',
    description: 'A handbook of agile software craftsmanship for writing clean, maintainable code.',
    tags: ['clean code', 'software engineering', 'best practices', 'programming'],
    totalCopies: 4,
    availableCopies: 1,
    year: 2008,
    edition: '1st',
    level: 'intermediate',
    rating: 4.7,
    borrowedCount: 62,
  },
  {
    title: 'Artificial Intelligence: A Modern Approach',
    author: 'Stuart Russell & Peter Norvig',
    isbn: '978-0137903955',
    subject: 'Artificial Intelligence',
    category: 'AI & Machine Learning',
    description: 'The most comprehensive and authoritative overview of AI theory and practice.',
    tags: ['artificial intelligence', 'machine learning', 'AI', 'deep learning'],
    totalCopies: 6,
    availableCopies: 4,
    year: 2021,
    edition: '4th',
    level: 'advanced',
    rating: 4.9,
    borrowedCount: 55,
  },
  {
    title: 'Deep Learning',
    author: 'Ian Goodfellow, Yoshua Bengio, Aaron Courville',
    isbn: '978-0262035613',
    subject: 'Artificial Intelligence',
    category: 'AI & Machine Learning',
    description: 'Comprehensive resource covering deep learning techniques, architectures and applications.',
    tags: ['deep learning', 'neural networks', 'machine learning', 'AI'],
    totalCopies: 3,
    availableCopies: 0,
    year: 2016,
    edition: '1st',
    level: 'advanced',
    rating: 4.7,
    borrowedCount: 78,
  },
  {
    title: 'Python Crash Course',
    author: 'Eric Matthes',
    isbn: '978-1718502703',
    subject: 'Computer Science',
    category: 'Programming Languages',
    description: 'A hands-on, project-based introduction to programming with Python.',
    tags: ['python', 'programming', 'beginner', 'projects'],
    totalCopies: 8,
    availableCopies: 5,
    year: 2023,
    edition: '3rd',
    level: 'beginner',
    rating: 4.6,
    borrowedCount: 89,
  },
  {
    title: 'Database System Concepts',
    author: 'Abraham Silberschatz',
    isbn: '978-1260515046',
    subject: 'Computer Science',
    category: 'Databases',
    description: 'Comprehensive introduction to database design, SQL, and database management systems.',
    tags: ['database', 'SQL', 'DBMS', 'data management'],
    totalCopies: 5,
    availableCopies: 2,
    year: 2020,
    edition: '7th',
    level: 'intermediate',
    rating: 4.5,
    borrowedCount: 43,
  },
  {
    title: 'Computer Networks',
    author: 'Andrew S. Tanenbaum',
    isbn: '978-0132126953',
    subject: 'Computer Science',
    category: 'Networking',
    description: 'Complete guide to computer networking fundamentals, protocols, and architectures.',
    tags: ['networking', 'TCP/IP', 'protocols', 'internet'],
    totalCopies: 4,
    availableCopies: 3,
    year: 2021,
    edition: '6th',
    level: 'intermediate',
    rating: 4.4,
    borrowedCount: 38,
  },
  // Mathematics
  {
    title: 'Calculus: Early Transcendentals',
    author: 'James Stewart',
    isbn: '978-1285741550',
    subject: 'Mathematics',
    category: 'Calculus',
    description: 'Classic calculus textbook covering single and multi-variable calculus with applications.',
    tags: ['calculus', 'mathematics', 'derivatives', 'integrals'],
    totalCopies: 10,
    availableCopies: 7,
    year: 2015,
    edition: '8th',
    level: 'intermediate',
    rating: 4.3,
    borrowedCount: 92,
  },
  {
    title: 'Linear Algebra and Its Applications',
    author: 'Gilbert Strang',
    isbn: '978-0030105678',
    subject: 'Mathematics',
    category: 'Linear Algebra',
    description: 'Clear introduction to linear algebra with geometric and applications-based approach.',
    tags: ['linear algebra', 'matrices', 'vectors', 'mathematics'],
    totalCopies: 6,
    availableCopies: 4,
    year: 2016,
    edition: '5th',
    level: 'intermediate',
    rating: 4.7,
    borrowedCount: 67,
  },
  {
    title: 'Probability and Statistics for Engineers and Scientists',
    author: 'Walpole, Myers & Myers',
    isbn: '978-0134115856',
    subject: 'Mathematics',
    category: 'Statistics & Probability',
    description: 'Bridge between probability theory and real-world engineering applications.',
    tags: ['probability', 'statistics', 'engineering math', 'data analysis'],
    totalCopies: 5,
    availableCopies: 3,
    year: 2016,
    edition: '9th',
    level: 'intermediate',
    rating: 4.2,
    borrowedCount: 51,
  },
  // Physics
  {
    title: 'University Physics with Modern Physics',
    author: 'Young & Freedman',
    isbn: '978-0135159552',
    subject: 'Physics',
    category: 'General Physics',
    description: 'Comprehensive university-level physics textbook with modern physics concepts.',
    tags: ['physics', 'mechanics', 'thermodynamics', 'electromagnetism'],
    totalCopies: 8,
    availableCopies: 5,
    year: 2019,
    edition: '15th',
    level: 'intermediate',
    rating: 4.4,
    borrowedCount: 74,
  },
  // Data Science
  {
    title: 'Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow',
    author: 'Aurélien Géron',
    isbn: '978-1098125974',
    subject: 'Data Science',
    category: 'Machine Learning',
    description: 'Practical guide to building intelligent systems using modern ML frameworks.',
    tags: ['machine learning', 'scikit-learn', 'tensorflow', 'keras', 'data science'],
    totalCopies: 4,
    availableCopies: 2,
    year: 2022,
    edition: '3rd',
    level: 'intermediate',
    rating: 4.8,
    borrowedCount: 66,
  },
  {
    title: 'The Elements of Statistical Learning',
    author: 'Hastie, Tibshirani & Friedman',
    isbn: '978-0387848570',
    subject: 'Data Science',
    category: 'Statistics & ML',
    description: 'Mathematical foundations of machine learning and statistical prediction methods.',
    tags: ['statistical learning', 'machine learning', 'data mining', 'statistics'],
    totalCopies: 3,
    availableCopies: 1,
    year: 2016,
    edition: '2nd',
    level: 'advanced',
    rating: 4.6,
    borrowedCount: 44,
  },
  // Business / Economics
  {
    title: 'Principles of Economics',
    author: 'N. Gregory Mankiw',
    isbn: '978-0357038314',
    subject: 'Economics',
    category: 'Microeconomics / Macroeconomics',
    description: 'Clear, student-friendly introduction to economic principles and real-world applications.',
    tags: ['economics', 'microeconomics', 'macroeconomics', 'business'],
    totalCopies: 7,
    availableCopies: 5,
    year: 2020,
    edition: '9th',
    level: 'beginner',
    rating: 4.3,
    borrowedCount: 82,
  },
  {
    title: 'The Lean Startup',
    author: 'Eric Ries',
    isbn: '978-0307887894',
    subject: 'Business',
    category: 'Entrepreneurship',
    description: 'Revolutionary approach to building startups through continuous innovation and learning.',
    tags: ['startup', 'entrepreneurship', 'business', 'agile', 'innovation'],
    totalCopies: 3,
    availableCopies: 2,
    year: 2011,
    edition: '1st',
    level: 'beginner',
    rating: 4.5,
    borrowedCount: 59,
  },
];

const sampleStudents = [
  {
    name: 'Alex Johnson',
    email: 'alex.johnson@university.edu',
    studentId: 'STU001',
    major: 'Computer Science',
    year: 3,
    currentCourses: ['Algorithms', 'Database Systems', 'Operating Systems'],
    interests: ['machine learning', 'web development', 'algorithms'],
    preferences: { preferDigital: false, preferNewEditions: true },
  },
  {
    name: 'Maria Garcia',
    email: 'maria.garcia@university.edu',
    studentId: 'STU002',
    major: 'Data Science',
    year: 2,
    currentCourses: ['Introduction to ML', 'Statistics', 'Python Programming'],
    interests: ['data analysis', 'deep learning', 'visualization'],
    preferences: { preferDigital: true, preferNewEditions: true },
  },
  {
    name: 'James Chen',
    email: 'james.chen@university.edu',
    studentId: 'STU003',
    major: 'Physics',
    year: 1,
    currentCourses: ['Mechanics', 'Calculus I', 'Introduction to Programming'],
    interests: ['quantum physics', 'mathematics', 'simulations'],
    preferences: { preferDigital: false, preferNewEditions: false },
  },
];

async function seed() {
  console.log('🌱 Seeding Library AI Agent database...\n');

  // Clear and seed books
  const { db } = require('../models/database');
  db.set('books', []).write();
  db.set('students', []).write();
  db.set('reservations', []).write();
  db.set('waitlists', []).write();
  db.set('chatHistory', []).write();

  console.log('📚 Adding books...');
  sampleBooks.forEach(book => {
    BookModel.create(book);
    console.log(`   ✅ "${book.title}"`);
  });

  console.log('\n👩‍🎓 Adding sample students...');
  sampleStudents.forEach(student => {
    StudentModel.create(student);
    console.log(`   ✅ ${student.name} (${student.major})`);
  });

  console.log(`\n✨ Seeding complete!`);
  console.log(`   📖 ${sampleBooks.length} books added`);
  console.log(`   🎓 ${sampleStudents.length} students added`);
  console.log('\nRun "npm run dev" to start the server.\n');
}

seed().catch(console.error);
