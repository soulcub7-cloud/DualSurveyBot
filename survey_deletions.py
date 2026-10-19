"""Local tombstones double as a retryable deletion outbox. No respondent data."""
TABLES = {'survey': 'surveys', 'feedback': 'mentor_feedback'}


def schema(db):
    db.execute('''CREATE TABLE IF NOT EXISTS survey_deletions (
        kind TEXT NOT NULL, external_id TEXT NOT NULL,
        deleted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(kind,external_id))''')


def remove(database_path, kind, record_id):
    import sqlite3
    from contextlib import closing
    if kind not in TABLES or not str(record_id).isdigit():
        raise ValueError('Некорректная анкета')
    with closing(sqlite3.connect(database_path, timeout=30)) as db, db:
        schema(db)
        db.execute('INSERT OR IGNORE INTO survey_deletions(kind,external_id) VALUES (?,?)', (kind, str(record_id)))
        db.execute(f'DELETE FROM {TABLES[kind]} WHERE id=?', (int(record_id),))


def pending(database_path):
    import sqlite3
    from contextlib import closing
    with closing(sqlite3.connect(database_path, timeout=30)) as db, db:
        schema(db)
        return [{'kind': r[0], 'external_id': r[1]} for r in db.execute('SELECT kind,external_id FROM survey_deletions')]
