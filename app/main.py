from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI()

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

DATABASE_URL = "mysql+pymysql://fastpass:fastpass1234@mysql:3306/fastpass"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class TicketRequest(BaseModel):
    user_id: int
    event_id: int


@app.get("/")
def root():
    return {"message": "FASTPASS API is running"}


@app.post("/tickets/request")
def request_ticket(data: TicketRequest):
    try:
        # 1. DB 저장
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO ticket_requests (user_id, event_id, status)
                    VALUES (:user_id, :event_id, 'QUEUED')
                """),
                {"user_id": data.user_id, "event_id": data.event_id}
            )
            ticket_id = result.lastrowid

        # 2. Redis queue에 ticket_id push
        redis_client.rpush("ticket_queue", ticket_id)

        # 3. queue 길이 확인
        queue_length = redis_client.llen("ticket_queue")

        return {
            "message": "request queued",
            "ticket_id": ticket_id,
            "user_id": data.user_id,
            "event_id": data.event_id,
            "status": "QUEUED",
            "queue_length": queue_length
        }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/queue")
def get_queue():
    try:
        items = redis_client.lrange("ticket_queue", 0, -1)
        return {"queue": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")