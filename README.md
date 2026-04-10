# Consensia

Consensia is a self-hosted idea management app. Capture ideas, organise them into books, tag and search them — and let the built-in ML pipeline automatically cluster them into a meaningful Table of Contents and surface semantically similar ideas.

**Backend:** FastAPI + SQLite + ChromaDB &nbsp;|&nbsp; **Frontend:** React + Vite + Tailwind &nbsp;|&nbsp; **Auth:** TOTP (Google Authenticator) + JWT &nbsp;|&nbsp; **Deployment:** Raspberry Pi 4 + nginx + Gunicorn

---

## Features

- **Idea CRUD** — create, edit, and delete ideas with rich text content and tags
- **Books** — group ideas into workspaces; assign multiple collaborators per book
- **Semantic similarity** — find ideas with related meaning using sentence embeddings
- **Auto Table of Contents** — ML clustering (UMAP + Agglomerative) organises ideas into sections and chapters automatically
- **Voting** — upvote / downvote ideas to surface the best ones
- **TOTP authentication** — no passwords; login with Google Authenticator
- **Role-based access** — admin users can manage accounts via the Admin Panel

---

## Documentation

| Document | Audience | Description |
|---|---|---|
| [Installation Guide](docs/installation.md) | Everyone | Step-by-step setup for local dev and Raspberry Pi production |
| [User Guide](docs/user-guide.md) | End users | Quick start and feature walkthroughs |
| [Architecture](docs/architecture.md) | Developers | C4 diagrams, database schema, auth flow, design decisions |
| [API Reference](docs/api-reference.md) | Developers | All 26 endpoints with request/response schemas |
| [Data Science](docs/data-science.md) | Developers | Embedding, clustering, and TOC generation pipeline |
| [Contributing](docs/contributing.md) | Developers | TDD workflow, quality gates, adding features |
| [Operations](docs/operations.md) | Operators | Service management, logs, backup, troubleshooting |

---

## Quick Start (Local Development)

```bash
# Clone
git clone https://github.com/pseroul/consensia.git
cd consensia

# Backend
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
mkdir -p data
# Create backend/data/site.json (see installation guide)
export JWT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
python authenticator.py your@email.com   # add first user
python main.py                           # → http://localhost:8000

# Frontend (new terminal)
cd frontend && npm install
npm run dev                              # → http://localhost:5173
```

Full instructions, including Raspberry Pi deployment and HTTPS setup: [docs/installation.md](docs/installation.md)

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI 0.128, Python 3.11 |
| Database | SQLite (via pandas) |
| Vector store | ChromaDB 1.4 |
| Embeddings | SentenceTransformers `all-distilroberta-v1` |
| Clustering | UMAP + AgglomerativeClustering (scikit-learn) |
| Auth | pyotp (TOTP) + python-jose (JWT HS256) |
| Frontend | React 19, Vite 7, TailwindCSS 4 |
| Production server | Gunicorn + Uvicorn |
| Reverse proxy | nginx |

---

## License

See [LICENSE](LICENSE).
