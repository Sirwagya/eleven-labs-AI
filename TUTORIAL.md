# Tutorial — ElevenLabs Child Profile API

A step-by-step guide to running the app locally, testing it with curl, and connecting it to an ElevenLabs Conversational Agent via a Server Tool.

---

## Table of Contents

1. [What This App Does](#1-what-this-app-does)
2. [Install Prerequisites](#2-install-prerequisites)
3. [Set Up MongoDB](#3-set-up-mongodb)
4. [Set Up the Python Project](#4-set-up-the-python-project)
5. [Start the FastAPI Server](#5-start-the-fastapi-server)
6. [Test the API with curl](#6-test-the-api-with-curl)
7. [Verify Data in MongoDB](#7-verify-data-in-mongodb)
8. [Expose Your Server with ngrok](#8-expose-your-server-with-ngrok)
9. [Configure the ElevenLabs Server Tool](#9-configure-the-elevenlabs-server-tool)
10. [Talk to Your Agent](#10-talk-to-your-agent)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. What This App Does

Your ElevenLabs voice agent has a conversation with a user and collects four pieces of information about a child:

| Field       | Type                   | Example                          |
| ----------- | ---------------------- | -------------------------------- |
| `name`      | string                 | `"Aarav"`                        |
| `age`       | integer (> 0)          | `7`                              |
| `gender`    | `"boy"` or `"girl"`    | `"boy"`                          |
| `interests` | array of strings       | `["dinosaurs", "painting"]`      |

Once the agent has all four fields, it calls the **save_child_profile** server tool, which sends a JSON POST request to your FastAPI backend. The backend validates the data, adds a `created_at` timestamp, and stores it in MongoDB.

**Flow:**

```
User ↔ ElevenLabs Agent ──(server tool call)──▶ FastAPI ──▶ MongoDB
```

---

## 2. Install Prerequisites

### Python 3.11+

```bash
# Check your version
python3 --version

# If needed, install via Homebrew
brew install python@3.11
```

### MongoDB Community 6.x / 7.x

```bash
brew tap mongodb/brew
brew install mongodb-community
```

### ngrok

```bash
brew install ngrok
# — or download from https://ngrok.com/download
# Then authenticate (free account):
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

---

## 3. Set Up MongoDB

Start the MongoDB service:

```bash
brew services start mongodb-community
```

Verify it's running:

```bash
mongosh --eval "db.runCommand({ ping: 1 })"
```

You should see `{ ok: 1 }`.

> MongoDB listens on `mongodb://127.0.0.1:27017` by default — that's exactly what the app expects.

---

## 4. Set Up the Python Project

```bash
# Navigate into the project folder
cd "eleven labs AI"

# Create a virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Check your `.env` file

The project root should contain a `.env` file with:

```dotenv
MONGODB_URL=mongodb://127.0.0.1:27017
DATABASE_NAME=child_profiles
LOG_LEVEL=INFO
```

These are the defaults — you only need to edit this file if your MongoDB is running on a different host/port.

---

## 5. Start the FastAPI Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You'll see output like:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     ✅  MongoDB connection established.
INFO:     Indexes ensured on 'profiles' collection.
```

### Useful URLs

| URL                            | What                           |
| ------------------------------ | ------------------------------ |
| http://localhost:8000/health   | Health check (`{"status":"healthy"}`) |
| http://localhost:8000/docs     | Swagger UI (interactive docs)  |
| http://localhost:8000/redoc    | ReDoc (alternative docs)       |

Open http://localhost:8000/docs in your browser to explore the API visually.

---

## 6. Test the API with curl

Open a **new terminal** (keep the server running in the first one).

### 6.1 — Send a valid profile

```bash
curl -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Aarav",
    "age": 7,
    "gender": "boy",
    "interests": ["dinosaurs", "painting", "cricket"]
  }'
```

**Expected response (200):**

```json
{
  "status": "success",
  "id": "6830a1f2e4b0c5d3a1234567"
}
```

The `id` is the MongoDB `_id` of the inserted document.

### 6.2 — Send with empty interests (valid)

```bash
curl -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Priya",
    "age": 5,
    "gender": "girl",
    "interests": []
  }'
```

This is valid — `interests` can be an empty list.

### 6.3 — Missing a required field (→ 422)

```bash
curl -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Aarav",
    "age": 7,
    "gender": "boy"
  }'
```

**Expected response (422):** Pydantic validation error listing the missing field (`interests`).

### 6.4 — Extra field not allowed (→ 422)

```bash
curl -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Aarav",
    "age": 7,
    "gender": "boy",
    "interests": ["drawing"],
    "favorite_color": "blue"
  }'
```

**Expected response (422):** `"Extra inputs are not permitted"` — the schema disallows unknown fields.

### 6.5 — Invalid age (→ 422)

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

**Expected response (422):** `"Input should be greater than 0"`.

### 6.6 — Invalid gender value (→ 422)

```bash
curl -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Aarav",
    "age": 7,
    "gender": "other",
    "interests": []
  }'
```

**Expected response (422):** `"Input should be 'boy' or 'girl'"`.

---

## 7. Verify Data in MongoDB

After sending a few successful requests, check what's stored:

```bash
mongosh --eval 'use child_profiles; db.profiles.find().pretty()'
```

You'll see documents like:

```json
{
  "_id": ObjectId("6830a1f2e4b0c5d3a1234567"),
  "name": "Aarav",
  "age": 7,
  "gender": "boy",
  "interests": ["dinosaurs", "painting", "cricket"],
  "created_at": ISODate("2026-03-02T10:30:00.000Z")
}
```

### Useful MongoDB queries

```bash
# Count all profiles
mongosh --eval 'use child_profiles; db.profiles.countDocuments()'

# Find by name
mongosh --eval 'use child_profiles; db.profiles.find({name: "Aarav"}).pretty()'

# Find children older than 5
mongosh --eval 'use child_profiles; db.profiles.find({age: {$gt: 5}}).pretty()'

# Delete all profiles (start fresh)
mongosh --eval 'use child_profiles; db.profiles.deleteMany({})'
```

---

## 8. Expose Your Server with ngrok

ElevenLabs needs a public URL to reach your local server. That's what ngrok does.

Open a **new terminal** and run:

```bash
ngrok http 8000
```

You'll see something like:

```
Forwarding   https://a1b2-203-0-113-42.ngrok-free.app -> http://localhost:8000
```

Copy the `https://...ngrok-free.app` URL. This is your **public endpoint**.

### Quick test through ngrok

```bash
curl -X POST https://a1b2-203-0-113-42.ngrok-free.app/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test via ngrok",
    "age": 3,
    "gender": "girl",
    "interests": ["blocks"]
  }'
```

If you get `{"status":"success","id":"..."}`, ngrok is forwarding correctly.

> **Tip:** The free ngrok URL changes every time you restart ngrok. You'll need to update the tool URL in ElevenLabs each time.

---

## 9. Configure the ElevenLabs Server Tool

This is the step that connects your voice agent to your backend.

### Step-by-step in the ElevenLabs dashboard

1. Log in to [elevenlabs.io](https://elevenlabs.io) and open your **Agent**.

2. Go to the **Tools** section (left sidebar or agent settings).

3. Click **Add Tool** → select **Server Tool** (also called Custom Tool / Webhook Tool depending on UI version).

4. Fill in the fields:

   | Field         | Value |
   | ------------- | ----- |
   | **Name**      | `save_child_profile` |
   | **Description** | `Save structured child profile data to the backend database. Call this tool after collecting the child's name, age, gender, and interests from the conversation.` |
   | **URL**       | `https://<your-ngrok-url>/api/save-profile` |
   | **Method**    | `POST` |

5. For the **Parameters / Schema**, paste the contents of `elevenlabs_tool_config.json`:

   ```json
   {
     "type": "object",
     "properties": {
       "name": {
         "type": "string",
         "description": "The child's name"
       },
       "age": {
         "type": "integer",
         "description": "The child's age in years"
       },
       "gender": {
         "type": "string",
         "enum": ["boy", "girl"],
         "description": "The child's gender (boy or girl)"
       },
       "interests": {
         "type": "array",
         "items": { "type": "string" },
         "description": "A list of the child's interests and hobbies"
       }
     },
     "required": ["name", "age", "gender", "interests"]
   }
   ```

6. Click **Save**.

### Update your Agent's system prompt

Make sure the agent knows **when** to use the tool. Add something like this to the agent's system prompt:

> You are a friendly assistant that talks to parents about their child. During the conversation, collect the child's **name**, **age**, **gender** (boy or girl), and **interests** (hobbies, favorite activities). Once you have all four pieces of information, call the `save_child_profile` tool to save the data. Confirm to the user that the profile has been saved.

---

## 10. Talk to Your Agent

1. Make sure all three processes are running:
   - **MongoDB** (`brew services start mongodb-community`)
   - **FastAPI** (`uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`)
   - **ngrok** (`ngrok http 8000`)

2. Open the ElevenLabs Agent playground and start a conversation.

3. Tell the agent about a child, for example:

   > "Hi, I'd like to register my son. His name is Aarav, he's 7 years old, and he loves dinosaurs and painting."

4. The agent will extract the fields, call the `save_child_profile` tool, and confirm.

5. Check your terminal — you should see logs like:

   ```
   INFO | app.routes:save_profile:46 — Received profile for: Aarav (age 7)
   INFO | app.routes:save_profile:53 — ✅  Saved profile 6830a1f2... for Aarav
   ```

6. Verify in MongoDB:

   ```bash
   mongosh --eval 'use child_profiles; db.profiles.find().sort({created_at: -1}).limit(1).pretty()'
   ```

---

## 11. Troubleshooting

### "Connection refused" when starting the server

MongoDB isn't running. Start it:

```bash
brew services start mongodb-community
```

### 422 errors from ElevenLabs

The agent is sending data that doesn't match the schema. Check:
- Is `age` an integer (not a string like `"7"`)?
- Is `gender` exactly `"boy"` or `"girl"` (not `"male"` or `"Boy"`)?
- Is `interests` an array (not a single string)?

Look at the FastAPI logs for the detailed validation error.

### ngrok URL not working

- Make sure ngrok is still running (free URLs expire after ~2 hours of inactivity).
- Verify the URL ends with `/api/save-profile` in the ElevenLabs tool config.
- Test the ngrok URL directly with curl first (see [Section 8](#8-expose-your-server-with-ngrok)).

### Agent doesn't call the tool

- Check that the tool is **enabled** in the agent settings.
- Make sure the agent's system prompt instructs it to call the tool.
- Verify the tool name matches exactly: `save_child_profile`.

### "Database not initialised" error

The lifespan event didn't run, usually because:
- MongoDB wasn't reachable at startup.
- You're importing `app` incorrectly. Always start with `uvicorn app.main:app`.

### Reset everything

```bash
# Stop the server (Ctrl+C)
# Clear all saved profiles
mongosh --eval 'use child_profiles; db.profiles.deleteMany({})'
# Restart
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Quick Reference

```bash
# ── Start everything ──────────────────────────────
brew services start mongodb-community
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  # Terminal 1
ngrok http 8000                                              # Terminal 2

# ── Test ──────────────────────────────────────────
curl -s -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{"name":"Aarav","age":7,"gender":"boy","interests":["dinosaurs"]}' | python3 -m json.tool

# ── Check DB ──────────────────────────────────────
mongosh --eval 'use child_profiles; db.profiles.find().pretty()'

# ── Stop everything ──────────────────────────────
# Ctrl+C on uvicorn and ngrok
brew services stop mongodb-community
```
