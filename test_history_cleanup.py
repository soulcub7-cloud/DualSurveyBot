"""Explicit, one-time launch cleanup. Never reset accounts or SQLite sequences."""
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

CONFIRMATION = "launch-2026-10-02"
MARKER = "test_history_cleanup_2026_10_02"


def run_if_requested(database_path, service):
    if os.environ.get("CLEAR_TEST_HISTORY", "").strip() != CONFIRMATION:
        return {"status": "disabled"}
    if service not in ("lms", "bot"):
        raise ValueError("Unknown service")
    path = Path(database_path).resolve()
    if not path.is_file():
        raise RuntimeError("Database is missing; cleanup aborted")
    with closing(sqlite3.connect(path, timeout=30)) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE IF NOT EXISTS maintenance_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        try:
            done = db.execute("SELECT value FROM maintenance_meta WHERE key=?", (MARKER,)).fetchone()
            if done:
                db.rollback()
                print(f"TEST_HISTORY_CLEANUP {service}: already completed; new records preserved")
                return {"status": "already_completed", **json.loads(done[0])}

            # The write lock prevents changes while a second connection makes a
            # consistent SQLite backup, including committed WAL contents.
            folder = path.parent / "maintenance_backups"
            folder.mkdir(mode=0o700, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            backup = folder / f"{service}-before-test-cleanup-{stamp}.sqlite3"
            fd = os.open(backup, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
            with closing(sqlite3.connect(path)) as source, closing(sqlite3.connect(backup)) as destination:
                source.backup(destination)
                if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("Backup verification failed; cleanup aborted")

            counts = {}
            if service == "lms":
                # Prevent later retries of the removed imports from restoring tests.
                db.execute("""CREATE TABLE IF NOT EXISTS removed_test_imports (
                    kind TEXT NOT NULL, source TEXT NOT NULL, external_id TEXT NOT NULL,
                    PRIMARY KEY(kind, source, external_id))""")
                for kind, table in (("survey", "skill_assessment_batches"), ("feedback", "mentor_feedback")):
                    db.execute(f"INSERT OR IGNORE INTO removed_test_imports SELECT ?, source, external_id FROM {table}", (kind,))
                tables = ("mentor_feedback_comments", "mentor_feedback", "skill_assessments", "skill_assessment_batches")
            else:
                tables = ("mentor_feedback", "surveys")
            for table in tables:
                counts[table] = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                db.execute(f"DELETE FROM {table}")
            if service == "lms":
                counts["progress_reset"] = db.execute("""UPDATE progress
                    SET status='not_started', score=NULL, note='', mentor_id=NULL, updated_at=CURRENT_TIMESTAMP
                    WHERE status!='not_started' OR score IS NOT NULL OR COALESCE(note,'')!='' OR mentor_id IS NOT NULL""").rowcount
                counts["notifications"] = db.execute("""DELETE FROM notifications
                    WHERE dedupe_key LIKE 'dual-survey-%' OR dedupe_key LIKE 'mentor-feedback-%'
                       OR title IN ('Матрица навыков обновлена', 'Новая оценка компетенций', 'Новый отзыв о наставнике')""").rowcount
            result = {"completed_at": datetime.now(timezone.utc).isoformat(), "backup": str(backup), "counts": counts}
            db.execute("INSERT INTO maintenance_meta(key,value) VALUES (?,?)", (MARKER, json.dumps(result)))
            if db.execute("PRAGMA foreign_key_check").fetchone():
                raise RuntimeError("Database relation check failed; cleanup rolled back")
            db.commit()
        except Exception:
            db.rollback()
            raise
    print(f"TEST_HISTORY_CLEANUP {service}: completed; " + json.dumps(result, ensure_ascii=False))
    return {"status": "completed", **result}


def was_removed(db, kind, source, external_id):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='removed_test_imports'").fetchone():
        return False
    return bool(db.execute("SELECT 1 FROM removed_test_imports WHERE kind=? AND source=? AND external_id=?", (kind, source, external_id)).fetchone())
