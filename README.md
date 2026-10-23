# NARI-KAVACH — AI-Powered Women's Safety System

## Overview

NARI-KAVACH is a women's safety application designed to support emergency response, location tracking, and communication with trusted emergency contacts.

The project consists of a React frontend and a FastAPI backend, with PostgreSQL used for data storage.

## Technology Stack

- **Frontend:** React, Vite, JavaScript, CSS
- **Backend:** Python, FastAPI
- **Database:** PostgreSQL
- **API Documentation:** FastAPI Swagger UI

## Prerequisites

Install the following before running the project:

- Git
- Python 3.10 or a compatible version required by the backend dependencies
- Node.js and npm
- PostgreSQL
- A code editor such as Visual Studio Code

## Project Structure

```text
MAJOR PROJECT/
├── Backend/
│   ├── app/
│   ├── requirements.txt
│   └── .env.example
├── Frontend/
│   ├── src/
│   ├── package.json
│   └── package-lock.json
├── .gitignore
└── README.md
```

*The structure above is illustrative. The actual files in the repository may differ.*

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/Madebyrishi04/NARI-KAVACH.git
cd NARI-KAVACH
```

### 2. Configure the backend

Open a terminal in the `Backend` directory.

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the backend dependencies:

```powershell
pip install -r requirements.txt
```

Create your local `.env` file using the provided `.env.example` as a reference. Fill in your own database credentials, JWT secret, and any other required configuration.

Never commit your actual `.env` file or share its secrets.

### 3. Configure PostgreSQL

Install and start PostgreSQL. Create a database for the application and configure the backend environment variables to match your local database settings.

Apply any required database migrations or initialization steps before starting the application.

### 4. Start the backend

From the `Backend` directory, with the virtual environment activated, run:

```powershell
uvicorn app.main:app --reload
```

The backend should be available at:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

### 5. Start the frontend

Open a second terminal and navigate to the `Frontend` directory.

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the local URL printed by Vite in your terminal, typically:

http://localhost:5173

## Environment Configuration

The backend requires environment variables for its database connection, authentication, and any configured external services.

Use `Backend/.env.example` to identify the required variable names. Supply your own values locally.

Do not commit passwords, API keys, email app passwords, or production credentials.

## Team Setup

Each team member should:

1. Clone the repository.
2. Install the backend and frontend dependencies.
3. Configure their own environment variables.
4. Set up their local database.
5. Start the backend and frontend in separate terminals.
6. Test the application using the frontend and API documentation.

## Development Status

This project is under development. Features that depend on database setup, email configuration, external services, or other environment-specific settings may require additional configuration.

## Contributors

NARI-KAVACH development team.
