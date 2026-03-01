import os
import json
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from calendar_service import create_event

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vikara Voice Scheduling Agent")

# Allow CORS (needed for VAPI to call your server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "alive", "service": "Vikara Voice Scheduling Agent"}


@app.post("/api/webhook")
async def vapi_webhook(request: Request):
    """
    Main webhook endpoint that VAPI calls.

    VAPI sends different types of messages:
    - function-call: When the AI wants to execute a tool/function
    - status-update: Call status changes
    - end-of-call-report: Summary after call ends
    """
    try:
        payload = await request.json()
        logger.info(f"Received webhook: {json.dumps(payload, indent=2)}")

        message = payload.get("message", {})
        message_type = message.get("type", "")

        # Handle function calls from VAPI
        if message_type == "function-call":
            function_name = message.get("functionCall", {}).get("name", "")
            parameters = message.get("functionCall", {}).get("parameters", {})

            logger.info(f"Function call: {function_name} with params: {parameters}")

            if function_name == "create_calendar_event":
                # Extract parameters
                name = parameters.get("name", "Unknown")
                date = parameters.get("date", "")
                time = parameters.get("time", "")
                title = parameters.get("title", None)

                # Create the calendar event
                result = create_event(name=name, date=date, time=time, title=title)

                logger.info(f"Calendar result: {result}")

                # Return result to VAPI — it will speak this to the user
                if result.get("success"):
                    return JSONResponse({
                        "result": f"I've successfully created the meeting '{result['summary']}' on {result['start']}. "
                                  f"The event has been added to the calendar. Is there anything else I can help you with?"
                    })
                else:
                    return JSONResponse({
                        "result": f"I'm sorry, I couldn't create the event. Error: {result.get('error', 'Unknown error')}. "
                                  f"Could you please try again with a different date or time?"
                    })

            else:
                return JSONResponse({
                    "result": f"Unknown function: {function_name}"
                })

        # Handle status updates (optional — good for logging)
        elif message_type == "status-update":
            status = message.get("status", "")
            logger.info(f"Call status update: {status}")
            return JSONResponse({"status": "ok"})

        # Handle end of call reports (optional — good for analytics)
        elif message_type == "end-of-call-report":
            logger.info(f"Call ended: {json.dumps(message, indent=2)}")
            return JSONResponse({"status": "ok"})

        # Handle transcript updates
        elif message_type == "transcript":
            logger.info(f"Transcript: {message.get('transcript', '')}")
            return JSONResponse({"status": "ok"})

        else:
            logger.info(f"Unhandled message type: {message_type}")
            return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JSONResponse(
            {"result": "An internal error occurred. Please try again."},
            status_code=500
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
