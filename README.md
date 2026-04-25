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
- MongoDB for persistent storage
- a C++ compiler only if you want to build the optional native parking library

Windows notes:

- the backend can run without MongoDB and without the native DLL for local testing
- when MongoDB is unavailable, the app falls back to in-memory storage
- when `libparking.dll` is unavailable, the app falls back to Python implementations of the parking helpers

## Backend Setup

Go to the backend folder:

```powershell
cd web/backend
```

Install dependencies:

```powershell
py -3.11 -m pip install -r requirement.txt
```

Optional: copy `web/backend/.env.example` to `web/backend/.env` and adjust values as needed:

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
CORS_ORIGINS=*
STRIPE_API_KEY=sk_test_emergent
JWT_SECRET=your-secret
ADMIN_EMAIL=admin@smartpark.com
ADMIN_PASSWORD=admin123
```

Optional: build the native C++ library on Windows if you have `g++` installed:

```powershell
g++ -shared parking_system.cpp -o libparking.dll
```

## Start MongoDB

If MongoDB is installed and you want persistent data, start it before launching the backend.

Example:

```powershell
mongod
```

## Run the Project

From `web/backend`, start the backend with:

```powershell
.\start_backend.ps1
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

- The simplest local start command on Windows is `.\start_backend.ps1`.
- The direct Python command is `py -3.11 -m uvicorn server:app --host 0.0.0.0 --port 8001`.
- The backend prefers `libparking.dll` on Windows, but can start without it.
- `wsgi.py` is not the preferred local entry point for this setup.
- The backend serves files from `web/frontend`.
- Do not commit `web/backend/.env`, `.venv/`, generated `memory/`, or compiled binaries.

## Troubleshooting

If you get `ServerSelectionTimeoutError`, MongoDB is not running or your `MONGO_URL` is wrong.

If you want persistent data, make sure MongoDB is running and `web/backend/.env` contains `MONGO_URL` and `DB_NAME`.

If you want the native library and get an error about `libparking.dll`, rebuild it with:

```powershell
g++ -shared parking_system.cpp -o libparking.dll
```

If the page looks blank:

- make sure the backend is still running
- open `http://localhost:8001/index.html`
- do not open the HTML file directly from disk

## Tech Stack

- C++
- Python
- Flask
- Socket.IO
- MongoDB
- HTML/CSS/JavaScript

