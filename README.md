#  FastAPI Endpoint Builder

A minimalist, high-utility visual environment (IDE) and CLI tool designed to eliminate boilerplate code when scaling **FastAPI** microservices. 

Stop manually creating `routers.py`, `schemas.py`, `models.py`, configuring asynchronous connections, or copy-pasting JWT and Pytest configurations. **Click it out in UI, get clean architecture instantly.**

---

##  Features

- **Monochrome Tech UI**: Clean, high-contrast, zero-distraction layout optimized for developers.
- **Dual Database Core**: One-click switch between **Synchronous SQLite** (for fast prototyping) and **Asynchronous PostgreSQL** (via `asyncpg` & SQLAlchemy 2.0).
- **Embedded JWT Authentication**: Toggle secure route protection with a single checkbox (injects `get_current_user` dependency automatically).
- **Auto-Generated Tests**: Instantly creates ready-to-run `pytest` environments using `TestClient`.
- **Docker Ready**: Automatically drops production-grade `Dockerfile`, `docker-compose.yml`, and `requirements.txt` into your project root based on your database choice.
- **Zero Disk Bloat**: Completely Virtual Cloud-ready mode. Generates code on the fly without writing temporary files to your physical disk.

---

##  Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, Jinja2 Templates, Pydantic v2.
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, Lucide Icons.

---

##  Quick Start (Local Development)

### 1. Backend Setup
Navigate to the backend directory, install dependencies, and launch the core generator API:
```bash
cd backend
pip install fastapi uvicorn jinja2 pydantic pyjwt
python main.py
```
*The API will start running at `http://127.0.0.1:8000`*

### 2. Frontend Setup
In a new terminal window, navigate to the frontend directory, install npm packages, and spin up Next.js:
```bash
cd fastapi-builder-web
npm install
npm run dev
```
*Open `http://localhost:3000` in your browser to launch the IDE.*

---

## 🐳 Running Generated Code via Docker

Deploying your newly created microservice is incredibly simple:

1. Extract the downloaded `.zip` archive into an empty folder.
2. Ensure **Docker Desktop** is active.
3. Open your terminal in the extracted directory and type:
```bash
docker compose up --build
```
Docker will automatically pull down PostgreSQL images, install required system libraries, execute database migrations/schemas, map network ports, and boot up your FastAPI instance. 
* Access your new interactive Swagger documentation at: `http://127.0.0`

---
