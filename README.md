# 🗓️ Voice Scheduling Agent

A real-time AI voice assistant that schedules meetings through natural conversation and creates Google Calendar events automatically.

## 🔗 Live Demo

- **Deployed Backend**: [web-production-9d71c.up.railway.app](https://web-production-9d71c.up.railway.app)
- **VAPI Assistant**: Test via the VAPI dashboard or phone number (details below)

### How to Test

1. Visit the [VAPI Dashboard](https://dashboard.vapi.ai)
2. Navigate to **Assistants** → **vikara Scheduling Assistant**
3. Click **"Talk to Assistant"** to start a voice call
4. Have a conversation — provide your name, date, time, and optionally a meeting title
5. The agent will confirm details and create a real Google Calendar event

## 🏗️ Architecture

```
User (Voice) → VAPI (STT + LLM + TTS) → Webhook (FastAPI) → Google Calendar API
```

| Component | Technology | Purpose |
|---|---|---|
| Voice Platform | [VAPI](https://vapi.ai) | Orchestrates the voice pipeline |
| Speech-to-Text | Deepgram (via VAPI) | Converts user speech to text |
| LLM | Google Gemini 2.5 Flash (via VAPI) | Powers conversation & function calling |
| Text-to-Speech | ElevenLabs (via VAPI) | Converts assistant responses to speech |
| Backend | FastAPI (Python) | Handles webhook & calendar integration |
| Calendar | Google Calendar API | Creates real calendar events |
| Deployment | Railway | Hosts the backend server |

### Why Gemini 2.5 Flash?

- **Cost-efficient**: Free via VAPI credits — no separate API key needed
- **Low latency**: ~390ms Time to First Token, 268 tokens/sec output speed
- **Function calling**: Native tool/function calling support — critical for scheduling
- **Conversation quality**: Optimized for natural, multi-turn dialogue

## 📁 Project Structure

```
vikara-voice-agent/
├── main.py               # FastAPI webhook server (handles VAPI tool calls)
├── calendar_service.py   # Google Calendar API integration
├── requirements.txt      # Python dependencies
├── Procfile              # Railway deployment config
├── runtime.txt           # Python version specification
├── .env                  # Environment variables (not committed)
├── credentials.json      # Google service account key (not committed)
└── README.md             # This file
```

## 📞 Conversation Flow

The voice agent follows this structured flow:

1. **Greet** → Introduces itself and asks for the caller's name
2. **Collect Date** → Asks for preferred meeting date
3. **Collect Time** → Asks for preferred meeting time
4. **Optional Title** → Offers to name the meeting (defaults to "Meeting with [name]")
5. **Confirm** → Reads back all details for confirmation
6. **Create Event** → Calls the backend webhook to create the Google Calendar event
7. **Acknowledge** → Confirms the meeting was created successfully

## 🔧 Calendar Integration

### How It Works

1. **VAPI** detects the user has confirmed meeting details
2. VAPI calls the **`create_calendar_event`** custom tool with parameters: `name`, `date`, `time`, `title`
3. The tool sends a POST request to our **FastAPI webhook** (`/api/webhook`)
4. The webhook parses the date/time and calls **Google Calendar API** via a service account
5. A real calendar event is created with a 1-hour default duration
6. The result is returned to VAPI, which speaks the confirmation to the user

### Service Account Authentication

The app uses a Google Cloud **service account** for calendar access. This allows server-to-server authentication without user login prompts — ideal for an automated voice agent.

- The service account's email is added as a calendar editor
- Credentials are stored as an environment variable (`GOOGLE_CREDENTIALS_JSON`) in production
- Locally, a `credentials.json` file is used

## 🚀 Local Setup

### Prerequisites

- Python 3.11+
- Google Cloud project with Calendar API enabled
- Google service account with calendar access

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/madhav-051429/vikara-voice-agent.git
   cd vikara-voice-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up Google Calendar**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a project and enable the **Google Calendar API**
   - Create a **Service Account** and download the JSON key as `credentials.json`
   - Share your Google Calendar with the service account email (give **"Make changes to events"** permission)

4. **Create `.env` file**
   ```env
   GOOGLE_CALENDAR_ID=your-email@gmail.com
   GOOGLE_CREDENTIALS_PATH=credentials.json
   ```

5. **Run the server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

6. **Test the health endpoint**
   ```bash
   curl http://localhost:8000/
   # Returns: {"status": "alive", "service": "Vikara Voice Scheduling Agent"}
   ```

7. **Test the webhook manually**
   ```bash
   curl -X POST http://localhost:8000/api/webhook \
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

### Configuring Your Own Google Calendar

To use this agent with your own calendar:

1. Follow step 3 above to create your own service account
2. Share **your** Google Calendar with the service account email
3. Update `GOOGLE_CALENDAR_ID` in `.env` to your calendar email
4. Replace `credentials.json` with your service account key
5. For deployment, paste the entire JSON key contents into the `GOOGLE_CREDENTIALS_JSON` environment variable

## 🎯 Use Cases

- **Business Scheduling**: Deploy as a customer-facing appointment booking system (clinics, salons, consultancies)
- **Personal Assistant**: Use as a personal voice scheduler to quickly add events to your calendar
- **Team Coordination**: Extend to handle multi-calendar scheduling and availability checks

## 🛠️ Tech Stack

- **Python 3.11** — Backend language
- **FastAPI** — Async web framework for the webhook server
- **VAPI** — Voice AI platform (STT + LLM orchestration + TTS)
- **Google Gemini 2.5 Flash** — LLM for conversation and function calling
- **Google Calendar API** — Calendar event creation
- **Railway** — Cloud deployment platform

## 📝 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GOOGLE_CALENDAR_ID` | Google Calendar ID (usually your email) | ✅ |
| `GOOGLE_CREDENTIALS_JSON` | Service account JSON key (for deployment) | ✅ (production) |
| `GOOGLE_CREDENTIALS_PATH` | Path to credentials file (for local dev) | ✅ (local) |
| `PORT` | Server port (default: 8000) | ❌ |
