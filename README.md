# ElevenLabs Child Profile API

FastAPI + MongoDB backend that receives **structured JSON** from an ElevenLabs Server Tool and stores child profiles.

## What this app does

- Exposes `POST /api/save-profile` for direct tool calls from ElevenLabs
- Validates strict schema with Pydantic
- Stores profiles in MongoDB (`child_profiles.profiles`)
- Adds `created_at` (UTC) automatically
- Provides `GET /health` for liveness checks

---

## Required JSON schema

```json
{
  "name": "string",
  "age": 7,
  "gender": "boy",
  "interests": ["string"]
}
```

Validation rules:
- `age` must be `> 0`
- `gender` must be `boy | girl`
- `interests` must be an array (can be empty)
- extra fields are rejected

---

## Local setup

### 1) Prerequisites

- Python 3.11+
- MongoDB Community (local)
- ngrok

### 2) Install deps

```bash
cd "eleven labs AI"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure environment

Create/update `.env` in project root:

```dotenv
MONGODB_URL=mongodb://127.0.0.1:27017
DATABASE_NAME=child_profiles
LOG_LEVEL=INFO
```

### 4) Start MongoDB

```bash
brew services start mongodb-community
mongosh --eval "db.runCommand({ ping: 1 })"
```

### 5) Run API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Available endpoints:
- `http://localhost:8000/health`
- `http://localhost:8000/docs`

---

## ElevenLabs Server Tool setup (priority)

### 1) Start ngrok tunnel

```bash
ngrok http 8000
```

Copy the HTTPS URL (example: `https://abcd-1234.ngrok-free.app`).

### 2) Tool endpoint URL

Use:

```text
https://<your-ngrok-url>/api/save-profile
```

### 3) Create tool in ElevenLabs

Use this config (same as `elevenlabs_tool_config.json`):

```json
{
  "name": "save_child_profile",
  "description": "Save structured child profile to backend",
  "parameters": {
    "type": "object",
    "properties": {
      "name": { "type": "string" },
      "age": { "type": "integer" },
      "gender": {
        "type": "string",
        "enum": ["male", "female"]
      },
      "type": {
        "type": "string",
        "enum": ["boy", "girl"]
      },
      "interests": {
        "type": "array",
        "items": { "type": "string" }
      }
    },
    "required": ["name", "age", "gender", "type", "interests"]
  }
}
```

### 4) Agent instruction suggestion

Tell the agent to:
- collect `name`, `age`, `gender`, `type`, `interests`
- call `save_child_profile` only when all required fields are available
- keep `interests` as an array

---

## API test with curl

### Successful request

```bash
curl -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Aarav",
    "age": 7,
    "gender": "boy",
    "interests": ["dinosaurs", "painting"]
  }'
```

Response:

```json
{
  "status": "success",
  "id": "69a5a5e0c5de59bc81181cc4"
}
```

### Validation failure example

```bash
curl -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Aarav",
    "age": 0,
    "gender": "boy",
    "interests": []
  }'
```

Expected: `422 Unprocessable Entity`

---

## Verify document in MongoDB

```bash
mongosh child_profiles --quiet --eval 'db.profiles.find().sort({created_at:-1}).limit(1).toArray()'
```

Expected shape:

```json
{
  "_id": "ObjectId(...)",
  "name": "Aarav",
  "age": 7,
  "gender": "boy",
  "interests": ["dinosaurs", "painting"],
  "created_at": "ISODate(...)"
}
```

---

## Project structure

```text
eleven labs AI/
├── .env
├── README.md
├── TUTORIAL.md
├── elevenlabs_tool_config.json
├── requirements.txt
└── app/
    ├── __init__.py
    ├── config.py
    ├── database.py
    ├── main.py
    ├── models.py
    └── routes.py
```

For a longer walkthrough, see `TUTORIAL.md`.
