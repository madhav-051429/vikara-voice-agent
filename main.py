import os
import json
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from calendar_service import create_event

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Scheduling Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "alive", "service": "Voice Scheduling Agent"}


@app.post("/api/webhook")
async def vapi_webhook(request: Request):
    """Handles incoming webhook requests from VAPI."""
    try:
        payload = await request.json()
        logger.info(f"Webhook payload: {json.dumps(payload, indent=2)}")

        message = payload.get("message", {})
        msg_type = message.get("type", "")

        # VAPI Tools format (current)
        if msg_type == "tool-calls":
            tool_calls = message.get("toolCallList", [])
            results = []

            for tc in tool_calls:
                tc_id = tc.get("id", "")
                func = tc.get("function", {})
                name = func.get("name", "")
                args = func.get("arguments", {})

                # arguments might come as a JSON string
                if isinstance(args, str):
                    args = json.loads(args)

                logger.info(f"Tool call: {name}, args: {args}")

                if name == "create_calendar_event":
                    result = handle_scheduling(args)
                    results.append({"toolCallId": tc_id, "result": result})
                else:
                    results.append({"toolCallId": tc_id, "result": f"Unknown tool: {name}"})

            return JSONResponse({"results": results})

        # legacy function-call format (keeping for backwards compat)
        elif msg_type == "function-call":
            fc = message.get("functionCall", {})
            name = fc.get("name", "")
            params = fc.get("parameters", {})
            logger.info(f"Function call: {name}, params: {params}")

            if name == "create_calendar_event":
                return JSONResponse({"result": handle_scheduling(params)})
            return JSONResponse({"result": f"Unknown function: {name}"})

        elif msg_type == "status-update":
            logger.info(f"Status: {message.get('status', '')}")
            return JSONResponse({"status": "ok"})

        elif msg_type == "end-of-call-report":
            logger.info("Call ended")
            return JSONResponse({"status": "ok"})

        elif msg_type == "transcript":
            return JSONResponse({"status": "ok"})

        else:
            logger.info(f"Unhandled message type: {msg_type}")
            return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse({"result": "Internal error. Please try again."}, status_code=500)


def handle_scheduling(params: dict) -> str:
    """Takes scheduling params and creates a calendar event."""
    name = params.get("name", "Unknown")
    date = params.get("date", "")
    time_val = params.get("time", "")
    title = params.get("title", None)

    result = create_event(name=name, date=date, time=time_val, title=title)
    logger.info(f"Calendar result: {result}")

    if result.get("success"):
        return (f"Meeting '{result['summary']}' created on {result['start']}. "
                "Is there anything else I can help with?")
    else:
        return f"Sorry, I couldn't create the event. {result.get('error', 'Unknown error')}."


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
