# Library AI Agent

An intelligent library assistant powered by **IBM Granite** on **IBM watsonx.ai** (IBM Cloud Lite).

![Library AI Agent](https://img.shields.io/badge/IBM-Granite-0f62fe?style=flat-square&logo=ibm)
![watsonx.ai](https://img.shields.io/badge/watsonx.ai-Enabled-8a3ffc?style=flat-square&logo=ibm)
![Node.js](https://img.shields.io/badge/Node.js-18+-green?style=flat-square&logo=node.js)
![React](https://img.shields.io/badge/React-18-61dafb?style=flat-square&logo=react)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Chat Agent** | Conversational interface powered by IBM Granite for NLP understanding |
| 🔍 **Semantic Search** | Natural language queries matched to the library catalog |
| ⭐ **Personalized Recommendations** | AI-driven book picks tailored to major, courses, and interests |
| 📊 **Real-time Availability** | Instant check of copy availability across all titles |
| 📌 **Smart Reservations** | One-click reservations with automated 14-day due dates |
| 📋 **Waitlist Management** | Join priority waitlists with position tracking and estimated wait times |
| 🎓 **Syllabus Analysis** | Paste a course syllabus — Granite extracts and matches required books |
| 👤 **Student Profiles** | Academic profiles with course history and reading preferences |

---

## 🛠️ Tech Stack

- **Backend**: Node.js + Express.js
- **AI/LLM**: IBM Granite via `@ibm-cloud/watsonx-ai` (IBM Cloud Lite)
- **Database**: LowDB (JSON-based, file-persisted)
- **Frontend**: React 18 + React Router v6
- **Styling**: IBM Design System inspired (IBM Plex Sans font)

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- An **IBM Cloud Lite** account: https://cloud.ibm.com/registration
- A **watsonx.ai** project with API key

### 1. Clone & install dependencies

```bash
# Backend
cd backend
npm install

# Frontend
cd ../frontend
npm install
```

### 2. Configure environment variables

```bash
# In the backend directory:
cp .env.example .env
# Then edit .env with your IBM credentials
```

Fill in your `.env`:

```env
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
```

### 3. Get IBM Cloud credentials

1. Log in to [IBM Cloud](https://cloud.ibm.com)
2. Create an **API Key**: `Manage → Access (IAM) → API Keys → Create`
3. Create a **watsonx.ai project**: Go to [watsonx.ai](https://dataplatform.cloud.ibm.com/wx)
4. Copy your **Project ID** from the project settings

### 4. Seed the database

```bash
cd backend
npm run seed
```

This adds 15 sample books across 6 subjects and 3 student profiles.

### 5. Run the application

```bash
# Terminal 1 — Backend (port 5000)
cd backend
npm run dev

# Terminal 2 — Frontend (port 3000)
cd frontend
npm start
```

Open **http://localhost:3000** in your browser.

---

## 📁 Project Structure

```
LibraryAI/
├── backend/
│   ├── src/
│   │   ├── server.js                 # Express app entrypoint
│   │   ├── services/
│   │   │   └── graniteService.js     # IBM Granite / watsonx.ai integration
│   │   ├── models/
│   │   │   └── database.js           # LowDB models (books, students, reservations)
│   │   ├── routes/
│   │   │   ├── agentRoutes.js        # AI Agent endpoints (chat, recommend, syllabus)
│   │   │   ├── bookRoutes.js         # Book catalog CRUD
│   │   │   ├── studentRoutes.js      # Student profiles
│   │   │   └── reservationRoutes.js  # Reservations & waitlists
│   │   └── data/
│   │       └── seed.js               # Database seeder
│   ├── .env.example                  # Environment template
│   └── package.json
│
└── frontend/
    ├── src/
    │   ├── App.js                    # Router & navbar
    │   ├── context/
    │   │   └── LibraryContext.js     # Global student state
    │   ├── services/
    │   │   └── api.js                # Axios API client
    │   └── pages/
    │       ├── DashboardPage.js      # Home with stats and popular books
    │       ├── ChatPage.js           # AI Agent chat interface
    │       ├── CatalogPage.js        # Browse & search books
    │       ├── ReservationsPage.js   # My reservations & waitlists
    │       └── StudentsPage.js       # Student profiles
    └── package.json
```

---

## 🔌 API Reference

### AI Agent
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/agent/chat` | Send a message to the AI agent |
| POST | `/api/agent/recommend` | Get AI book recommendations for a student |
| POST | `/api/agent/analyze-syllabus` | Extract and match books from a syllabus |
| GET | `/api/agent/chat-history/:studentId` | Get conversation history |
| GET | `/api/agent/search?q=query` | AI-powered semantic search |

### Books
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/books` | List books (supports `?search=`, `?subject=`, `?available=true`, `?sort=`) |
| GET | `/api/books/popular` | Most borrowed books |
| GET | `/api/books/subjects` | All available subjects |
| GET | `/api/books/:id` | Single book details |
| POST | `/api/books` | Add a new book |

### Reservations
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/reservations` | Reserve a book |
| GET | `/api/reservations/student/:id` | Student's reservations |
| DELETE | `/api/reservations/:id` | Cancel reservation |
| POST | `/api/reservations/waitlist` | Join a waitlist |
| DELETE | `/api/reservations/waitlist/:bookId/:studentId` | Leave waitlist |

---

## 🔐 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `WATSONX_API_KEY` | ✅ | IBM Cloud API Key |
| `WATSONX_PROJECT_ID` | ✅ | watsonx.ai Project ID |
| `WATSONX_URL` | ✅ | watsonx.ai service URL (region) |
| `GRANITE_MODEL_ID` | ✅ | Granite model to use |
| `PORT` | ❌ | Backend port (default: 5000) |
| `FRONTEND_URL` | ❌ | Frontend URL for CORS (default: http://localhost:3000) |

---

## 🌐 Supported IBM Granite Models (IBM Cloud Lite)

| Model ID | Description |
|---|---|
| `ibm/granite-4-h-small` | ✅ Recommended — supports text_generation + text_chat |
| `ibm/granite-3-1-8b-base` | Base model (fine-tuning only, not for inference) |

---

Built with ❤️ using IBM Granite on watsonx.ai
