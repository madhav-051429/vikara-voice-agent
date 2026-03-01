from calendar_service import create_event

result = create_event(
    name="Test User",
    date="2026-03-05",
    time="14:00",
    title="Test Meeting from Voice Agent"
)
print(result)
