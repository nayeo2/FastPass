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


def process_ticket(ticket_id: int):
    """
    ticket_id를 기반으로 DB 상태를 변경하는 핵심 처리 함수
    """
    with engine.begin() as conn:
        # 1) 현재 티켓 상태 조회
        row = conn.execute(
            text("""
                SELECT id, status
                FROM ticket_requests
                WHERE id = :ticket_id
            """),
            {"ticket_id": ticket_id}
        ).fetchone()

        if row is None:
            print(f"[WARN] ticket_id={ticket_id} 는 DB에 없음", flush=True)
            return

        current_status = row[1]

        # 이미 처리됐거나 비정상 상태면 스킵
        if current_status != "QUEUED":
            print(f"[INFO] ticket_id={ticket_id} 는 이미 처리 대상이 아님. current_status={current_status}")
            return

        # 2) PROCESSING으로 변경
        conn.execute(
            text("""
                UPDATE ticket_requests
                SET status = 'PROCESSING', updated_at = NOW()
                WHERE id = :ticket_id
            """),
            {"ticket_id": ticket_id}
        )
        print(f"[INFO] ticket_id={ticket_id} → PROCESSING", flush=True)

    # 실제 처리 시간이 있다고 가정
    time.sleep(2)

    with engine.begin() as conn:
        # 3) COMPLETED로 변경
        conn.execute(
            text("""
                UPDATE ticket_requests
                SET status = 'COMPLETED', updated_at = NOW()
                WHERE id = :ticket_id
            """),
            {"ticket_id": ticket_id}
        )
        print(f"[INFO] ticket_id={ticket_id} → COMPLETED", flush=True)


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
        print(f"[ERROR] ticket_id={ticket_id} → FAILED")
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