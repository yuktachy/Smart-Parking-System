# Smart Parking System

A smart parking project with:

- a C++ parking fee and utility library
- a Python backend using Flask, Socket.IO, and MongoDB
- a frontend under `web/frontend`

## Project Structure

```text
Smart-Parking-System/
├── cpp/
├── documentation/
└── web/
    ├── backend/
    │   ├── server.py
    │   ├── parking_system.cpp
    │   └── requirement.txt
    └── frontend/
```

## Features

- parking slot management
- vehicle entry and exit flow
- parking fee estimation
- QR code generation and validation
- admin dashboard
- reservation support
- basic authentication
- MongoDB-backed storage
- INR-based parking charges

## Prerequisites

Install these first:

- Python 3.11+ recommended
- `g++`
- MongoDB

On macOS with Homebrew:

```bash
brew install mongodb-community
```

## Backend Setup

Go to the backend folder:

```bash
cd web/backend
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirement.txt
```

Compile the C++ shared library used by the backend:

```bash
g++ -shared -fPIC parking_system.cpp -o libparking.so
```

## Environment Variables

Create `web/backend/.env` with values like:

```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
STRIPE_API_KEY=sk_test_emergent
JWT_SECRET="your-secret"
ADMIN_EMAIL="admin@smartpark.com"
ADMIN_PASSWORD="admin123"
```

## Start MongoDB

If installed with Homebrew:

```bash
brew services start mongodb-community
```

Confirm it is running:

```bash
brew services list | grep mongo
```

## Run the Project

From `web/backend`, start the backend with:

```bash
source .venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001
```

Then open:

```text
http://localhost:8001/index.html
```

## Default Admin Login

- Email: `admin@smartpark.com`
- Password: `admin123`

These are seeded automatically on startup if the database is empty.

## Important Notes

- The backend loads `libparking.so`, so compile it before running the server.
- The correct local command is `uvicorn server:app --host 0.0.0.0 --port 8001`.
- `wsgi.py` is not the preferred local entry point for this setup.
- The backend serves files from `web/frontend`.
- Do not commit `web/backend/.env`, `.venv/`, generated `memory/`, or compiled binaries.

## Troubleshooting

If you get `ServerSelectionTimeoutError`, MongoDB is not running.

If you get an error about `libparking.so`, rebuild it with:

```bash
g++ -shared -fPIC parking_system.cpp -o libparking.so
```

If the page looks blank:

- make sure `uvicorn` is still running
- open `http://localhost:8001/index.html`
- do not open the HTML file directly from disk

## Tech Stack

- C++
- Python
- Flask
- Socket.IO
- MongoDB
- HTML/CSS/JavaScript

