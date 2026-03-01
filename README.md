# 🗓️ Voice Scheduling Agent

A real-time AI voice assistant that schedules meetings through natural conversation and creates Google Calendar events — with built-in conflict detection.

---

## 🔗 Deployed URL & How to Test

**🎙️ Try the Voice Agent:** [Click here to talk to the assistant](https://vapi.ai?demo=true&shareKey=2701445f-a21f-402c-b1d1-881af1ad5dbf&assistantId=fa66c2ac-b68d-4443-91f4-9a5272dd3fe2)

**Backend Server:** [https://web-production-9d71c.up.railway.app](https://web-production-9d71c.up.railway.app)

### Testing the Voice Agent

1. Open the [**Voice Agent Demo Link**](https://vapi.ai?demo=true&shareKey=2701445f-a21f-402c-b1d1-881af1ad5dbf&assistantId=fa66c2ac-b68d-4443-91f4-9a5272dd3fe2)
2. Click the call button to start a voice conversation
3. The assistant will ask for your **name**, **preferred date & time**, and an optional **meeting title**
4. It will **confirm all details** before booking
5. A real **Google Calendar event** is created automatically
6. If the requested time slot is already booked, the agent will inform you and ask for a different time

### Testing the Backend Directly

```bash
# Health check
curl https://web-production-9d71c.up.railway.app/

# Test webhook with a sample tool call
curl -X POST https://web-production-9d71c.up.railway.app/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "type": "tool-calls",
      "toolCallList": [{
        "id": "test-123",
        "function": {
          "name": "create_calendar_event",
          "arguments": {
            "name": "Test User",
            "date": "2026-03-15",
            "time": "14:00",
            "title": "Test Meeting"
          }
        }
      }]
    }
  }'
```

---

## 🏗️ Architecture

```
User (Voice) ──► VAPI (STT + LLM + TTS) ──► FastAPI Webhook ──► Google Calendar API
```

| Component        | Technology                          | Role                                  |
| ---------------- | ----------------------------------- | ------------------------------------- |
| Voice Platform   | VAPI                                | Orchestrates the full voice pipeline  |
| Speech-to-Text   | Deepgram (via VAPI)                 | Converts speech to text               |
| LLM              | Google Gemini 2.0 Flash (via VAPI)  | Powers conversation & function calls  |
| Text-to-Speech   | ElevenLabs (via VAPI)               | Converts responses to speech          |
| Backend          | FastAPI (Python)                    | Webhook server & calendar integration |
| Calendar         | Google Calendar API                 | Creates real calendar events          |
| Hosting          | Railway                             | Deploys the backend server            |

### Why Gemini 2.0 Flash?

- **Low latency:** ~390ms Time to First Token — well under the 500ms threshold for natural conversation
- **Fast generation:** 268 tokens/sec — over 2x faster than GPT-4o
- **Native function calling:** Built-in tool/function support, critical for triggering calendar events
- **Cost-efficient:** Free via VAPI credits, no separate API key needed

---

## 📞 Conversation Flow

```
1. Greet ──► "Hi! I can help you book a meeting. What's your name?"
2. Name  ──► "What date works best for you?"
3. Date  ──► "And what time?"
4. Time  ──► "Would you like to give it a title?"
5. Confirm ► "So I have [title] for [name] on [date] at [time]. Sound right?"
6. Book  ──► Calls backend → creates Google Calendar event
7. Done  ──► "Your meeting has been confirmed!"
```

**Smart features:**
- Handles vague dates like "tomorrow" or "next Monday"
- Confirms details before booking
- Detects scheduling conflicts and asks for an alternative time
- Handles corrections without restarting the conversation

---

## 🔧 Calendar Integration Explained

### Overview

The voice agent creates **real Google Calendar events** using the Google Calendar API with a **service account** for server-to-server authentication.

### How It Works

1. During the voice call, the LLM collects name, date, time, and optional title
2. When the user confirms, VAPI sends a **tool call** to the FastAPI webhook
3. The webhook receives the parameters and:
   - Parses the date and time (supports multiple formats: `YYYY-MM-DD`, `March 5, 2026`, etc.)
   - **Checks for conflicts** using the Google Calendar FreeBusy API
   - If the slot is free, creates a 1-hour calendar event
   - If the slot is taken, returns an error so the agent can ask for a new time
4. The result is sent back to VAPI, which speaks the confirmation to the user

### Service Account Setup

A Google Cloud **service account** is used for authentication — this allows the backend to access the calendar without user login prompts. The service account's email is added as an editor to the target Google Calendar.

### Key Files

- **`calendar_service.py`** — Handles Google Calendar API calls (authentication, conflict detection, event creation)
- **`main.py`** — FastAPI server that receives VAPI webhook requests and routes them to the calendar service

---

## 🚀 Running Locally

### Prerequisites

- Python 3.11+
- A [Google Cloud](https://console.cloud.google.com) account
- A [VAPI](https://vapi.ai) account (free $10 credits on signup)

### Step 1: Clone & Install

```bash
git clone https://github.com/madhav-051429/vikara-voice-agent.git
cd vikara-voice-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Set Up Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com) → create a new project
2. Search for **"Google Calendar API"** in the top search bar → click **Enable**
3. Go to **IAM & Admin** → **Service Accounts** → click **Create Service Account**
4. Give it a name (e.g., `voice-agent`) → click **Done**
5. Click on the created service account → go to **Keys** tab → **Add Key** → **Create new key** → select **JSON** → download it
6. Rename the downloaded file to `credentials.json` and place it in the project folder
7. Copy the service account email (looks like `voice-agent@your-project.iam.gserviceaccount.com`)
8. Open [Google Calendar](https://calendar.google.com) → click the ⚙️ icon → **Settings** → under your calendar, click **Share with specific people** → **Add people** → paste the service account email → set permission to **"Make changes to events"** → click **Send**

### Step 3: Configure Environment

Create a `.env` file in the project root:

```env
GOOGLE_CALENDAR_ID=your-email@gmail.com
GOOGLE_CREDENTIALS_PATH=credentials.json
```

> Replace `your-email@gmail.com` with the Gmail address associated with your Google Calendar.

### Step 4: Run the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Verify it's running:

```bash
curl http://localhost:8000/
# → {"status": "alive", "service": "Voice Scheduling Agent"}
```

### Step 5: Set Up VAPI Assistant (only for full replication)

> **Note:** The deployed assistant is already publicly accessible via the [demo link](https://vapi.ai?demo=true&shareKey=2701445f-a21f-402c-b1d1-881af1ad5dbf&assistantId=fa66c2ac-b68d-4443-91f4-9a5272dd3fe2). The steps below are only needed if you want to create your own assistant connected to your own backend and calendar.

1. Sign up at [vapi.ai](https://vapi.ai) and create a new **Assistant**
2. Set **Provider** to Google, **Model** to Gemini 2.0 Flash
3. Add a system prompt for collecting name, date, time, and optional meeting title
4. Create a **Custom Tool** named `create_calendar_event` with your server URL as the endpoint
5. For local dev, use [ngrok](https://ngrok.com) (`ngrok http 8000`) to expose your local server to VAPI

---

## 📁 Project Structure

```
vikara-voice-agent/
├── main.py               # FastAPI webhook server
├── calendar_service.py   # Google Calendar API + conflict detection
├── requirements.txt      # Python dependencies
├── Procfile              # Railway deployment config
├── runtime.txt           # Python version (3.11.6)
├── .env                  # Environment variables (not committed)
├── credentials.json      # Service account key (not committed)
├── .gitignore
└── README.md
```

---

## 📝 Environment Variables

| Variable                  | Description                             | Required       |
| ------------------------- | --------------------------------------- | -------------- |
| `GOOGLE_CALENDAR_ID`      | Target calendar ID (usually your email) | Yes            |
| `GOOGLE_CREDENTIALS_JSON` | Service account JSON key (for Railway)  | Yes (deployed) |
| `GOOGLE_CREDENTIALS_PATH` | Path to credentials file (for local)    | Yes (local)    |
| `PORT`                    | Server port (default: 8000)             | No             |

---

## 📋 Sample Call Log

Below is a transcript from an actual test call showing the complete scheduling flow:

```
Assistant: Hi! I'm the scheduling assistant. I can help you book a meeting.
           Could I get your name, please?
User:      My name is Madhav.
Assistant: Thanks, Madhav. What date works best for you?
User:      March twelfth.
Assistant: And what time would you like to schedule it for?
User:      3 PM.
Assistant: Would you like to give this meeting a title?
           If not, I'll just name it "Meeting with Madhav."
User:      No, that's fine.
Assistant: Just to confirm — "Meeting with Madhav"
           on March 12th, 2026 at 3 PM. Does that sound right?
User:      Yes.

→ [create_calendar_event called — completed successfully]
