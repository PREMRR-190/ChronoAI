# ChronoAI - AI-Powered Productivity Suite

ChronoAI is a full-stack productivity application designed to help users manage tasks, schedules, and daily habits with intelligent insights. The project consists of a Flask-based backend API, React/Vite frontend applications, and machine learning modules for predictive analytics.

## Table of Contents
- [Project Structure](#project-structure)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup (chronoai-frontend)](#frontend-setup-chronoai-frontend)
  - [Alternative Frontend (frontend)](#alternative-frontend-frontend)
  - [ML Module Setup](#ml-module-setup)
- [Running the Application](#running-the-application)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Further Development](#further-development)
- [Contributing](#contributing)
- [License](#license)

## Project Structure
```
ML/
├── backend/                  # Flask REST API
│   ├── app.py                # Main application file
│   └── requirements.txt      # Python dependencies
├── chronoai-frontend/        # Primary React/Vite frontend
│   ├── src/                  # Source code
│   ├── public/               # Static assets
│   ├── package.json
│   └── vite.config.js
├── frontend/                 # Alternative/react frontend (may be legacy)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── ml/                       # Machine learning utilities
│   ├── module3.py            # Core ML logic
│   ├── data/                 # Training data
│   ├── models/               # Saved models
│   └── requirements.txt
└── chronoai-backend.zip      # Backup of backend (ignore)
```

## Features
- **Task Management**: Create, read, update, delete tasks with priority and time estimates.
- **Scheduling**: Add daily schedule items with time-bound activities.
- **Habit Tracking**: Log sleep, wake, screen, and study times.
- **RESTful API**: Well-documented endpoints for all entities.
- **Machine Learning**: Placeholder for predictive task duration and optimal scheduling.
- **Responsive UI**: Built with React and Vite for fast development and production builds.
- **CORS Enabled**: Allows frontend and backend to run on different ports/domains.

## Tech Stack
### Backend
- **Language**: Python 3.9+
- **Framework**: Flask
- **Database**: MongoDB (via PyMongo)
- **CORS**: Flask-CORS
- **Dependencies**: See `backend/requirements.txt`

### Frontend (chronoai-frontend & frontend)
- **Language**: JavaScript (ES6+) / TypeScript (if configured)
- **Framework**: React 19
- **Build Tool**: Vite
- **Styling**: CSS (can be extended with Tailwind, etc.)
- **Linting**: Oxlint

### ML Module
- **Language**: Python
- **Libraries**: pandas, numpy, scikit-learn, joblib
- **Purpose**: Data preprocessing, model training, prediction (to be integrated)

## Setup Instructions

### Prerequisites
- [Node.js](https://nodejs.org/) (v18+ recommended)
- [Python](https://www.python.org/) (3.9+)
- [MongoDB](https://www.mongodb.com/) (local instance or Atlas)
- Git

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Ensure MongoDB is running on `mongodb://127.0.0.1:27017/` (or update `MONGO_URI` in `app.py`).
5. The backend will create the database `ChronoAI` and collections automatically on first run.

### Frontend Setup (chronoai-frontend)
1. Navigate to the frontend directory:
   ```bash
   cd chronoai-frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   The app will be available at `http://localhost:5173` (or another port if 5173 is in use).

### Alternative Frontend (frontend)
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

### ML Module Setup
1. Navigate to the ml directory:
   ```bash
   cd ml
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Explore `module3.py` for available functions. Integrate with backend as needed.

## Running the Application
To run the full stack locally:
1. Start MongoDB (if not running as a service).
2. Start the backend:
   ```bash
   cd backend
   python app.py
   ```
   Backend runs on `http://127.0.0.1:5000`.
3. Start the frontend(s):
   ```bash
   cd chronoai-frontend
   npm run dev
   ```
   (or `cd frontend && npm run dev` for the alternative)
4. Open your browser to the frontend URL (usually `http://localhost:5173`).

## Environment Variables
Currently, the backend uses a hardcoded MongoDB URI. For production, consider using environment variables:
- Create a `.env` file in the backend directory:
  ```
  MONGO_URI=mongodb+srv://<username>:<password>@cluster0.example.mongodb.net/ChronoAI
  PORT=5000
  DEBUG=False
  ```
- Modify `app.py` to load from `os.getenv`.

## API Endpoints
### Tasks
- `GET /api/tasks` - Retrieve all tasks (sorted by creation date descending)
- `POST /api/tasks` - Create a new task
  - Body: `{ "title": string, "priority": "Low"/"Medium"/"High", "hours": number }`
- `PUT /api/tasks/<task_id>` - Update task completion status
  - Body: `{ "completed": boolean }`
- `DELETE /api/tasks/<task_id>` - Delete a task

### Schedule
- `GET /api/schedule` - Retrieve all schedule items
- `POST /api/schedule` - Add a schedule item
  - Body: `{ "time": string (HH:MM), "activity": string }`
- `DELETE /api/schedule/<schedule_id>` - Delete a schedule item

### Habits
- `GET /api/habits` - Retrieve the most recent habit entry
- `POST /api/habits` - Save a new habit entry
  - Body: `{ "sleep_time": string (HH:MM), "wake_time": string (HH:MM), "screen_time": number, "study_time": number }`

## Further Development
- **Authentication**: Add user authentication (JWT or session-based) to protect endpoints.
- **ML Integration**: Train models on task completion times to provide smart scheduling suggestions.
- **Dashboard**: Visualize productivity trends with charts (using a library like Chart.js or Recharts).
- **Notifications**: Implement email/push notifications for upcoming tasks or habit reminders.
- **Dockerize**: Create Dockerfiles for backend and frontend for easy deployment.
- **Testing**: Add unit and integration tests (PyTest for backend, Vitest/Jest for frontend).
- **Deployment**: Deploy to platforms like Render, Vercel, or AWS.

## Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

Please ensure your code follows the existing style and includes appropriate tests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (to be added).

## Acknowledgments
- Inspired by personal productivity challenges.
- Built with Flask, React, Vite, and MongoDB.
- Special thanks to the open-source community for the libraries used.