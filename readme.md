# 🤖 AI-Powered Github PR Automation


This project provides an **AI-powered multi-agent code review system** that analyzes GitHub pull requests, identifies issues (bugs, performance, security, style), and generates structured review reports. It uses **FastAPI** for APIs, **Celery + Redis** for async task processing, and **LLM agents** for code review.


---

## 🚀 Features

- Analyze GitHub pull requests with AI-powered agents.
- AI-agent system for **specialized analysis** (security, bugs, style, performance).
- Asynchronous background processing with **Celery + Redis**.
- Exposes REST API endpoints for:
  - Submitting PRs for analysis
  - Checking task status
  - Fetching structured final reports
- Structured logging with detailed function start/end tracking.
- Dockerized for easy deployment.

---

## 📂 Project Structure

```

├── agents.py              # CrewAI agent setup for PR analysis
├── config.py              # Configuration and environment handling
├── docker-compose.yml     # Multi-service setup (Redis, Web, Worker)
├── Dockerfile             # Build instructions for web/worker containers
├── logger_config.py       # Structured logging utilities
├── main.py                # FastAPI entry point (API routes)
├── models.py              # Pydantic models for requests, responses, reports
├── requirements.txt       # Python dependencies
├── test_api.py            # Pytest tests for API endpoints
├── worker.py              # Celery worker tasks (PR analysis, validation)
└── logs/                  # Log files

````

---

## ⚙️ Tech Stack

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Task Queue**: [Celery](https://docs.celeryq.dev/) + [Redis](https://redis.io/)
- **LLM Integration**: Gemini Model (gemini-1.5-flash) 
- **Validation & Models**: [Pydantic](https://docs.pydantic.dev/)
- **Testing**: [Pytest](https://pytest.org/)
- **Logging**: Structured logging with file + console handlers
- **Containerization**: Docker + Docker Compose

---
## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes | - |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Yes | - |
| `REDIS_URL` | Redis connection URL | No | `redis://localhost:6379/0` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

### GitHub Token Permissions

Your GitHub token needs the following permissions:
- `repo` (for private repositories)
- `public_repo` (for public repositories)
- `pull_requests:read`

### Gemini API Setup

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file
---

## Quick Start
### Prerequisites

1. Docker setup
2. GitHub Personal Access Token
3. Google Gemini API Key

### Installation & Setup


1. **Clone the repository**
   ```bash
   git clone https://github.com/omkardev7/Github_PR_Automation.git
   cd Github_PR_Automation
   ```

2. **Set up environment variables**
  Create a `.env` file in the root directory with the following:

    ```ini
    REDIS_URL=redis://redis:6379/0
    GEMINI_API_KEY=your_gemini_api_key_here
    GITHUB_TOKEN=your_github_personal_access_token_here
    ````
  ####  🐳 Running with Docker
  
  - Build and start services (Redis, Web, Worker):
  
    ```bash
    docker-compose up --build
    ```
  
  - Services:
  
    * **Web API** → `http://localhost:8000`
    * **Redis** → `localhost:6379`
    * **Worker** → Celery background worker

  ####  ▶️ Running Locally (without Docker)
  
  1. Install dependencies:
  
     ```bash
     pip install -r requirements.txt
     ```
  
  2. Start Redis (local or Docker):
  
     ```bash
     redis-server
     ```
  
  3. Start Celery worker:
  
     ```bash
     celery -A worker.celery_app worker -P gevent --loglevel=info
     ```
  
  4. Run FastAPI server:
  
     ```bash
     python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
     ```
  
  ---



## 📡 API Endpoints

### 1. **Analyze Pull Request**

Submit a GitHub PR for analysis:

```http
POST /analyze-pr
Content-Type: application/json
```

**Payload:**

```json
{
  "repo_url": "https://github.com/your-org/your-repo",
  "pr_number": 42,
  "github_token": "ghp_xxx"
}
```

**Response:**

```json
{
  "task_id": "8e2d4e92-...",
  "status": "PENDING"
}
```

---

### 2. **Check Task Status**

```http
GET /status/{task_id}
```

**Response:**

```json
{
  "task_id": "8e2d4e92-..",
  "status": "PROGRESS"
}
```

---

### 3. **Get Results**

```http
GET /results/{task_id}
```

**Successful Response:**

```json
{
  "task_id": "8e2d4e92-...",
  "status": "COMPLETED",
  "results": {
    "files": [
      {
        "name": "main.py",
        "issues": [
          {
            "type": "bug",
            "line": 42,
            "description": "Possible unhandled exception",
            "suggestion": "Add try/except around API call"
          }
        ]
      }
    ],
    "summary": {
      "total_files": 3,
      "total_issues": 5,
      "critical_issues": 2
    }
  }
}
```

---

## 🧪 Testing Instructions

Automated tests are included in `test_api.py`. They cover:

1. **Valid payloads** → ensures `/analyze-pr` accepts correct inputs.
2. **Invalid payloads** → checks for proper validation (`422` errors).
3. **Task lifecycle** → submit PR → check `/status` → fetch `/results`.
4. **Invalid task IDs** → verifies system handles non-existent tasks gracefully.

### Running Tests

1. Ensure Redis and the API server are running:
   (manual):

   ```bash
   celery -A worker.celery_app worker -P gevent --loglevel=info &
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Run tests with pytest:

   ```bash
   pytest -v test_api.py
   ```

3. Example output:

   ```
   test_api.py::test_analyze_pr[valid_payload0] PASSED
   test_api.py::test_analyze_pr[valid_payload1] PASSED
   test_api.py::test_analyze_pr[valid_payload2] PASSED
   test_api.py::test_analyze_pr_invalid_payload PASSED
   test_api.py::test_status_and_results_with_valid_task PASSED
   test_api.py::test_status_with_invalid_task PASSED
   test_api.py::test_results_with_invalid_task PASSED
   ```
   
**What is Tested:**
- ✅ /analyze-pr endpoint with valid and invalid payloads
- ✅ /status/{task_id} with valid and invalid task IDs
- ✅ /results/{task_id} for both valid and invalid task IDs

---
## 🖥️ Example `cURL` Commands

1. **Submit a PR for Analysis**

```bash
curl -X POST http://localhost:8000/analyze-pr \
  -H "Content-Type: application/json" \
  -d '{
        "repo_url": "https://github.com/............",
        "pr_number": 42,
        "github_token": "ghp_xxx"
      }'
```

2. **Check Task Status**

```bash
curl http://localhost:8000/status/{task_id}
```

3. **Get Analysis Results**

```bash
curl http://localhost:8000/results/{task_id}
```

---


## 📜 Logging

* Logs are stored in the `logs/` directory (daily log files).
* Both console + file logging enabled.
* Includes:

  * Function start/end markers
  * Key parameters
  * Errors with context

---

## 🛠️ Design Decisions

- **FastAPI** chosen for high-performance async APIs.

- **Celery** + **Redis** for distributed background task execution.

- **CrewAI** multi-agent system for specialized code review tasks (bugs, style, security, performance).

- **Pydantic** models for strict request/response validation.

- Structured logging with start/end markers and contextual details.

- **Docker** for consistent local & production deployment.

- Config validation ensures required API keys exist (GEMINI_API_KEY, GITHUB_TOKEN).
