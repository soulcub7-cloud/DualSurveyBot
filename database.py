import sqlite3
import json

DATABASE = "data/survey.db"


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
        enterprise TEXT
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

        FOREIGN KEY (mentor_id) REFERENCES mentors(id),
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

def add_student(fio, speciality, course, enterprise):

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
                speciality=?,
                course=?,
                enterprise=?

            WHERE fio=?
            """,
            (
                speciality,
                course,
                enterprise,
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
            speciality,
            course,
            enterprise
        )
        VALUES(?,?,?,?)
        """,
        (
            fio,
            speciality,
            course,
            enterprise
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

def save_survey(
        mentor_id,
        student_id,
        answers,
        average,
        best,
        improve,
        recommendation,
        survey_date
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
            recommendation

        )

        VALUES(?,?,?,?,?,?,?,?)

        """,
        (
            mentor_id,
            student_id,
            survey_date,
            json.dumps(answers),
            average,
            best,
            improve,
            recommendation
        )
    )

    conn.commit()
    conn.close()


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
            surveys.*,
            students.fio

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
def get_mentor_role(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role
        FROM mentors
        WHERE telegram_id=?
    """, (telegram_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]

    return "mentor"
def set_specialist(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE mentors
        SET role='specialist'
        WHERE telegram_id=?
    """, (telegram_id,))

    conn.commit()
    conn.close()
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

    conn.commit()
    conn.close()


create_tables()
migrate()
from config import SPECIALIST_ID

def get_mentor_role(telegram_id):
    if telegram_id == SPECIALIST_ID:
        return "specialist"
    return "mentor"
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
            students.enterprise,

            mentors.fio,

            surveys.answers,

            surveys.average,
            surveys.best,
            surveys.improve,
            surveys.recommendation

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

            ROUND(AVG(surveys.average),2)

        FROM students

        LEFT JOIN surveys
            ON surveys.student_id = students.id

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

            ROUND(AVG(surveys.average), 2)

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
    cursor.execute("SELECT COUNT(*) FROM students")
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
            students.enterprise,

            mentors.fio,

            surveys.answers,

            surveys.average,
            surveys.best,
            surveys.improve,
            surveys.recommendation

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
            MAX(survey_date)
        FROM surveys
        WHERE mentor_id = ?
    """, (mentor_id,))

    stats = cursor.fetchone()

    conn.close()

    return {
        "mentor": mentor_name,
        "count": stats[0] or 0,
        "average": stats[1] or 0,
        "last_date": stats[2] or "-"
    }
# =====================================================
# ПРЕДПРИЯТИЯ
# =====================================================

def get_enterprises():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            enterprise,
            COUNT(*)

        FROM students

        GROUP BY enterprise

        ORDER BY enterprise
    """)

    enterprises = cursor.fetchall()

    conn.close()

    return enterprises


# =====================================================
# СТУДЕНТЫ ПО ПРЕДПРИЯТИЮ
# =====================================================

def get_students_by_enterprise(enterprise):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        fio,
        course,
        speciality

    FROM students

    WHERE enterprise=?

    ORDER BY fio
""", (enterprise,))

    students = cursor.fetchall()

    conn.close()

    return students
# =====================================================
# УДАЛЕНИЕ СТУДЕНТОВ, ОТСУТСТВУЮЩИХ В EXCEL
# =====================================================

def delete_missing_students(actual_students):

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(actual_students))

    if actual_students:

        cursor.execute(
            f"""
            DELETE FROM students
            WHERE fio NOT IN ({placeholders})
            """,
            actual_students
        )

    else:

        cursor.execute("DELETE FROM students")

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted
def get_student(student_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            fio,
            speciality,
            course,
            enterprise

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
    cursor.execute("SELECT COUNT(*) FROM students")
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