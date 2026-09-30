import sqlite3
from contextlib import closing
import json
import os
from pathlib import Path

from questions import get_questions
from config import ADMIN_ID, SPECIALIST_ID

BASE_DIR = Path(__file__).resolve().parent
DATABASE = os.getenv(
    "DATABASE_PATH",
    str(BASE_DIR / "data" / "survey.db")
)


def get_connection():
    return sqlite3.connect(DATABASE)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # =====================================================
    # НАСТАВНИКИ
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mentors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        fio TEXT NOT NULL,
        registration_date TEXT,
        role TEXT DEFAULT 'mentor'
    )
    """)

    # =====================================================
    # СТУДЕНТЫ
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fio TEXT NOT NULL,
        speciality TEXT,
        course INTEGER,
        enterprise TEXT,
        stream INTEGER,
        active INTEGER DEFAULT 1,
        telegram_id INTEGER UNIQUE,
        registered_at TEXT
    )
    """)

    # =====================================================
    # ПРЕДПРИЯТИЯ
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enterprises(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        active INTEGER DEFAULT 1
    )
    """)

    # =====================================================
    # АНКЕТЫ
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS surveys(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mentor_id INTEGER,
        student_id INTEGER,
        survey_date TEXT,
        answers TEXT,
        average REAL,
        best TEXT,
        improve TEXT,
        recommendation TEXT,
        enterprise TEXT,
        questionnaire_key TEXT DEFAULT 'legacy',
        questions_json TEXT,
        hard_average REAL,
        soft_average REAL,
        suitability_score INTEGER,

        FOREIGN KEY (mentor_id) REFERENCES mentors(id),
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mentor_directory(
        lms_id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        enterprise TEXT,
        city TEXT,
        workshop TEXT,
        qualification TEXT,
        active INTEGER DEFAULT 1,
        synced_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mentor_feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        mentor_lms_id INTEGER NOT NULL,
        mentor_name TEXT NOT NULL,
        enterprise TEXT,
        city TEXT,
        workshop TEXT,
        speciality TEXT,
        course INTEGER,
        stream INTEGER,
        module TEXT NOT NULL,
        submitted_at TEXT NOT NULL,
        ratings_json TEXT NOT NULL,
        questions_json TEXT NOT NULL,
        average REAL NOT NULL,
        strengths TEXT,
        weaknesses TEXT,
        missing_topics TEXT,
        liked TEXT,
        disliked TEXT,
        conclusion TEXT,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    conn.commit()
    conn.close()


# =====================================================
# НАСТАВНИКИ
# =====================================================

def mentor_exists(telegram_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM mentors WHERE telegram_id=?",
        (telegram_id,)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


def add_mentor(telegram_id, fio, date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO mentors(
            telegram_id,
            fio,
            registration_date
        )
        VALUES(?,?,?)
        """,
        (telegram_id, fio, date)
    )

    conn.commit()
    conn.close()


def get_mentor_name(telegram_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT fio
        FROM mentors
        WHERE telegram_id=?
        """,
        (telegram_id,)
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return None


def get_mentor_id(telegram_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM mentors
        WHERE telegram_id=?
        """,
        (telegram_id,)
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return None


# =====================================================
# СТУДЕНТЫ
# =====================================================

def add_student(fio, stream, speciality=None, course=None):

    conn = get_connection()
    cursor = conn.cursor()

    # Проверяем, существует ли студент
    cursor.execute(
        """
        SELECT id
        FROM students
        WHERE fio=?
        """,
        (fio,)
    )

    student = cursor.fetchone()

    # ===========================
    # Если студент уже существует
    # ===========================
    if student:

        cursor.execute(
            """
            UPDATE students

            SET
                stream=?,
                speciality=?,
                course=?,
                active=1

            WHERE fio=?
            """,
            (
                stream,
                speciality,
                course,
                fio
            )
        )

        conn.commit()
        conn.close()

        return False

    # ===========================
    # Если новый студент
    # ===========================
    cursor.execute(
        """
        INSERT INTO students(
            fio,
            stream,
            speciality,
            course,
            active
        )
        VALUES(?,?,?,?,1)
        """,
        (
            fio,
            stream,
            speciality,
            course
        )
    )

    conn.commit()
    conn.close()

    return True


def get_students():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, fio
        FROM students
        WHERE active=1
        ORDER BY fio
    """)

    students = cursor.fetchall()

    conn.close()

    return students


def get_student_name(student_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT fio
        FROM students
        WHERE id=?
        """,
        (student_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if row:
        return row[0]

    return "Неизвестный студент"


# =====================================================
# АНКЕТЫ
# =====================================================

def load_survey_questions(questionnaire_key, questions_json=None):
    """Return the exact question snapshot, falling back to the catalog."""
    if questions_json:
        try:
            loaded = json.loads(questions_json)
            if isinstance(loaded, list) and loaded:
                return loaded
        except (TypeError, json.JSONDecodeError):
            pass
    return get_questions(questionnaire_key or "legacy")


def build_survey_responses(questionnaire_key, questions_json, answers_json):
    questions = load_survey_questions(questionnaire_key, questions_json)
    try:
        answers = json.loads(answers_json) if isinstance(answers_json, str) else list(answers_json or [])
    except (TypeError, json.JSONDecodeError):
        answers = []
    responses = []
    for question, score in zip(questions, answers):
        responses.append(
            {
                "skill_code": question.get("code"),
                "question": question.get("text", ""),
                "section": question.get("section", "soft"),
                "score": int(score),
            }
        )
    return responses

def save_survey(
        mentor_id,
        student_id,
        enterprise,
        answers,
        average,
        best,
        improve,
        recommendation,
        survey_date,
        questionnaire_key="legacy",
        questions=None,
        hard_average=None,
        soft_average=None,
        suitability_score=None,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO surveys(

            mentor_id,
            student_id,
            survey_date,
            answers,
            average,
            best,
            improve,
            recommendation,
            enterprise,
            questionnaire_key,
            questions_json,
            hard_average,
            soft_average,
            suitability_score

        )

        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)

        """,
        (
            mentor_id,
            student_id,
            survey_date,
            json.dumps(answers),
            average,
            best,
            improve,
            recommendation,
            enterprise,
            questionnaire_key,
            json.dumps(questions or get_questions(questionnaire_key), ensure_ascii=False),
            hard_average,
            soft_average,
            suitability_score,
        )
    )

    survey_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return survey_id


def get_surveys_by_mentor(mentor_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            surveys.id,
            students.fio,
            surveys.survey_date,
            surveys.average
        FROM surveys

        JOIN students
        ON surveys.student_id = students.id

        WHERE mentor_id=?

        ORDER BY surveys.id DESC
    """, (mentor_id,))

    result = cursor.fetchall()

    conn.close()

    return result


def get_survey(survey_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            surveys.id,
            surveys.mentor_id,
            surveys.student_id,
            surveys.survey_date,
            surveys.answers,
            surveys.average,
            surveys.best,
            surveys.improve,
            surveys.recommendation,
            students.fio,
            COALESCE(
                surveys.enterprise,
                students.enterprise,
                'Не указано'
            ),
            students.stream,
            surveys.questionnaire_key,
            surveys.questions_json,
            surveys.hard_average,
            surveys.soft_average,
            surveys.suitability_score

        FROM surveys

        JOIN students
        ON surveys.student_id = students.id

        WHERE surveys.id=?
    """, (survey_id,))

    result = cursor.fetchone()

    conn.close()

    return result


def get_surveys_count(mentor_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM surveys
        WHERE mentor_id=?
        """,
        (mentor_id,)
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count


create_tables()
def can_manage_access(telegram_id):
    """Only configured bot owners may appoint specialists."""
    return telegram_id > 0 and telegram_id in {ADMIN_ID, SPECIALIST_ID}


def get_mentor_role(telegram_id):
    if can_manage_access(telegram_id):
        return "specialist"
    with closing(get_connection()) as conn:
        row = conn.execute("SELECT role FROM mentors WHERE telegram_id=?", (telegram_id,)).fetchone()
    return "specialist" if row and row[0] in {"admin", "specialist"} else "mentor"


def is_specialist(telegram_id):
    return get_mentor_role(telegram_id) == "specialist"


def set_specialist(telegram_id):
    if telegram_id <= 0:
        return False
    with closing(get_connection()) as conn:
        result = conn.execute("UPDATE mentors SET role='specialist' WHERE telegram_id=?", (telegram_id,))
        conn.commit()
        return result.rowcount == 1


def migrate():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            ALTER TABLE mentors
            ADD COLUMN role TEXT DEFAULT 'mentor'
        """)
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("""
            ALTER TABLE surveys
            ADD COLUMN enterprise TEXT
        """)
    except sqlite3.OperationalError:
        pass

    survey_columns = {
        "questionnaire_key": "TEXT DEFAULT 'legacy'",
        "questions_json": "TEXT",
        "hard_average": "REAL",
        "soft_average": "REAL",
        "suitability_score": "INTEGER",
    }
    existing_survey_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(surveys)").fetchall()
    }
    for column, definition in survey_columns.items():
        if column not in existing_survey_columns:
            cursor.execute(f"ALTER TABLE surveys ADD COLUMN {column} {definition}")

    existing_student_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(students)").fetchall()
    }
    for column, definition in {
        "telegram_id": "INTEGER",
        "registered_at": "TEXT",
    }.items():
        if column not in existing_student_columns:
            cursor.execute(f"ALTER TABLE students ADD COLUMN {column} {definition}")
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_students_telegram_id "
        "ON students(telegram_id) WHERE telegram_id IS NOT NULL"
    )

    try:
        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN stream INTEGER
        """)
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN active INTEGER DEFAULT 1
        """)
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("""
            ALTER TABLE enterprises
            ADD COLUMN active INTEGER DEFAULT 1
        """)
    except sqlite3.OperationalError:
        pass

    cursor.execute("UPDATE students SET active=1 WHERE active IS NULL")
    cursor.execute("UPDATE enterprises SET active=1 WHERE active IS NULL")
    cursor.execute(
        "UPDATE surveys SET questionnaire_key='legacy' "
        "WHERE questionnaire_key IS NULL OR TRIM(questionnaire_key)=''"
    )

    cursor.execute("""
        UPDATE surveys
        SET enterprise = (
            SELECT students.enterprise
            FROM students
            WHERE students.id = surveys.student_id
        )
        WHERE enterprise IS NULL
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO enterprises(name)
        SELECT DISTINCT TRIM(enterprise)
        FROM students
        WHERE enterprise IS NOT NULL
          AND TRIM(enterprise) != ''
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO enterprises(name)
        SELECT DISTINCT TRIM(enterprise)
        FROM surveys
        WHERE enterprise IS NOT NULL
          AND TRIM(enterprise) != ''
    """)

    conn.commit()
    conn.close()


create_tables()
migrate()
def get_all_surveys_for_excel():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            surveys.id,
            surveys.survey_date,

            students.fio,
            students.speciality,
            students.course,
            COALESCE(
                surveys.enterprise,
                students.enterprise,
                'Не указано'
            ),

            mentors.fio,

            surveys.answers,

            surveys.average,
            surveys.best,
            surveys.improve,
            surveys.recommendation,
            surveys.questionnaire_key,
            surveys.questions_json,
            surveys.hard_average,
            surveys.soft_average,
            surveys.suitability_score

        FROM surveys

        JOIN students
            ON students.id = surveys.student_id

        JOIN mentors
            ON mentors.id = surveys.mentor_id

        ORDER BY surveys.id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return data
def get_surveys():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            surveys.id,
            students.fio,
            mentors.fio,
            surveys.survey_date,
            surveys.average
        FROM surveys
        JOIN students
            ON students.id = surveys.student_id
        JOIN mentors
            ON mentors.id = surveys.mentor_id
        ORDER BY surveys.id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return data
def delete_survey(survey_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM surveys
        WHERE id=?
        """,
        (survey_id,)
    )

    conn.commit()

    conn.close()
    # =====================================================
# СПИСОК СТУДЕНТОВ СО СТАТИСТИКОЙ
# =====================================================

def get_students_statistics():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT

            students.id,
            students.fio,

            COUNT(surveys.id),
            ROUND(AVG(surveys.average),2),
            ROUND(AVG(surveys.hard_average),2),
            ROUND(AVG(surveys.soft_average),2)

        FROM students

        LEFT JOIN surveys
            ON surveys.student_id = students.id

        WHERE students.active=1

        GROUP BY students.id

        ORDER BY students.fio
    """)

    data = cursor.fetchall()

    conn.close()

    return data
# =====================================================
# СПИСОК НАСТАВНИКОВ СО СТАТИСТИКОЙ
# =====================================================

def get_mentors_statistics():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT

            mentors.id,
            mentors.fio,

            COUNT(surveys.id),
            ROUND(AVG(surveys.average), 2),
            ROUND(AVG(surveys.hard_average), 2),
            ROUND(AVG(surveys.soft_average), 2)

        FROM mentors

        LEFT JOIN surveys
            ON surveys.mentor_id = mentors.id

        GROUP BY mentors.id

        ORDER BY mentors.fio
    """)

    data = cursor.fetchall()

    conn.close()

    return data
# =====================================================
# ОБЩАЯ СТАТИСТИКА
# =====================================================

def get_statistics():

    conn = get_connection()
    cursor = conn.cursor()

    # Студенты
    cursor.execute("SELECT COUNT(*) FROM students WHERE active=1")
    students = cursor.fetchone()[0]

    # Наставники
    cursor.execute("SELECT COUNT(*) FROM mentors WHERE role='mentor'")
    mentors = cursor.fetchone()[0]

    # Специалисты
    cursor.execute("SELECT COUNT(*) FROM mentors WHERE role='specialist'")
    specialists = cursor.fetchone()[0]

    # Анкеты
    cursor.execute("SELECT COUNT(*) FROM surveys")
    surveys = cursor.fetchone()[0]

    # Средний балл
    cursor.execute("""
        SELECT ROUND(AVG(average),2)
        FROM surveys
    """)
    average = cursor.fetchone()[0]

    if average is None:
        average = 0

    conn.close()

    return {
        "students": students,
        "mentors": mentors,
        "specialists": specialists,
        "surveys": surveys,
        "average": average
    }
# =====================================================
# ОДНА АНКЕТА ДЛЯ EXCEL/PDF
# =====================================================

def get_survey_by_id(survey_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT

            surveys.id,
            surveys.survey_date,

            students.fio,
            students.speciality,
            students.course,
            COALESCE(
                surveys.enterprise,
                students.enterprise,
                'Не указано'
            ),

            mentors.fio,

            surveys.answers,

            surveys.average,
            surveys.best,
            surveys.improve,
            surveys.recommendation,
            surveys.questionnaire_key,
            surveys.questions_json,
            surveys.hard_average,
            surveys.soft_average,
            surveys.suitability_score

        FROM surveys

        JOIN students
            ON students.id = surveys.student_id

        JOIN mentors
            ON mentors.id = surveys.mentor_id

        WHERE surveys.id=?

    """,(survey_id,))

    survey = cursor.fetchone()

    conn.close()

    return survey
# =====================================================
# СТАТИСТИКА НАСТАВНИКА
# =====================================================

def get_mentor_statistics(telegram_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, fio
        FROM mentors
        WHERE telegram_id = ?
    """, (telegram_id,))

    mentor = cursor.fetchone()

    if not mentor:
        conn.close()
        return None

    mentor_id = mentor[0]
    mentor_name = mentor[1]

    cursor.execute("""
        SELECT
            COUNT(*),
            ROUND(AVG(average), 2),
            MAX(survey_date),
            ROUND(AVG(hard_average), 2),
            ROUND(AVG(soft_average), 2),
            ROUND(AVG(suitability_score), 2),
            SUM(CASE WHEN questionnaire_key='ct_assembly' THEN 1 ELSE 0 END),
            SUM(CASE WHEN questionnaire_key='ct_agro' THEN 1 ELSE 0 END)
        FROM surveys
        WHERE mentor_id = ?
    """, (mentor_id,))

    stats = cursor.fetchone()

    conn.close()

    return {
        "mentor": mentor_name,
        "count": stats[0] or 0,
        "average": stats[1] or 0,
        "last_date": stats[2] or "-",
        "hard_average": stats[3],
        "soft_average": stats[4],
        "suitability_average": stats[5],
        "ct_assembly_count": stats[6] or 0,
        "ct_agro_count": stats[7] or 0,
    }
# =====================================================
# ПРЕДПРИЯТИЯ
# =====================================================

def get_enterprises():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM enterprises
        WHERE active=1
        ORDER BY name
    """)

    enterprises = cursor.fetchall()

    conn.close()

    return enterprises


def get_enterprise(enterprise_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM enterprises WHERE id=?",
        (enterprise_id,)
    )

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


def add_enterprise(name):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO enterprises(name, active)
        VALUES(?, 1)
        ON CONFLICT(name) DO UPDATE SET active=1
        """,
        (name,)
    )

    conn.commit()
    conn.close()


def deactivate_missing_enterprises(actual_enterprises):

    if not actual_enterprises:
        return 0

    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join(["?"] * len(actual_enterprises))

    cursor.execute(
        f"""
        UPDATE enterprises
        SET active=0
        WHERE name NOT IN ({placeholders})
          AND active=1
        """,
        actual_enterprises
    )

    changed = cursor.rowcount
    conn.commit()
    conn.close()

    return changed


# =====================================================
# СТУДЕНТЫ ПО ПОТОКУ
# =====================================================

def get_streams():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT stream
        FROM students
        WHERE active=1
          AND stream IS NOT NULL
        ORDER BY stream
    """)

    streams = [row[0] for row in cursor.fetchall()]

    conn.close()

    return streams


def get_students_by_stream(stream):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, fio
        FROM students
        WHERE active=1
          AND stream=?
        ORDER BY fio
    """, (stream,))

    students = cursor.fetchall()

    conn.close()

    return students
# =====================================================
# СКРЫТИЕ СТУДЕНТОВ, ОТСУТСТВУЮЩИХ В EXCEL
# =====================================================

def deactivate_missing_students(actual_students):

    if not actual_students:
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(actual_students))

    cursor.execute(
        f"""
        UPDATE students
        SET active=0
        WHERE fio NOT IN ({placeholders})
          AND active=1
        """,
        actual_students
    )

    deactivated = cursor.rowcount

    conn.commit()
    conn.close()

    return deactivated
def get_student(student_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            fio,
            speciality,
            course,
            enterprise,
            stream

        FROM students

        WHERE id=?
    """, (student_id,))

    student = cursor.fetchone()

    conn.close()

    return student
# =====================================================
# ОБЩАЯ СТАТИСТИКА
# =====================================================

def get_statistics():

    conn = get_connection()
    cursor = conn.cursor()

    # количество студентов
    cursor.execute("SELECT COUNT(*) FROM students WHERE active=1")
    students = cursor.fetchone()[0]

    # количество наставников
    cursor.execute("SELECT COUNT(*) FROM mentors")
    mentors = cursor.fetchone()[0]

    # количество анкет
    cursor.execute("SELECT COUNT(*) FROM surveys")
    surveys = cursor.fetchone()[0]

    # средний балл
    cursor.execute("SELECT AVG(average) FROM surveys")
    avg = cursor.fetchone()[0]

    if avg is None:
        avg = 0

    # Отлично
    cursor.execute("""
        SELECT COUNT(*)
        FROM surveys
        WHERE average>=4.5
    """)
    excellent = cursor.fetchone()[0]

    # Хорошо
    cursor.execute("""
        SELECT COUNT(*)
        FROM surveys
        WHERE average>=3.5
        AND average<4.5
    """)
    good = cursor.fetchone()[0]

    # Удовлетворительно
    cursor.execute("""
        SELECT COUNT(*)
        FROM surveys
        WHERE average>=2.5
        AND average<3.5
    """)
    satisfactory = cursor.fetchone()[0]

    # Требуют внимания
    cursor.execute("""
        SELECT COUNT(*)
        FROM surveys
        WHERE average<2.5
    """)
    poor = cursor.fetchone()[0]

    conn.close()

    return (
        students,
        mentors,
        surveys,
        round(avg, 2),
        excellent,
        good,
        satisfactory,
        poor
    )


def get_extended_statistics():
    """Section and enterprise metrics for the specialist dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT
               ROUND(AVG(hard_average), 2),
               ROUND(AVG(soft_average), 2),
               ROUND(AVG(suitability_score), 2),
               SUM(CASE WHEN questionnaire_key='ct_assembly' THEN 1 ELSE 0 END),
               SUM(CASE WHEN questionnaire_key='ct_agro' THEN 1 ELSE 0 END),
               SUM(CASE WHEN questionnaire_key='legacy' OR questionnaire_key IS NULL THEN 1 ELSE 0 END)
           FROM surveys"""
    )
    row = cursor.fetchone()
    conn.close()
    return {
        "hard_average": row[0],
        "soft_average": row[1],
        "suitability_average": row[2],
        "ct_assembly_count": row[3] or 0,
        "ct_agro_count": row[4] or 0,
        "legacy_count": row[5] or 0,
    }


def get_surveys_for_lms_sync(survey_id=None):
    """Return complete saved questionnaires without changing the bot database."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            surveys.id,
            students.fio,
            students.stream,
            mentors.fio,
            mentors.telegram_id,
            COALESCE(surveys.enterprise, students.enterprise, ''),
            surveys.survey_date,
            surveys.answers,
            surveys.average,
            surveys.best,
            surveys.improve,
            surveys.recommendation,
            COALESCE(surveys.questionnaire_key, 'legacy'),
            surveys.questions_json,
            surveys.hard_average,
            surveys.soft_average,
            surveys.suitability_score
        FROM surveys
        JOIN students ON students.id = surveys.student_id
        JOIN mentors ON mentors.id = surveys.mentor_id
    """
    params = ()
    if survey_id is not None:
        query += " WHERE surveys.id = ?"
        params = (survey_id,)
    query += " ORDER BY surveys.id"
    cursor.execute(query, params)
    result = []
    for row in cursor.fetchall():
        try:
            answers = json.loads(row[7])
        except (TypeError, json.JSONDecodeError):
            answers = []
        responses = build_survey_responses(row[12], row[13], answers)
        result.append(
            {
                "source": "dual-survey-bot",
                "survey_id": row[0],
                "student_name": row[1],
                "stream": row[2],
                "mentor_name": row[3],
                "mentor_external_id": row[4],
                "enterprise": row[5],
                "survey_date": row[6],
                "answers": answers,
                "average": row[8],
                "best": row[9],
                "improve": row[10],
                "recommendation": row[11],
                "questionnaire_key": row[12],
                "responses": responses,
                "hard_average": row[14],
                "soft_average": row[15],
                "suitability_score": row[16],
            }
        )
    conn.close()
    return result


# =====================================================
# РЕГИСТРАЦИЯ СТУДЕНТА В TELEGRAM
# =====================================================

def student_exists(telegram_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM students WHERE telegram_id=? AND active=1",
        (telegram_id,),
    ).fetchone()
    conn.close()
    return row is not None


def get_student_by_telegram(telegram_id):
    conn = get_connection()
    row = conn.execute(
        """SELECT id, fio, speciality, course, enterprise, stream
           FROM students WHERE telegram_id=? AND active=1""",
        (telegram_id,),
    ).fetchone()
    conn.close()
    return row


def register_student_telegram(student_id, telegram_id, registered_at):
    conn = get_connection()
    cursor = conn.cursor()
    student = cursor.execute(
        "SELECT id, fio, telegram_id FROM students WHERE id=? AND active=1",
        (student_id,),
    ).fetchone()
    if not student:
        conn.close()
        raise ValueError("Студент не найден")
    if student[2] not in (None, telegram_id):
        conn.close()
        raise ValueError("Эта карточка уже связана с другим Telegram-аккаунтом")
    existing = cursor.execute(
        "SELECT id FROM students WHERE telegram_id=? AND id<>?",
        (telegram_id, student_id),
    ).fetchone()
    if existing:
        conn.close()
        raise ValueError("Этот Telegram-аккаунт уже связан с другим студентом")
    cursor.execute(
        "UPDATE students SET telegram_id=?, registered_at=? WHERE id=?",
        (telegram_id, registered_at, student_id),
    )
    conn.commit()
    conn.close()
    return student[1]


# =====================================================
# СПРАВОЧНИК НАСТАВНИКОВ ИЗ LMS
# =====================================================

def sync_mentor_directory(mentors):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE mentor_directory SET active=0")
    for mentor in mentors:
        cursor.execute(
            """INSERT INTO mentor_directory
               (lms_id, full_name, enterprise, city, workshop, qualification, active, synced_at)
               VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'))
               ON CONFLICT(lms_id) DO UPDATE SET
                 full_name=excluded.full_name,
                 enterprise=excluded.enterprise,
                 city=excluded.city,
                 workshop=excluded.workshop,
                 qualification=excluded.qualification,
                 active=1,
                 synced_at=excluded.synced_at""",
            (
                int(mentor["id"]),
                str(mentor.get("full_name") or "").strip(),
                str(mentor.get("enterprise") or "").strip(),
                str(mentor.get("city") or "").strip(),
                str(mentor.get("workshop") or "").strip(),
                str(mentor.get("qualification") or "").strip(),
            ),
        )
    conn.commit()
    conn.close()


def get_directory_mentors():
    conn = get_connection()
    rows = conn.execute(
        """SELECT lms_id, full_name, enterprise, city, workshop, qualification
           FROM mentor_directory WHERE active=1
           ORDER BY enterprise, full_name"""
    ).fetchall()
    conn.close()
    keys = ("lms_id", "full_name", "enterprise", "city", "workshop", "qualification")
    return [dict(zip(keys, row)) for row in rows]


def get_directory_mentor(lms_id):
    conn = get_connection()
    row = conn.execute(
        """SELECT lms_id, full_name, enterprise, city, workshop, qualification
           FROM mentor_directory WHERE lms_id=? AND active=1""",
        (lms_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    keys = ("lms_id", "full_name", "enterprise", "city", "workshop", "qualification")
    return dict(zip(keys, row))


# =====================================================
# АНОНИМНЫЕ ОТЗЫВЫ СТУДЕНТОВ О НАСТАВНИКАХ
# =====================================================

def save_mentor_feedback(
    student_id,
    mentor,
    module,
    submitted_at,
    ratings,
    questions,
    average,
    open_answers,
):
    student = get_student(student_id)
    if not student:
        raise ValueError("Студент не найден")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO mentor_feedback
           (student_id, mentor_lms_id, mentor_name, enterprise, city, workshop,
            speciality, course, stream, module, submitted_at, ratings_json,
            questions_json, average, strengths, weaknesses, missing_topics,
            liked, disliked, conclusion)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            student_id,
            int(mentor["lms_id"]),
            mentor["full_name"],
            mentor.get("enterprise", ""),
            mentor.get("city", ""),
            mentor.get("workshop", ""),
            student[2] or "",
            student[3],
            student[5],
            module.strip(),
            submitted_at,
            json.dumps(ratings, ensure_ascii=False),
            json.dumps(questions, ensure_ascii=False),
            average,
            open_answers.get("strengths", ""),
            open_answers.get("weaknesses", ""),
            open_answers.get("missing_topics", ""),
            open_answers.get("liked", ""),
            open_answers.get("disliked", ""),
            open_answers.get("conclusion", ""),
        ),
    )
    feedback_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return feedback_id


def _feedback_rows(where="", params=()):
    conn = get_connection()
    rows = conn.execute(
        f"""SELECT f.id, f.submitted_at, f.mentor_lms_id, f.mentor_name,
                   f.enterprise, f.city, f.workshop, f.module, f.average,
                   f.ratings_json, f.questions_json, f.strengths, f.weaknesses,
                   f.missing_topics, f.liked, f.disliked, f.conclusion,
                   s.id, s.fio, s.speciality, s.course, s.stream
            FROM mentor_feedback f
            JOIN students s ON s.id=f.student_id
            {where}
            ORDER BY f.id DESC""",
        params,
    ).fetchall()
    conn.close()
    keys = (
        "id", "submitted_at", "mentor_lms_id", "mentor_name", "enterprise",
        "city", "workshop", "module", "average", "ratings_json",
        "questions_json", "strengths", "weaknesses", "missing_topics",
        "liked", "disliked", "conclusion", "student_id", "student_name",
        "speciality", "course", "stream",
    )
    result = []
    for row in rows:
        item = dict(zip(keys, row))
        for field in ("ratings_json", "questions_json"):
            try:
                item[field.removesuffix("_json")] = json.loads(item.pop(field))
            except (TypeError, json.JSONDecodeError):
                item[field.removesuffix("_json")] = []
        result.append(item)
    return result


def get_all_mentor_feedback():
    return _feedback_rows()


def get_mentor_feedback(feedback_id):
    rows = _feedback_rows("WHERE f.id=?", (feedback_id,))
    return rows[0] if rows else None


def get_student_feedback(telegram_id):
    return _feedback_rows("WHERE s.telegram_id=?", (telegram_id,))


def get_mentor_feedback_statistics():
    conn = get_connection()
    rows = conn.execute(
        """SELECT mentor_lms_id, mentor_name, enterprise,
                  COUNT(*) AS feedback_count, ROUND(AVG(average), 2) AS average,
                  MAX(submitted_at) AS last_feedback
           FROM mentor_feedback
           GROUP BY mentor_lms_id, mentor_name, enterprise
           ORDER BY mentor_name"""
    ).fetchall()
    totals = conn.execute(
        """SELECT COUNT(*), ROUND(AVG(average), 2), COUNT(DISTINCT mentor_lms_id)
           FROM mentor_feedback"""
    ).fetchone()
    conn.close()
    keys = ("mentor_lms_id", "mentor_name", "enterprise", "feedback_count", "average", "last_feedback")
    return {
        "mentors": [dict(zip(keys, row)) for row in rows],
        "count": totals[0] or 0,
        "average": totals[1] or 0,
        "mentor_count": totals[2] or 0,
    }


def get_mentor_feedback_for_lms_sync(feedback_id=None):
    where = "WHERE f.id=?" if feedback_id is not None else ""
    records = _feedback_rows(where, (feedback_id,) if feedback_id is not None else ())
    payloads = []
    for record in reversed(records):
        payloads.append(
            {
                "source": "dual-survey-bot",
                "feedback_id": record["id"],
                "student_external_id": record["student_id"],
                "student_name": record["student_name"],
                "stream": record["stream"],
                "speciality": record["speciality"],
                "course": record["course"],
                "mentor_id": record["mentor_lms_id"],
                "mentor_name": record["mentor_name"],
                "enterprise": record["enterprise"],
                "city": record["city"],
                "workshop": record["workshop"],
                "module": record["module"],
                "submitted_at": record["submitted_at"],
                "ratings": [
                    {
                        "code": question.get("code", f"MF-{index + 1:02d}"),
                        "question": question.get("text", ""),
                        "score": int(score),
                    }
                    for index, (question, score) in enumerate(
                        zip(record["questions"], record["ratings"])
                    )
                ],
                "average": record["average"],
                "strengths": record["strengths"],
                "weaknesses": record["weaknesses"],
                "missing_topics": record["missing_topics"],
                "liked": record["liked"],
                "disliked": record["disliked"],
                "conclusion": record["conclusion"],
            }
        )
    return payloads
