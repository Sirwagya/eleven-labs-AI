# ElevenLabs Child Profile API

FastAPI + MongoDB backend that receives **structured JSON** from ElevenLabs Agent Server Tools and manages child profile orders.

## What this app does

| Method   | Endpoint                 | Description                                         |
| -------- | ------------------------ | --------------------------------------------------- |
| `POST`   | `/api/save-profile`      | Create a new child profile (returns `OUM` order ID) |
| `GET`    | `/api/get-order-details` | Look up a profile by order ID                       |
| `PUT`    | `/api/update-order`      | Update fields on an existing profile                |
| `DELETE` | `/api/cancel-order`      | Cancel (delete) a profile                           |
| `GET`    | `/health`                | Liveness check                                      |

Each profile gets a unique **order ID** (format: `OUM` + 8 random digits, e.g. `OUM12345678`).

---

## JSON Schema

### Save Profile (POST)

```json
{
  "parent_name": "Rahul",
  "phone_number": "+919876543210",
  "email": "rahul@example.com",
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
  "interests": ["dinosaurs", "painting"],
  "extra_message": "Make it colorful"
}
```

### Validation Rules

- `parent_name` — string (1–100 chars, required)
- `phone_number` — string (required)
- `email` — string (optional)
- `address` — object with `pincode`, `Country`, `State`, `city`, `locality` (required)
- `name` — string (1–100 chars, required)
- `age` — integer (1–18, required)
- `gender` — `"boy"` or `"girl"` (required)
- `order_type` — `"story book"`, `"movie"`, or `"combo story book + animated movie"` (required)
- `character` — string (optional)
- `interests` — array of strings (max 10 items)
- `extra_message` — string (optional)
- Extra fields are rejected

---

## Local Setup

### 1) Prerequisites

- Python 3.11+
- MongoDB Community (local)
- ngrok

### 2) Install dependencies

```bash
cd "eleven labs AI"
python3 -m venv venv
source venv/bin/activate
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

Swagger docs: http://localhost:8000/docs

---

## ElevenLabs Server Tools Setup

### 1) Start ngrok tunnel

```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g. `https://abcd-1234.ngrok-free.app`).

### 2) Add tools in ElevenLabs

There are **4 tool configs** in the project root — paste each into the ElevenLabs dashboard after replacing `<your-ngrok-link>` with your ngrok URL:

| File                                       | Tool Name            | Method |
| ------------------------------------------ | -------------------- | ------ |
| `elevenlabs_tool_config.json`              | `save_child_profile` | POST   |
| `elevenlabs_get_order_tool_config.json`    | `get_order_details`  | GET    |
| `elevenlabs_update_order_tool_config.json` | `update_order`       | PUT    |
| `elevenlabs_cancel_order_tool_config.json` | `cancel_order`       | DELETE |

### 3) Agent system prompt suggestion

> You are a friendly assistant that helps parents create and manage orders for their children. During the conversation, collect the child's **name**, **age**, **gender** (boy or girl), **order type** (story book, movie, or combo story book + animated movie), **character qualities** (optional), and **interests**. Once you have all fields, call the `save_child_profile` tool. Always tell the user their order ID (starts with "OUM") after saving. To look up, update, or cancel an order, ask the user for their order ID.

---

## API Test with curl

### Save a profile

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
    "interests": ["dinosaurs", "painting"]
  }'
```

Response (`201 Created`):

```json
{
  "status": "success",
  "order_id": "OUM12345678"
}
```

### Get order details

```bash
curl "http://localhost:8000/api/get-order-details?order_id=OUM12345678"
```

### Update order

```bash
curl -X PUT http://localhost:8000/api/update-order \
  -H "Content-Type: application/json" \
  -d '{"order_id": "OUM12345678", "age": 8}'
```

### Cancel order

```bash
curl -X DELETE "http://localhost:8000/api/cancel-order?order_id=OUM12345678"
```

---

## Verify in MongoDB

```bash
mongosh child_profiles --quiet --eval 'db.profiles.find().sort({created_at:-1}).limit(1).toArray()'
```

Expected shape:

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
  "interests": ["dinosaurs", "painting"],
  "status": "pending",
  "created_at": "ISODate(...)"
}
```

---

## Project Structure

```text
eleven labs AI/
├── .env
├── README.md
├── TUTORIAL.md
├── requirements.txt
├── elevenlabs_tool_config.json
├── elevenlabs_get_order_tool_config.json
├── elevenlabs_update_order_tool_config.json
├── elevenlabs_cancel_order_tool_config.json
└── app/
    ├── __init__.py
    ├── config.py
    ├── database.py
    ├── main.py
    ├── models.py
    └── routes.py
```

For a longer walkthrough, see `TUTORIAL.md`.
