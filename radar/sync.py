"""Safe explicit sync. Does not hide failures or imply global coverage."""
import argparse
import json
import sys
from datetime import datetime, timezone
from .core import metrics
from .github import GitHubClient, GithubError
from .store import connect, upsert


def sync(path=None, limit=100):
    client = GitHubClient()
    db = connect(path) if path else connect()
    started = datetime.now(timezone.utc).isoformat()
    cursor = db.execute("INSERT INTO sync_runs(started_at,status) VALUES (?,?)", (started,"running"))
    run_id = cursor.lastrowid
    db.commit()
    refreshed = failures = discovered = 0
    try:
        candidates = client.discover()
        discovered = len(candidates)
        for item in candidates[:limit]:
            try:
                history = client.history(item["full_name"])
                measured_at = datetime.now(timezone.utc)
                upsert(db, item, metrics(history, item["stargazers_count"], measured_at), measured_at.isoformat())
                db.commit()
                refreshed += 1
            except (GithubError, ValueError, KeyError, TypeError) as e:
                failures += 1
                print(f"ERROR {item['full_name']}: {e}", file=sys.stderr)
        status = "complete" if failures == 0 else "partial"
    except Exception:
        status = "failed"
        raise
    finally:
        db.execute("UPDATE sync_runs SET completed_at=?,discovered=?,refreshed=?,failures=?,status=? WHERE id=?", (
            datetime.now(timezone.utc).isoformat(),discovered,refreshed,failures,status,run_id))
        db.commit()
        db.close()
    return {"discovered":discovered,"refreshed":refreshed,"failures":failures,"status":status}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(sync(limit=args.limit), indent=2))
