# Native Colab

> **Unified Collaboration Platform** - Self-hosted solution consolidating chat, project management, document collaboration, time tracking, and more.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](docker-compose.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![React 18](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev)

---

## 🚀 Features

### Core Modules

- **💬 Real-Time Chat** - Channels, DMs, threads, file sharing
- **📋 Project Management** - Kanban boards, tasks, workflows, dependencies
- **📄 Document Collaboration** - Rich text editing with real-time co-authoring
- **✍️ Digital Signatures** - Document signing workflows with audit trails
- **⏱️ Time Tracking** - Timesheets, project time, billing reports
- **🎨 Shared Whiteboard** - Collaborative drawing and brainstorming
- **📹 Video/Audio Calls** - WebRTC-powered conferencing
- **📧 Email Integration** - Send, receive, and link emails to projects
- **📅 Calendar** - Scheduling with external calendar sync
- **🔔 Notifications** - Push, email, and in-app notifications
- **📱 Mobile Apps** - iOS and Android native applications

### Replaces

- ❌ Rocket Chat → ✅ Native Colab Chat
- ❌ DocuSign → ✅ Native Colab Signatures
- ❌ Microsoft Office → ✅ Native Colab Documents
- ❌ Asana → ✅ Native Colab Projects
- ❌ ProjectTime → ✅ Native Colab Time Tracking

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + Vite + TypeScript + Tailwind CSS + shadcn/ui |
| **State Management** | TanStack Query + TanStack Router |
| **Backend** | Python FastAPI + SQLAlchemy (async) |
| **Database** | PostgreSQL 15+ |
| **Caching** | Redis 7+ |
| **Real-Time** | Socket.io |
| **WebRTC** | Simple-peer + Mediasoup |
| **File Storage** | MinIO (S3-compatible) |
| **Task Queue** | Celery |
| **Mobile** | React Native |
| **Deployment** | Docker + Docker Compose |

---

## 📋 Prerequisites

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **Node.js** 18+ (for local development)
- **Python** 3.11+ (for local development)
- **PostgreSQL** 15+ (or use Docker)
- **Redis** 7+ (or use Docker)

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/native-colab.git
cd native-colab
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start with Docker Compose

```bash
# Development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 4. Access the Application

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **MinIO Console:** http://localhost:9001

### 5. Default Credentials

```
Email: admin@nativecolab.local
Password: ChangeMe123!
```

**⚠️ Change these immediately after first login!**

---

## 🛠️ Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Mobile Setup

```bash
cd mobile

# Install dependencies
npm install

# iOS
cd ios && pod install && cd ..
npm run ios

# Android
npm run android
```

---

## 📁 Project Structure

```
native-colab/
├── frontend/          # React + Vite web app
├── backend/           # FastAPI application
├── mobile/            # React Native app
├── docker/            # Docker configurations
├── docs/              # Documentation
├── scripts/           # Utility scripts
└── docker-compose.yml # Container orchestration
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm run test
```

### End-to-End Tests

```bash
npm run test:e2e
```

---

## 📦 Deployment

### Docker Compose (Recommended)

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale backend
docker-compose up -d --scale backend=3
```

### Manual Deployment

See [docs/deployment/manual-deployment.md](docs/deployment/manual-deployment.md)

---

## 🔒 Security

- All passwords hashed with bcrypt
- JWT-based authentication
- HTTPS/TLS encryption
- Rate limiting on all endpoints
- CORS protection
- SQL injection prevention
- XSS protection
- CSRF tokens

For security issues, email: security@yourcompany.com

---

## 📊 Monitoring

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3001
- **Application logs:** `docker-compose logs -f backend`

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🗺️ Roadmap

- [x] Architecture design
- [x] Phase 1: Authentication & Core Infrastructure ✅
- [x] Phase 2: Real-Time Chat ✅
- [x] Phase 3: Project Management ✅
- [x] Phase 4: Document Collaboration ✅
- [x] Phase 5: Time Tracking ✅
- [x] Phase 6: Whiteboard & WebRTC ✅
- [x] Phase 7: Analytics & Reporting ✅
- [x] Phase 8: Search & Webhooks ✅
- [ ] Phase 9: Mobile Apps (In Progress)
- [ ] Phase 10: Production Deployment & Testing

### Completed Features

**Backend (14 Modules, 46+ Tables, 244+ Endpoints)**
- ✅ Authentication & Authorization (JWT, refresh tokens, RBAC)
- ✅ Workspace Management (multi-tenancy, members, roles)
- ✅ Project Management (projects, tasks, assignments, comments)
- ✅ Real-Time Chat (channels, DMs, file sharing)
- ✅ Calendar & Events (scheduling, RSVP, recurring events)
- ✅ Document Management (upload, versioning, sharing)
- ✅ Digital Signatures (requests, signing workflows)
- ✅ Time Tracking (timers, billable hours, reporting)
- ✅ Video Meetings (WebRTC, recordings, participants)
- ✅ Collaborative Whiteboards (canvas, real-time sync)
- ✅ Notifications (real-time, preferences, delivery)
- ✅ Universal Search (PostgreSQL FTS, filtering)
- ✅ Webhooks & Integrations (events, deliveries, retries)
- ✅ Analytics & Reporting (events, metrics, exports)

**Frontend (12 Pages, 10 Services, 6,500+ Lines)**
- ✅ Authentication UI (Login, Register)
- ✅ Dashboard (stats, activity feed, quick actions)
- ✅ Chat Interface (channels, messages, real-time)
- ✅ Projects (kanban board, list view, progress tracking)
- ✅ Tasks (filtering, completion, priorities)
- ✅ Time Tracking (live timer, entries, statistics)
- ✅ Calendar (monthly view, event management)
- ✅ Documents (upload/download, grid/list views)
- ✅ Meetings (video interface, meeting room, controls)
- ✅ Whiteboards (drawing tools, collaborative canvas)
- ✅ Universal Search (type filtering, results grouping)
- ✅ API Services (9 service modules with full CRUD)

**Database**
- ✅ 13 Migration files
- ✅ 46+ tables with relationships
- ✅ Full-text search indices
- ✅ Optimized queries with proper indexing

---

## 📞 Support

- **Documentation:** [docs.yourcompany.com](https://docs.yourcompany.com)
- **Issues:** [GitHub Issues](https://github.com/yourusername/native-colab/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/native-colab/discussions)
- **Email:** support@yourcompany.com

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful component library
- [TanStack](https://tanstack.com/) - Powerful state management
- [Socket.io](https://socket.io/) - Real-time communication

---

**Built with ❤️ for modern teams**
