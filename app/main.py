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
    seat_id: str


@app.get("/")
def root():
    return {"message": "FASTPASS API is running"}


@app.post("/tickets/request")
def request_ticket(request: TicketRequest):
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO ticket_requests (user_id, event_id, seat_id, status, created_at, updated_at)
                    VALUES (:user_id, :event_id, :seat_id, 'QUEUED', NOW(), NOW())
                """),
                {
                    "user_id": request.user_id,
                    "event_id": request.event_id,
                    "seat_id": request.seat_id
                }
            )

            ticket_id = result.lastrowid

        redis_client.rpush("ticket_queue", ticket_id)

        return {
            "message": "Ticket request queued successfully",
            "ticket_id": ticket_id,
            "status": "QUEUED",
            "seat_id": request.seat_id
        }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except redis.RedisError as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/queue")
def get_queue():
    try:
        items = redis_client.lrange("ticket_queue", 0, -1)
        return {"queue": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")