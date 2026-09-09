# 🎓 Edusphere: AI-Powered Educational Assistant

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E)

**Edusphere** is a full-stack, production-ready conversational AI platform designed to provide contextual educational assistance. By leveraging a custom **Retrieval-Augmented Generation (RAG)** pipeline powered by sentence transformers, Edusphere intelligently crawls, indexes, and retrieves institutional data to deliver highly accurate, source-backed responses to end users.

![Edusphere Chatbot UI](./ui_screenshot.png)

## ⚡ System Architecture

The project is built on a decoupled client-server architecture, ensuring high cohesion and low coupling:
- **Client Tier (Frontend)**: A highly responsive Single Page Application (SPA) built with **React** and **Vite**. It features localized state management, robust session persistence, and a modular component architecture.
- **Service Tier (Backend)**: A high-performance asynchronous REST API built with **FastAPI**. It handles NLP processing, vector embeddings, and real-time inference.
- **Data Layer**: A lightweight, schema-enforced JSON storage system designed for rapid prototyping, complete with transactional integrity for users, conversations, and feedback data.

## 🚀 Key Engineering Features

- **Custom RAG Pipeline**: Integrates `sentence-transformers` for semantic search across crawled institutional content, providing end-users with dynamic answers and exact source citations (complete with relevance scoring).
- **Intelligent Session Management**: Implements secure, persistent user sessions leveraging HTML5 `localStorage` and synchronized backend states.
- **Adaptive UI/UX**: Fully responsive, mobile-first design implemented with custom CSS. Features fluid flexbox/grid layouts, micro-animations, and dynamic height calculations for seamless cross-device rendering.
- **Telemetry & Feedback Loop**: Asynchronous tracking of user interactions, including granular message-level feedback (Like/Dislike with reasoning), enabling continuous model/response tuning.
- **Concurrent Startup Scripting**: Engineered a unified `.bat` executor that concurrently spins up isolated virtual environments, installs dependencies, and boots both servers instantly.

## 🛠️ Tech Stack

**Frontend Layer:**
- React 18, Vite
- Vanilla CSS (Mobile-First, Flexbox/Grid)
- React Router DOM, React Icons

**Backend Layer:**
- Python 3.x, FastAPI, Uvicorn
- Sentence Transformers (HuggingFace)
- Pydantic (Data Validation & Serialization)

## 📦 Local Deployment

To run this project locally, simply clone the repository and execute the unified startup script.

```bash
# Clone the repository
git clone https://github.com/Yashvi2874/edusphere.git
cd edusphere

# Boot the entire stack (Windows)
# This script automatically creates venvs, installs dependencies, and starts both servers.
start.bat
```

**Manual Startup:**
* **Backend:** `cd Edusphere_backend && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && python app.py`
* **Frontend:** `cd Edusphere_frontend && npm install && npm run dev`

**Access Points:**
- **Web Application:** `http://localhost:5173`
- **REST API Base:** `http://localhost:5001`
- **Swagger Interactive API Docs:** `http://localhost:5001/docs`

## 🗄️ Core API Reference

The system exposes a fully documented RESTful interface. Below are the primary endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/login` | `POST` | Authenticates user and provisions session |
| `/chat` | `POST` | Dispatches query to RAG pipeline & returns context |
| `/new_conversation` | `POST` | Initializes a clean conversation context thread |
| `/feedback` | `POST` | Ingests telemetry & user feedback for tuning |
| `/faqs` | `GET` | Retrieves dynamically categorized quick-actions |

## 🔮 Roadmap & Future Enhancements

As a continuous integration project, the following architectural upgrades are planned:
- [ ] **Data Layer Migration**: Transition from JSON file-store to **PostgreSQL** with SQLAlchemy ORM.
- [ ] **Real-time Streaming**: Upgrade HTTP polling to **WebSockets** for real-time token-by-token response streaming.
- [ ] **Security Hardening**: Implement JWT-based Auth and Bcrypt password hashing.
- [ ] **Containerization**: Dockerize the application (Frontend, Backend, DB) via `docker-compose` for environment-agnostic deployments.

---
*Engineered with precision by [Yashvi2874](https://github.com/Yashvi2874).*
