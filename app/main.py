from fastapi import FastAPI
from pydantic import BaseModel
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI()

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

DATABASE_URL = "mysql+pymysql://fastpass:fastpass1234@mysql:3306/fastpass"
engine = create_engine(DATABASE_URL)

class TicketRequest(BaseModel):
    user_id: str
    event_id: str

@app.on_event("startup")
def startup():
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ticket_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    event_id VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
        print("DB table ready")
    except SQLAlchemyError as e:
        print("DB init error:", e)

@app.get("/")
def root():
    return {"message": "FASTPASS API is running"}

@app.post("/tickets/request")
def request_ticket(data: TicketRequest):
    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO ticket_requests (user_id, event_id, status)
                    VALUES (:user_id, :event_id, 'QUEUED')
                """),
                {"user_id": data.user_id, "event_id": data.event_id}
            )
            conn.commit()

        queue_data = f"{data.user_id}:{data.event_id}"
        redis_client.lpush("ticket_queue", queue_data)

        queue_length = redis_client.llen("ticket_queue")

        return {
            "message": "request queued",
            "user_id": data.user_id,
            "event_id": data.event_id,
            "queue_length": queue_length
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/queue")
def get_queue():
    items = redis_client.lrange("ticket_queue", 0, -1)
    return {"queue": items}