# Tutorial — ElevenLabs Child Profile API

A step-by-step guide to running the app locally, testing all endpoints, and connecting it to an ElevenLabs Conversational Agent.

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
9. [Configure the ElevenLabs Server Tools](#9-configure-the-elevenlabs-server-tools)
10. [Talk to Your Agent](#10-talk-to-your-agent)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. What This App Does

Your ElevenLabs voice agent has a conversation with a user and collects information about a child:

| Field        | Type                        | Example                     |
| ------------ | --------------------------- | --------------------------- |
| `parent_name`| string (1–100 chars)        | `"Rahul"`                   |
| `phone_number`| string                     | `"+919876543210"`           |
| `email`      | string (optional)           | `"rahul@example.com"`       |
| `address`    | object                      | `{"pincode": "400001"...}`  |
| `name`       | string (1–100 chars)        | `"Aarav"`                   |
| `age`        | integer (1–18)              | `7`                         |
| `gender`     | `"boy"` or `"girl"`         | `"boy"`                     |
| `order_type` | `"story book"`, `"movie"`, or `"combo..."` | `"story book"`              |
| `character`  | string (optional)           | `"brave, kind"`             |
| `interests`  | array of strings (max 10)   | `["dinosaurs", "painting"]` |
| `extra_message`| string (optional)         | `"Make it colorful"`        |

The agent can then:

- **Create** an order → gets a unique order ID (e.g. `OUM12345678`)
- **Look up** an order by its order ID
- **Update** an order (change name, age, gender, order type, character, or interests)
- **Cancel** an order (permanently delete it)

**Flow:**

```
User ↔ ElevenLabs Agent ──(server tool calls)──▶ FastAPI ──▶ MongoDB
```

### Endpoints

| Method   | Endpoint                 | Description                             |
| -------- | ------------------------ | --------------------------------------- |
| `POST`   | `/api/save-profile`      | Create a new profile (returns order ID) |
| `GET`    | `/api/get-order-details` | Look up a profile by order ID           |
| `PUT`    | `/api/update-order`      | Partially update an existing profile    |
| `DELETE` | `/api/cancel-order`      | Cancel and delete a profile             |
| `GET`    | `/health`                | Liveness check                          |

---

## 2. Install Prerequisites

### Python 3.11+

```bash
python3 --version
# If needed: brew install python@3.11
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
cd "eleven labs AI"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Check your `.env` file

The project root should contain a `.env` file with:

```dotenv
MONGODB_URL=mongodb://127.0.0.1:27017
DATABASE_NAME=child_profiles
LOG_LEVEL=INFO
```

These are the defaults — only edit if your MongoDB is on a different host/port.

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

| URL                          | What                                  |
| ---------------------------- | ------------------------------------- |
| http://localhost:8000/health | Health check (`{"status":"healthy"}`) |
| http://localhost:8000/docs   | Swagger UI (interactive docs)         |
| http://localhost:8000/redoc  | ReDoc (alternative docs)              |

---

## 6. Test the API with curl

Open a **new terminal** (keep the server running in the first one).

### 6.1 — Create a profile

```bash
curl -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{
    "parent_name": "Rahul",
    "phone_number": "+919876543210",
    "address": {
      "pincode": "400001",
      "Country": "India",
      "State": "Maharashtra",
      "city": "Mumbai",
      "locality": "Colaba"
    },
    "name": "Aarav",
    "age": 7,
    "gender": "boy",
    "order_type": "story book",
    "character": "brave, kind",
    "interests": ["dinosaurs", "painting", "cricket"]
  }'
```

**Expected response (201 Created):**

```json
{
  "status": "success",
  "order_id": "OUM12345678"
}
```

> Save this `order_id` — you'll need it for the next steps.

### 6.2 — Look up an order

```bash
curl "http://localhost:8000/api/get-order-details?order_id=OUM12345678"
```

**Expected response (200):**

```json
{
  "status": "success",
  "result": {
    "order_id": "OUM12345678",
    "parent_name": "Rahul",
    "phone_number": "+919876543210",
    "email": null,
    "address": {
      "pincode": "400001",
      "Country": "India",
      "State": "Maharashtra",
      "city": "Mumbai",
      "locality": "Colaba"
    },
    "name": "Aarav",
    "age": 7,
    "gender": "boy",
    "order_type": "story book",
    "character": "brave, kind",
    "interests": ["dinosaurs", "painting", "cricket"],
    "created_at": "2026-03-08T10:30:00+00:00"
  }
}
```

### 6.3 — Update an order

```bash
curl -X PUT http://localhost:8000/api/update-order \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "OUM12345678",
    "age": 8,
    "order_type": "movie"
  }'
```

**Expected response (200):**

```json
{
  "status": "success",
  "message": "Order OUM12345678 updated successfully.",
  "updated_fields": ["age", "order_type"]
}
```

### 6.4 — Cancel an order

```bash
curl -X DELETE "http://localhost:8000/api/cancel-order?order_id=OUM12345678"
```

**Expected response (200):**

```json
{
  "status": "success",
  "message": "Order OUM12345678 has been cancelled and removed."
}
```

### 6.5 — Validation errors

**Missing required field (→ 422):**

```bash
curl -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{"parent_name": "Rahul", "phone_number": "+919876543210", "address": {"pincode": "400", "Country": "IN", "State": "MH", "city": "MUM", "locality": "Colaba"}, "name": "Aarav", "age": 7, "gender": "boy"}'
```

**Invalid age (→ 422):**

```bash
curl -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{"parent_name": "Rahul", "phone_number": "123", "address": {"pincode": "400", "Country": "IN", "State": "MH", "city": "MUM", "locality": "Colaba"}, "name": "Aarav", "age": 0, "gender": "boy", "order_type": "movie", "character": "brave", "interests": []}'
```

**Invalid order ID format (→ 400):**

```bash
curl "http://localhost:8000/api/get-order-details?order_id=INVALID"
```

---

## 7. Verify Data in MongoDB

```bash
mongosh --eval 'use child_profiles; db.profiles.find().pretty()'
```

Expected document shape:

```json
{
  "_id": "ObjectId(...)",
  "order_id": "OUM12345678",
  "parent_name": "Rahul",
  "phone_number": "+919876543210",
  "address": {
    "pincode": "400001",
    "Country": "India",
    "State": "Maharashtra",
    "city": "Mumbai",
    "locality": "Colaba"
  },
  "name": "Aarav",
  "age": 7,
  "gender": "boy",
  "order_type": "story book",
  "character": "brave, kind",
  "interests": ["dinosaurs", "painting", "cricket"],
  "created_at": "ISODate(...)"
}
```

### Useful MongoDB queries

```bash
# Count all profiles
mongosh --eval 'use child_profiles; db.profiles.countDocuments()'

# Find by order_id
mongosh --eval 'use child_profiles; db.profiles.findOne({order_id: "OUM12345678"})'

# Delete all profiles (start fresh)
mongosh --eval 'use child_profiles; db.profiles.deleteMany({})'
```

---

## 8. Expose Your Server with ngrok

ElevenLabs needs a public URL to reach your local server.

```bash
ngrok http 8000
```

Copy the `https://...ngrok-free.app` URL.

### Quick test through ngrok

```bash
curl -X POST https://YOUR-NGROK-URL/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{
    "parent_name": "Test Parent",
    "phone_number": "1234567890",
    "address": {"pincode": "123", "Country": "US", "State": "NY", "city": "NY", "locality": "Test"},
    "name": "Test",
    "age": 3,
    "gender": "girl",
    "order_type": "movie",
    "character": "cute",
    "interests": ["blocks"]
  }'
```

If you get `{"status":"success","order_id":"OUM..."}`, ngrok is working.

> **Tip:** Free ngrok URLs change on restart. Update the tool URLs in ElevenLabs each time.

---

## 9. Configure the ElevenLabs Server Tools

### Step-by-step in the ElevenLabs dashboard

1. Log in to [elevenlabs.io](https://elevenlabs.io) and open your **Agent**.
2. Go to the **Tools** section.
3. Add **4 tools** — one for each JSON config file in the project root:

| Config File                                | Tool Name            | Method | Purpose         |
| ------------------------------------------ | -------------------- | ------ | --------------- |
| `elevenlabs_tool_config.json`              | `save_child_profile` | POST   | Create profiles |
| `elevenlabs_get_order_tool_config.json`    | `get_order_details`  | GET    | Look up orders  |
| `elevenlabs_update_order_tool_config.json` | `update_order`       | PUT    | Update orders   |
| `elevenlabs_cancel_order_tool_config.json` | `cancel_order`       | DELETE | Cancel orders   |

4. For each tool:
   - Open the JSON file
   - Replace `<your-ngrok-link>` with your actual ngrok URL
   - Paste the full JSON content into the tool configuration

5. **Save** each tool.

### Update your Agent's system prompt

> You are a friendly assistant that helps parents create and manage personalized orders for their children. During the conversation:
>
> 1. **To create an order**, collect the child's name, age, gender (boy or girl), order type (story book, movie, or combo story book + animated movie), character qualities (optional), and interests. Then call `save_child_profile`. Always tell the user their order ID (starts with "OUM").
> 2. **To look up an order**, ask for the order ID and call `get_order_details`.
> 3. **To update an order**, ask for the order ID and what they want to change, then call `update_order`.
> 4. **To cancel an order**, ask for the order ID, confirm with the user, then call `cancel_order`.

---

## 10. Talk to Your Agent

1. Make sure all three processes are running:
   - **MongoDB** (`brew services start mongodb-community`)
   - **FastAPI** (`uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`)
   - **ngrok** (`ngrok http 8000`)

2. Open the ElevenLabs Agent playground and start a conversation.

3. Example conversations:

   **Creating an order:**

   > "Hi, I'd like to create an order for my son. His name is Aarav, he's 7 years old, and he loves dinosaurs and painting. I'd like a story book."

   **Looking up an order:**

   > "Can you check the status of my order? My order ID is OUM12345678."

   **Updating an order:**

   > "I'd like to change my order OUM12345678. Can you update the age to 8?"

   **Cancelling an order:**

   > "Please cancel my order OUM12345678."

4. Check your terminal for logs like:

   ```
   INFO | ✅  Saved profile 6830a1f2... (order_id=OUM12345678) for Aarav
   INFO | 🔍  Order lookup order_id=OUM12345678 → found
   INFO | ✏️  Updated order OUM12345678 — fields: ['age']
   INFO | 🗑️  Cancelled order OUM12345678
   ```

---

## 11. Troubleshooting

### "Connection refused" when starting the server

MongoDB isn't running:

```bash
brew services start mongodb-community
```

### 422 errors from ElevenLabs

The agent is sending data that doesn't match the schema. Check:

- Is `age` an integer between 1 and 18?
- Is `gender` exactly `"boy"` or `"girl"`?
- Is `order_type` exactly `"story book"` or `"movie"`?
- Is `interests` an array (not a single string)?

### Invalid order ID errors (400)

The order ID must start with `OUM` followed by exactly 8 digits (e.g. `OUM12345678`).

### ngrok URL not working

- Make sure ngrok is still running.
- Verify all 4 tool URLs point to your current ngrok URL.
- Test the ngrok URL directly with curl.

### Agent doesn't call the tool

- Check that the tool is **enabled** in the agent settings.
- Make sure the agent's system prompt instructs it to call the correct tool.
- Verify the tool names match exactly.

### "Database not initialised" error

The lifespan event didn't run, usually because MongoDB wasn't reachable at startup. Always start with `uvicorn app.main:app`.

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
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  # Terminal 1
ngrok http 8000                                              # Terminal 2

# ── Test all endpoints ────────────────────────────
# Create
curl -s -X POST http://localhost:8000/api/save-profile \
  -H "Content-Type: application/json" \
  -d '{"parent_name":"Rahul","phone_number":"1234567890","address":{"pincode":"11","Country":"IN","State":"MH","city":"PU","locality":"K"},"name":"Aarav","age":7,"gender":"boy","order_type":"story book","character":"brave","interests":["dinosaurs"]}' | python3 -m json.tool

# Read
curl -s "http://localhost:8000/api/get-order-details?order_id=OUM12345678" | python3 -m json.tool

# Update
curl -s -X PUT http://localhost:8000/api/update-order \
  -H "Content-Type: application/json" \
  -d '{"order_id":"OUM12345678","age":8}' | python3 -m json.tool

# Delete
curl -s -X DELETE "http://localhost:8000/api/cancel-order?order_id=OUM12345678" | python3 -m json.tool

# ── Check DB ──────────────────────────────────────
mongosh --eval 'use child_profiles; db.profiles.find().pretty()'

# ── Stop everything ──────────────────────────────
# Ctrl+C on uvicorn and ngrok
brew services stop mongodb-community
```
