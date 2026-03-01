# 🗓️ Voice Scheduling Agent

A real-time AI voice assistant that schedules meetings through natural conversation and creates Google Calendar events — with built-in conflict detection.

---

## 🔗 Deployed URL & How to Test

**🎙️ Try the Voice Agent:** [Click here to talk to the assistant](https://vapi.ai?demo=true&shareKey=2701445f-a21f-402c-b1d1-881af1ad5dbf&assistantId=fa66c2ac-b68d-4443-91f4-9a5272dd3fe2)

**Backend Server:** [https://web-production-9d71c.up.railway.app](https://web-production-9d71c.up.railway.app)

### Testing the Voice Agent

1. Go to the [VAPI Dashboard](https://dashboard.vapi.ai)
2. Open the **"vikara Scheduling Assistant"**
3. Click **"Talk to Assistant"** (green button, top-right)
4. Have a voice conversation:
   - The assistant will ask for your **name**
   - Then your preferred **date** and **time**
   - Optionally, a **meeting title**
   - It will **confirm all details** before booking
   - A real **Google Calendar event** is created automatically
5. If the requested time slot is already booked, the agent will inform you and ask for a different time

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
| LLM              | Google Gemini 2.5 Flash (via VAPI)  | Powers conversation & function calls  |
| Text-to-Speech   | ElevenLabs (via VAPI)               | Converts responses to speech          |
| Backend          | FastAPI (Python)                    | Webhook server & calendar integration |
| Calendar         | Google Calendar API                 | Creates real calendar events          |
| Hosting          | Railway                             | Deploys the backend server            |

### Why Gemini 2.5 Flash?

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

## 🚀 Running Locally (Optional)

### Prerequisites

- Python 3.11+
- Google Cloud project with Calendar API enabled
- Service account with calendar access

### Steps

1. **Clone the repo**

   ```bash
   git clone https://github.com/madhav-051429/vikara-voice-agent.git
   cd vikara-voice-agent
   ```

2. **Set up virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Google Calendar**
   - Create a project in [Google Cloud Console](https://console.cloud.google.com)
   - Enable the **Google Calendar API**
   - Create a **Service Account** → download the JSON key as `credentials.json`
   - Open Google Calendar → Settings → Share your calendar with the service account email → give **"Make changes to events"** permission

4. **Create `.env` file**

   ```env
   GOOGLE_CALENDAR_ID=your-email@gmail.com
   GOOGLE_CREDENTIALS_PATH=credentials.json
   ```

5. **Run the server**

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

6. **Verify**

   ```bash
   curl http://localhost:8000/
   # → {"status": "alive", "service": "Vikara Voice Scheduling Agent"}
   ```

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
├── .gitignore            # Ignores .env, credentials, __pycache__
└── README.md
```

---

## 📝 Environment Variables

| Variable                   | Description                              | Required       |
| -------------------------- | ---------------------------------------- | -------------- |
| `GOOGLE_CALENDAR_ID`       | Target calendar ID (usually your email)  | Yes            |
| `GOOGLE_CREDENTIALS_JSON`  | Service account JSON key (for Railway)   | Yes (deployed) |
| `GOOGLE_CREDENTIALS_PATH`  | Path to credentials file (for local dev) | Yes (local)    |
| `PORT`                     | Server port (default: 8000)              | No             |

---

## 🎯 Use Cases

- **Business scheduling** — Deploy as a customer-facing appointment booking agent for clinics, salons, or consultancies
- **Personal assistant** — Use as a personal voice scheduler to add events to your calendar
- **Team coordination** — Extend to handle multi-calendar scheduling and availability checks
