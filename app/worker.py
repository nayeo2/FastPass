import time
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

REDIS_HOST = "redis"
REDIS_PORT = 6379
QUEUE_NAME = "ticket_queue"

DATABASE_URL = "mysql+pymysql://fastpass:fastpass1234@mysql:3306/fastpass"

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def try_lock_seat(redis_client, user_id, event_id, seat_id):
    seat_key = f"seat:{event_id}:{seat_id}"

    result = redis_client.set(
        seat_key,
        user_id,
        nx=True,
        ex=30
    )

    return result

def process_ticket(ticket_id: int):
    with engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT id, user_id, event_id, seat_id, status
                FROM ticket_requests
                WHERE id = :ticket_id
            """),
            {"ticket_id": ticket_id}
        ).fetchone()

        if row is None:
            print(f"[WARN] ticket_id={ticket_id} 없음", flush=True)
            return

        user_id = row[1]
        event_id = row[2]
        seat_id = row[3]
        status = row[4]

        if status != "QUEUED":
            print(f"[SKIP] ticket_id={ticket_id} status={status}", flush=True)
            return

        lock_success = try_lock_seat(redis_client, user_id, event_id, seat_id)

        if not lock_success:
            conn.execute(
                text("""
                    UPDATE ticket_requests
                    SET status = 'FAILED', updated_at = NOW()
                    WHERE id = :ticket_id
                """),
                {"ticket_id": ticket_id}
            )
            print(f"[LOCK FAIL] ticket_id={ticket_id}, seat={seat_id}", flush=True)
            return

        conn.execute(
            text("""
                UPDATE ticket_requests
                SET status = 'PROCESSING', updated_at = NOW()
                WHERE id = :ticket_id
            """),
            {"ticket_id": ticket_id}
        )

        print(f"[LOCK SUCCESS] user={user_id}, ticket_id={ticket_id}, seat={seat_id}", flush=True)

    time.sleep(2)

    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE ticket_requests
                SET status = 'COMPLETED', updated_at = NOW()
                WHERE id = :ticket_id
            """),
            {"ticket_id": ticket_id}
        )

        print(f"[DONE] ticket_id={ticket_id}, seat={seat_id}", flush=True)



def fail_ticket(ticket_id: int):
    """
    실패 시 상태를 FAILED로 변경
    """
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE ticket_requests
                    SET status = 'FAILED', updated_at = NOW()
                    WHERE id = :ticket_id
                """),
                {"ticket_id": ticket_id}
            )
        print(f"[ERROR] ticket_id={ticket_id} → FAILED", flush=True)
    except Exception as e:
        print(f"[FATAL] FAILED 상태 업데이트조차 실패. ticket_id={ticket_id}, error={e}", flush=True)


def main():
    print("[WORKER] started. waiting for tickets...", flush=True)

    while True:
        try:
            # BLPOP: queue에 데이터 들어올 때까지 대기
            result = redis_client.blpop(QUEUE_NAME, timeout=0)

            if result is None:
                continue

            _, ticket_id_str = result
            ticket_id = int(ticket_id_str)

            print(f"[WORKER] 받은 ticket_id={ticket_id}", flush=True)

            try:
                process_ticket(ticket_id)
            except Exception as e:
                print(f"[ERROR] ticket_id={ticket_id} 처리 실패: {e}", flush=True)
                fail_ticket(ticket_id)

        except redis.RedisError as e:
            print(f"[REDIS ERROR] {e}", flush=True)
            time.sleep(3)

        except SQLAlchemyError as e:
            print(f"[DB ERROR] {e}", flush=True)
            time.sleep(3)

        except Exception as e:
            print(f"[UNKNOWN ERROR] {e}", flush=True)
            time.sleep(3)


if __name__ == "__main__":
    main()