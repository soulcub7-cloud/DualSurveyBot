#!/usr/bin/env python3
"""CT Assembly Learning Hub — dependency-free LMS demo server."""

from __future__ import annotations

import json
import io
import hashlib
import hmac
import mimetypes
import os
import re
import secrets
import sqlite3
import sys
import zipfile
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from xml.sax.saxutils import escape as xml_escape


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DATA_DIR = ROOT / "data"
DB_PATH = Path(os.environ.get("LMS_DB_PATH", str(DATA_DIR / "lms.db")))
BUSINESS_TIMEZONE = timezone(timedelta(hours=5))
PASSWORD_ITERATIONS = 240_000
SESSION_HOURS = 12
DEFAULT_ADMIN_PHONE = "+77000000000"
DEFAULT_ADMIN_PASSWORD = "Admin2026!"
DEFAULT_INITIAL_PASSWORD = "Start2026!"
DEFAULT_SUPERVISOR_PHONE = "+77015499234"
DEFAULT_SUPERVISOR_PASSWORD = "Leader2026!"
APP_VERSION = "11.6.1"

PROFESSIONAL_SKILLS = [
    ("HSE-01", "Охрана труда и безопасность", "Hard skill", "Производственная безопасность", 1, "Соблюдает требования охраны труда, применяет СИЗ и безопасно действует в производственной зоне.", 1, 10),
    ("TOOL-01", "Работа с ручным и электроинструментом", "Hard skill", "Технические hard skills", 1, "Правильно выбирает, проверяет и безопасно применяет ручной и электрический инструмент.", 2, 20),
    ("MET-01", "Работа с измерительным инструментом", "Hard skill", "Технические hard skills", 1, "Выполняет измерения, считывает показания и корректно фиксирует результат.", 3, 30),
    ("DOC-01", "Работа с технической документацией", "Hard skill", "Технические hard skills", 1, "Понимает чертежи, схемы, технологические карты и производственные инструкции.", 4, 40),
    ("QLT-01", "Качество выполнения работы", "Hard skill", "Качество и оборудование", 1, "Соблюдает требования к результату, предупреждает брак и снижает количество переделок.", 6, 50),
    ("EQP-01", "Бережное отношение к оборудованию и инструменту", "Hard skill", "Качество и оборудование", 1, "Аккуратно использует оборудование, поддерживает его сохранность и сообщает о неисправностях.", 7, 60),
    ("5S-01", "Организация рабочего места по 5S", "Hard skill", "Качество и оборудование", 1, "Поддерживает сортировку, порядок, чистоту, стандартизацию и улучшение рабочего места.", None, 70),
    ("SFT-01", "Самостоятельность в работе", "Soft skill", "Soft skills", 1, "Выполняет освоенные операции без постоянных подсказок и своевременно обращается за помощью.", 5, 110),
    ("SFT-02", "Исполнительность и ответственность", "Soft skill", "Soft skills", 1, "Доводит задание до результата, соблюдает сроки и отвечает за качество своей работы.", 8, 120),
    ("SFT-03", "Трудовая дисциплина", "Soft skill", "Soft skills", 1, "Соблюдает график, правила предприятия и договорённости с наставником.", 9, 130),
    ("SFT-04", "Работа в коллективе", "Soft skill", "Soft skills", 1, "Уважительно взаимодействует с коллегами, сообщает о проблемах и принимает обратную связь.", 10, 140),
    ("SFT-05", "Инициативность", "Soft skill", "Soft skills", 1, "Проявляет интерес к работе, задаёт уточняющие вопросы и предлагает обоснованные улучшения.", 11, 150),
    ("SFT-06", "Обучаемость", "Soft skill", "Soft skills", 1, "Осваивает новые операции после объяснения и показа и переносит знания в практику.", 12, 160),
    ("SFT-07", "Принятие решений", "Soft skill", "Soft skills", 1, "Самостоятельно принимает безопасные решения в пределах подготовки и допуска.", 13, 170),
    ("SFT-08", "Работа над ошибками", "Soft skill", "Soft skills", 1, "Понимает причины ошибок, корректирует действия и не повторяет выявленные нарушения.", 14, 180),
    ("SFT-09", "Профессиональное развитие", "Soft skill", "Soft skills", 1, "Стремится расширять знания, улучшать результат и осознанно развивать профессиональные навыки.", 15, 190),
    ("ASM-01", "Сборка узла по технологическому процессу", "Hard skill", "Профильные hard skills", 1, "Собирает узел с соблюдением последовательности операций и требований технологического процесса.", None, 210),
    ("WLD-01", "Подготовка деталей к сварке", "Hard skill", "Профильные hard skills", 1, "Подготавливает кромки, детали, оборудование и рабочее место к выполнению сварочных работ.", None, 220),
    ("WLD-02", "Выполнение ручной дуговой сварки", "Hard skill", "Профильные hard skills", 1, "Выбирает режим и выполняет сварное соединение с соблюдением требований безопасности и качества.", None, 230),
    ("QLT-02", "Контроль геометрических параметров", "Hard skill", "Профильные hard skills", 1, "Проверяет размеры, геометрию и допуски детали предусмотренными средствами измерения.", None, 240),
    ("QLT-03", "Выявление и регистрация дефектов", "Hard skill", "Профильные hard skills", 1, "Распознаёт типовые дефекты, сообщает о них и корректно оформляет результат контроля.", None, 250),
]

SAFETY_QUIZ_QUESTIONS = [
    (
        "Что необходимо сделать перед началом работы на оборудовании?",
        ["Сразу включить оборудование", "Проверить исправность и рабочую зону", "Снять защитный экран", "Попросить студента включить станок"],
        1,
    ),
    (
        "Как следует действовать при обнаружении неисправности?",
        ["Продолжить работу на малой скорости", "Исправить самостоятельно без уведомления", "Остановить работу и сообщить наставнику", "Оставить оборудование включённым"],
        2,
    ),
    (
        "Когда средства индивидуальной защиты обязательны?",
        ["Только во время проверки", "Только для новых сотрудников", "По желанию работника", "Всегда в обозначенной производственной зоне"],
        3,
    ),
    (
        "Что нужно сделать при появлении дыма или признаков пожара?",
        ["Остановить работу, сообщить о пожаре и действовать по плану эвакуации", "Открыть все двери и продолжить работу", "Самостоятельно искать источник, никого не уведомляя", "Спрятать горючие материалы в шкаф"],
        0,
    ),
    (
        "Как безопасно помочь человеку, попавшему под действие электрического тока?",
        ["Сразу оттащить его голыми руками", "Отключить питание и вызвать помощь, не касаясь пострадавшего до снятия напряжения", "Полить место водой", "Подождать, пока оборудование отключится само"],
        1,
    ),
    (
        "Когда следует использовать кнопку аварийной остановки?",
        ["В конце каждой смены", "Для обычной остановки станка", "При непосредственной угрозе человеку или аварийной ситуации", "Только с разрешения другого студента"],
        2,
    ),
    (
        "Как должны содержаться проходы и эвакуационные выходы?",
        ["Их можно временно занимать готовой продукцией", "На них допускается хранить инструмент", "Их можно перекрывать во время перерыва", "Они должны быть свободными и обозначенными"],
        3,
    ),
    (
        "Что необходимо сделать с длинными волосами и свободной одеждой перед работой у вращающихся механизмов?",
        ["Убрать волосы и застегнуть либо закрепить одежду", "Надеть поверх одежды шарф", "Работать только на малой скорости", "Ничего, если работа займёт менее минуты"],
        0,
    ),
    (
        "Как правильно перемещать тяжёлую деталь вручную?",
        ["Поднять рывком без оценки веса", "Оценить массу и при необходимости использовать подъёмное средство или помощь", "Катить деталь ногой", "Переносить одному, чтобы не мешать коллегам"],
        1,
    ),
    (
        "Что делать при обнаружении разлива масла на полу?",
        ["Обойти место и никому не говорить", "Засыпать разлив любым материалом и уйти", "Оградить опасное место, сообщить ответственному и убрать разлив по установленному порядку", "Смыть масло водой в ближайший сток"],
        2,
    ),
    (
        "При каком условии разрешается выполнять работу на высоте?",
        ["Если студент уверен в себе", "Если работа займёт несколько минут", "Если рядом находится коллега", "После допуска, инструктажа и применения предусмотренной защиты от падения"],
        3,
    ),
    (
        "Что необходимо проверить перед началом сварочных или других огневых работ?",
        ["Наличие СИЗ, исправность оборудования, ограждение зоны и отсутствие горючих материалов", "Только наличие электродов", "Только освещение рабочего места", "Можно ли открыть окно"],
        0,
    ),
    (
        "Как защитить слух в зоне с повышенным уровнем шума?",
        ["Закрыть уши руками", "Использовать выданные противошумные наушники или вкладыши", "Работать быстрее", "Находиться дальше от наставника"],
        1,
    ),
    (
        "Как следует пересекать маршрут движения погрузчика?",
        ["Перебежать перед погрузчиком", "Идти в любом месте, если погрузчик движется медленно", "Использовать обозначенный проход, убедиться, что водитель вас видит, и уступить технике", "Подать водителю сигнал рукой и сразу идти"],
        2,
    ),
    (
        "Что включает безопасное отключение оборудования перед ремонтом или очисткой?",
        ["Только нажатие кнопки «Стоп»", "Отключение освещения в цехе", "Предупреждение коллег без отключения энергии", "Изоляцию источников энергии, блокировку, маркировку и проверку отсутствия энергии"],
        3,
    ),
]


def current_date() -> date:
    """Calendar date for the Kazakhstan training centre (UTC+5)."""
    return datetime.now(BUSINESS_TIMEZONE).date()


def plural_ru(number: int, one: str, few: str, many: str) -> str:
    n10, n100 = number % 10, number % 100
    if n10 == 1 and n100 != 11:
        return one
    if 2 <= n10 <= 4 and not 12 <= n100 <= 14:
        return few
    return many


def db_connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def rows(cursor: sqlite3.Cursor) -> list[dict]:
    return [dict(item) for item in cursor.fetchall()]


def init_database(reset: bool = False) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if reset and DB_PATH.exists():
        DB_PATH.unlink()

    with db_connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS mentors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                workshop TEXT NOT NULL,
                qualification TEXT NOT NULL,
                student_limit INTEGER NOT NULL DEFAULT 3,
                phone TEXT DEFAULT '',
                enterprise TEXT NOT NULL DEFAULT '',
                city TEXT NOT NULL DEFAULT '',
                role_type TEXT NOT NULL DEFAULT 'mentor',
                can_mentor INTEGER NOT NULL DEFAULT 1,
                is_archived INTEGER NOT NULL DEFAULT 0,
                archived_at TEXT
            );

            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                institution TEXT NOT NULL,
                specialty TEXT NOT NULL,
                course INTEGER NOT NULL,
                stream TEXT NOT NULL,
                base_city TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Ожидает допуска',
                mentor_id INTEGER REFERENCES mentors(id),
                avatar_color TEXT NOT NULL DEFAULT '#D71920',
                phone TEXT DEFAULT '',
                birth_date TEXT DEFAULT '',
                address TEXT DEFAULT '',
                additional_info TEXT DEFAULT '',
                is_archived INTEGER NOT NULL DEFAULT 0,
                archived_at TEXT,
                archived_from_status TEXT
            );

            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                module TEXT NOT NULL,
                required INTEGER NOT NULL DEFAULT 1,
                description TEXT DEFAULT '',
                bot_question_index INTEGER,
                display_order INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                duration_hours INTEGER NOT NULL,
                description TEXT NOT NULL,
                pass_score INTEGER NOT NULL DEFAULT 80,
                color TEXT NOT NULL DEFAULT '#D71920',
                is_archived INTEGER NOT NULL DEFAULT 0,
                archived_at TEXT
            );

            CREATE TABLE IF NOT EXISTS course_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id),
                course_id INTEGER NOT NULL REFERENCES courses(id),
                percent INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'not_started',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, course_id)
            );

            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL REFERENCES courses(id),
                question TEXT NOT NULL,
                options_json TEXT NOT NULL,
                correct_index INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id),
                course_id INTEGER NOT NULL REFERENCES courses(id),
                score INTEGER NOT NULL,
                correct_answers INTEGER,
                total_questions INTEGER,
                passed INTEGER NOT NULL,
                attempted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_legacy INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id),
                skill_id INTEGER NOT NULL REFERENCES skills(id),
                status TEXT NOT NULL DEFAULT 'not_started',
                score INTEGER,
                note TEXT DEFAULT '',
                mentor_id INTEGER REFERENCES mentors(id),
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, skill_id)
            );

            CREATE TABLE IF NOT EXISTS skill_assessment_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id),
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                mentor_name TEXT NOT NULL,
                mentor_external_id TEXT DEFAULT '',
                enterprise TEXT DEFAULT '',
                assessed_at TEXT NOT NULL,
                average_score REAL NOT NULL,
                best TEXT DEFAULT '',
                improve TEXT DEFAULT '',
                recommendation TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, external_id)
            );

            CREATE TABLE IF NOT EXISTS skill_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL REFERENCES skill_assessment_batches(id) ON DELETE CASCADE,
                student_id INTEGER NOT NULL REFERENCES students(id),
                skill_id INTEGER NOT NULL REFERENCES skills(id),
                score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
                status TEXT NOT NULL,
                assessed_at TEXT NOT NULL,
                UNIQUE(batch_id, skill_id)
            );

            CREATE TABLE IF NOT EXISTS rotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id),
                city TEXT NOT NULL,
                company TEXT NOT NULL,
                workshop TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Запланирована'
            );

            CREATE TABLE IF NOT EXISTS safety_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id),
                score INTEGER NOT NULL,
                passed INTEGER NOT NULL,
                completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                recipient_id INTEGER,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'info',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                dedupe_key TEXT UNIQUE,
                is_read INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id),
                attendance_date TEXT NOT NULL,
                status TEXT NOT NULL,
                hours REAL NOT NULL DEFAULT 0,
                note TEXT DEFAULT '',
                marked_by_mentor_id INTEGER REFERENCES mentors(id),
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, attendance_date)
            );

            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id),
                course_id INTEGER REFERENCES courses(id),
                evaluation_type TEXT NOT NULL,
                section_title TEXT NOT NULL,
                score INTEGER NOT NULL,
                grade INTEGER NOT NULL,
                comment TEXT DEFAULT '',
                rotation_id INTEGER REFERENCES rotations(id),
                evaluator_id INTEGER REFERENCES mentors(id),
                evaluated_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'mentor', 'student')),
                full_name TEXT NOT NULL,
                student_id INTEGER UNIQUE REFERENCES students(id),
                mentor_id INTEGER UNIQUE REFERENCES mentors(id),
                must_change_password INTEGER NOT NULL DEFAULT 1,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login_at TEXT
            );

            CREATE TABLE IF NOT EXISTS auth_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
            CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
            CREATE INDEX IF NOT EXISTS idx_evaluations_student ON evaluations(student_id);
            CREATE INDEX IF NOT EXISTS idx_quiz_attempts_student ON quiz_attempts(student_id);
            CREATE INDEX IF NOT EXISTS idx_quiz_attempts_course ON quiz_attempts(course_id);
            CREATE INDEX IF NOT EXISTS idx_skill_batches_student ON skill_assessment_batches(student_id);
            CREATE INDEX IF NOT EXISTS idx_skill_assessments_student ON skill_assessments(student_id);
            CREATE INDEX IF NOT EXISTS idx_skill_assessments_skill ON skill_assessments(skill_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON auth_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON auth_sessions(expires_at);
            """
        )
        ensure_column(db, "mentors", "is_archived", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "mentors", "archived_at", "TEXT")
        ensure_column(db, "mentors", "enterprise", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "mentors", "city", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "mentors", "role_type", "TEXT NOT NULL DEFAULT 'mentor'")
        ensure_column(db, "mentors", "can_mentor", "INTEGER NOT NULL DEFAULT 1")
        ensure_column(db, "students", "is_archived", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "students", "archived_at", "TEXT")
        ensure_column(db, "students", "archived_from_status", "TEXT")
        ensure_column(db, "students", "phone", "TEXT DEFAULT ''")
        ensure_column(db, "students", "birth_date", "TEXT DEFAULT ''")
        ensure_column(db, "students", "address", "TEXT DEFAULT ''")
        ensure_column(db, "students", "additional_info", "TEXT DEFAULT ''")
        ensure_column(db, "courses", "is_archived", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "courses", "archived_at", "TEXT")
        ensure_column(db, "evaluations", "course_id", "INTEGER REFERENCES courses(id)")
        ensure_column(db, "skills", "bot_question_index", "INTEGER")
        ensure_column(db, "skills", "display_order", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(db, "skills", "is_active", "INTEGER NOT NULL DEFAULT 1")
        ensure_column(db, "users", "can_delete", "INTEGER NOT NULL DEFAULT 1")
        db.execute("CREATE INDEX IF NOT EXISTS idx_evaluations_course ON evaluations(course_id)")
        db.execute(
            """UPDATE evaluations SET grade = CASE
               WHEN score >= 90 THEN 5
               WHEN score >= 70 THEN 4
               WHEN score >= 50 THEN 3
               ELSE 2 END"""
        )
        count = db.execute("SELECT COUNT(*) AS n FROM students").fetchone()["n"]
        if count == 0:
            seed_database(db)
        ensure_ct_assembly_name(db)
        ensure_mentor_roles(db)
        ensure_dual_mentor_roles(db)
        ensure_professional_skill_catalog(db)
        ensure_safety_quiz_questions(db)
        backfill_legacy_quiz_attempts(db)
        ensure_user_accounts(db)
        ensure_kurmanova_supervisor(db)
        db.commit()


def ensure_column(db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def ensure_ct_assembly_name(db: sqlite3.Connection) -> None:
    """Replace the former ST Assembly name in existing user data once."""
    migration_key = "company_name_ct_assembly_v10_2"
    if db.execute("SELECT 1 FROM app_meta WHERE key = ?", (migration_key,)).fetchone():
        return
    text_fields = {
        "mentors": ("enterprise", "workshop", "qualification"),
        "students": ("institution", "specialty", "base_city", "status", "address", "additional_info"),
        "skills": ("title", "module", "description"),
        "courses": ("title", "category", "description"),
        "quiz_questions": ("question", "options_json"),
        "progress": ("note",),
        "skill_assessment_batches": ("enterprise", "best", "improve", "recommendation"),
        "rotations": ("city", "company", "workshop"),
        "notifications": ("title", "message"),
        "attendance": ("note",),
        "evaluations": ("section_title", "comment"),
    }
    for table, columns in text_fields.items():
        for column in columns:
            db.execute(
                f"UPDATE {table} SET {column} = REPLACE({column}, ?, ?) WHERE {column} LIKE ?",
                ("ST Assembly", "CT Assembly", "%ST Assembly%"),
            )
    db.execute(
        "INSERT INTO app_meta (key, value) VALUES (?, ?)",
        (migration_key, current_date().isoformat()),
    )


def ensure_mentor_roles(db: sqlite3.Connection) -> None:
    """Separate programme leaders from production mentors once, without losing records."""
    migration_key = "mentor_roles_v10"
    if db.execute("SELECT 1 FROM app_meta WHERE key = ?", (migration_key,)).fetchone():
        return
    for mentor in db.execute("SELECT id, full_name FROM mentors").fetchall():
        normalized_name = str(mentor["full_name"] or "").casefold()
        if "уткин" in normalized_name or "орленко" in normalized_name:
            db.execute(
                "UPDATE mentors SET role_type = 'supervisor' WHERE id = ?",
                (mentor["id"],),
            )
    db.execute(
        "INSERT INTO app_meta (key, value) VALUES (?, ?)",
        (migration_key, current_date().isoformat()),
    )


def ensure_dual_mentor_roles(db: sqlite3.Connection) -> None:
    """Keep programme leadership separate from permission to mentor students."""
    migration_key = "dual_mentor_roles_v11_6"

    # These programme leaders also work directly with students. Keep them
    # selectable as mentors even after this migration has already run.
    for mentor in db.execute("SELECT id, full_name FROM mentors").fetchall():
        normalized_name = normalize_person_name(mentor["full_name"])
        if "орленко" in normalized_name or "уткин" in normalized_name:
            db.execute(
                "UPDATE mentors SET can_mentor = 1 WHERE id = ?",
                (mentor["id"],),
            )

    if db.execute("SELECT 1 FROM app_meta WHERE key = ?", (migration_key,)).fetchone():
        return

    assigned_mentor_ids = {
        int(item["mentor_id"])
        for item in db.execute(
            "SELECT DISTINCT mentor_id FROM students WHERE mentor_id IS NOT NULL"
        ).fetchall()
    }
    for mentor in db.execute("SELECT id, full_name, role_type FROM mentors").fetchall():
        normalized_name = normalize_person_name(mentor["full_name"])
        can_mentor = (
            mentor["role_type"] == "mentor"
            or int(mentor["id"]) in assigned_mentor_ids
            or "орленко" in normalized_name
            or "уткин" in normalized_name
        )
        db.execute(
            "UPDATE mentors SET can_mentor = ? WHERE id = ?",
            (int(can_mentor), mentor["id"]),
        )
    db.execute(
        "INSERT INTO app_meta (key, value) VALUES (?, ?)",
        (migration_key, current_date().isoformat()),
    )


def ensure_kurmanova_supervisor(db: sqlite3.Connection) -> None:
    """Ensure the programme leader account exists without resetting an existing password."""
    full_name = "Курманова Лейла Юрьевна"
    phone = normalize_phone(os.environ.get("LMS_SUPERVISOR_PHONE", DEFAULT_SUPERVISOR_PHONE))
    mentor = None
    for item in db.execute("SELECT * FROM mentors").fetchall():
        same_phone = bool(item["phone"]) and normalize_phone(item["phone"]) == phone
        same_name = normalize_person_name(item["full_name"]) == normalize_person_name(full_name)
        if same_phone or same_name:
            mentor = item
            break
    if mentor:
        mentor_id = int(mentor["id"])
        db.execute(
            """UPDATE mentors SET full_name = ?, phone = ?, role_type = 'supervisor',
               can_mentor = 0,
               enterprise = CASE WHEN TRIM(enterprise) = '' THEN 'CT Assembly' ELSE enterprise END,
               city = CASE WHEN TRIM(city) = '' THEN 'Петропавловск' ELSE city END,
               workshop = CASE WHEN TRIM(workshop) = '' THEN 'Руководство' ELSE workshop END,
               qualification = CASE WHEN TRIM(qualification) = '' THEN 'HR-директор' ELSE qualification END,
               is_archived = 0, archived_at = NULL
               WHERE id = ?""",
            (full_name, phone, mentor_id),
        )
    else:
        cursor = db.execute(
            """INSERT INTO mentors
               (full_name, workshop, qualification, student_limit, phone,
                enterprise, city, role_type, can_mentor)
               VALUES (?, 'Руководство', 'HR-директор', 1, ?, 'CT Assembly',
                       'Петропавловск', 'supervisor', 0)""",
            (full_name, phone),
        )
        mentor_id = int(cursor.lastrowid)

    account = db.execute(
        "SELECT id FROM users WHERE mentor_id = ? OR phone = ? ORDER BY mentor_id IS NOT NULL DESC LIMIT 1",
        (mentor_id, phone),
    ).fetchone()
    if account:
        db.execute(
            """UPDATE users SET phone = ?, role = 'admin', full_name = ?, mentor_id = ?,
               can_delete = 0, is_active = 1 WHERE id = ?""",
            (phone, full_name, mentor_id, account["id"]),
        )
    else:
        user_id = create_user(
            db,
            phone,
            os.environ.get("LMS_SUPERVISOR_PASSWORD", DEFAULT_SUPERVISOR_PASSWORD),
            "admin",
            full_name,
            mentor_id=mentor_id,
        )
        db.execute("UPDATE users SET can_delete = 0 WHERE id = ?", (user_id,))


def ensure_professional_skill_catalog(db: sqlite3.Connection) -> None:
    """Install the v9 competency catalog and preserve compatible old progress."""
    for skill in PROFESSIONAL_SKILLS:
        db.execute(
            """INSERT INTO skills
               (code, title, category, module, required, description,
                bot_question_index, display_order, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
               ON CONFLICT(code) DO UPDATE SET
                 title = excluded.title,
                 category = excluded.category,
                 module = excluded.module,
                 required = excluded.required,
                 description = excluded.description,
                 bot_question_index = excluded.bot_question_index,
                 display_order = excluded.display_order,
                 is_active = 1""",
            skill,
        )

    status_rank = {"not_started": 0, "in_progress": 1, "confirmed": 2}
    legacy_mapping = {
        "TB-01": "HSE-01",
        "TB-02": "HSE-01",
        "DR-01": "DOC-01",
        "QM-01": "QLT-02",
        "WL-01": "WLD-01",
        "WL-02": "WLD-02",
        "AS-01": "ASM-01",
        "QC-01": "QLT-03",
        "CO-01": "SFT-04",
    }
    for legacy_code, new_code in legacy_mapping.items():
        legacy = db.execute("SELECT id FROM skills WHERE code = ?", (legacy_code,)).fetchone()
        target = db.execute("SELECT id FROM skills WHERE code = ?", (new_code,)).fetchone()
        if not legacy or not target or legacy["id"] == target["id"]:
            continue
        old_rows = db.execute(
            "SELECT * FROM progress WHERE skill_id = ?", (legacy["id"],)
        ).fetchall()
        for old in old_rows:
            current = db.execute(
                "SELECT * FROM progress WHERE student_id = ? AND skill_id = ?",
                (old["student_id"], target["id"]),
            ).fetchone()
            if current and status_rank.get(current["status"], 0) > status_rank.get(old["status"], 0):
                continue
            db.execute(
                """INSERT INTO progress
                   (student_id, skill_id, status, score, note, mentor_id, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(student_id, skill_id) DO UPDATE SET
                     status = excluded.status,
                     score = COALESCE(excluded.score, progress.score),
                     note = CASE WHEN excluded.note != '' THEN excluded.note ELSE progress.note END,
                     mentor_id = COALESCE(excluded.mentor_id, progress.mentor_id),
                     updated_at = excluded.updated_at""",
                (
                    old["student_id"], target["id"], old["status"], old["score"],
                    old["note"], old["mentor_id"], old["updated_at"],
                ),
            )

    active_codes = [skill[0] for skill in PROFESSIONAL_SKILLS]
    placeholders = ",".join("?" for _ in active_codes)
    db.execute(
        f"UPDATE skills SET is_active = CASE WHEN code IN ({placeholders}) THEN 1 ELSE 0 END",
        active_codes,
    )
    db.execute(
        "DELETE FROM progress WHERE skill_id IN (SELECT id FROM skills WHERE is_active = 0)"
    )
    db.execute(
        """INSERT OR IGNORE INTO progress (student_id, skill_id)
           SELECT s.id, sk.id FROM students s CROSS JOIN skills sk
           WHERE s.is_archived = 0 AND sk.is_active = 1"""
    )


def backfill_legacy_quiz_attempts(db: sqlite3.Connection) -> None:
    """Keep course results recorded before attempt history was introduced."""
    safety_course = db.execute(
        "SELECT id FROM courses WHERE title = 'Охрана труда и техника безопасности' LIMIT 1"
    ).fetchone()
    if safety_course:
        db.execute(
            """INSERT INTO quiz_attempts
               (student_id, course_id, score, correct_answers, total_questions,
                passed, attempted_at, is_legacy)
               SELECT t.student_id, ?, t.score, NULL, NULL, t.passed,
                      t.completed_at, 1
               FROM safety_tests t
               WHERE NOT EXISTS (
                   SELECT 1 FROM quiz_attempts qa
                   WHERE qa.student_id = t.student_id AND qa.course_id = ?
                     AND qa.score = t.score AND qa.attempted_at = t.completed_at
                     AND qa.is_legacy = 1
               )""",
            (safety_course["id"], safety_course["id"]),
        )
    db.execute(
        """INSERT INTO quiz_attempts
           (student_id, course_id, score, correct_answers, total_questions,
            passed, attempted_at, is_legacy)
           SELECT cp.student_id, cp.course_id, cp.percent, NULL, NULL,
                  CASE WHEN cp.status = 'completed' THEN 1 ELSE 0 END,
                  cp.updated_at, 1
           FROM course_progress cp
           WHERE cp.percent > 0
             AND NOT EXISTS (
                 SELECT 1 FROM quiz_attempts qa
                 WHERE qa.student_id = cp.student_id AND qa.course_id = cp.course_id
             )"""
    )


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) == 10:
        digits = "7" + digits
    elif len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) != 11 or not digits.startswith("7"):
        raise ValueError("Введите номер телефона в формате +7 700 000 00 00")
    return "+" + digits


def validate_password(password: str) -> str:
    password = str(password or "")
    if len(password) < 8:
        raise ValueError("Пароль должен содержать не менее 8 символов")
    if not any(character.isalpha() for character in password) or not any(character.isdigit() for character in password):
        raise ValueError("Пароль должен содержать буквы и цифры")
    return password


def password_digest(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return digest.hex(), salt.hex()


def verify_password(password: str, expected_hash: str, salt_hex: str) -> bool:
    actual_hash, _ = password_digest(password, salt_hex)
    return hmac.compare_digest(actual_hash, expected_hash)


def temporary_password() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    return "Tmp" + "".join(secrets.choice(alphabet) for _ in range(9)) + "7"


def create_user(
    db: sqlite3.Connection,
    phone: str,
    password: str,
    role: str,
    full_name: str,
    student_id: int | None = None,
    mentor_id: int | None = None,
    must_change_password: bool = True,
) -> int:
    phone = normalize_phone(phone)
    password = validate_password(password)
    password_hash, password_salt = password_digest(password)
    try:
        cursor = db.execute(
            """INSERT INTO users
               (phone, password_hash, password_salt, role, full_name,
                student_id, mentor_id, must_change_password)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                phone, password_hash, password_salt, role, full_name.strip(),
                student_id, mentor_id, int(must_change_password),
            ),
        )
    except sqlite3.IntegrityError as exc:
        raise ValueError("Этот номер телефона уже используется другой учётной записью") from exc
    return int(cursor.lastrowid)


def sync_profile_account(
    db: sqlite3.Connection,
    role: str,
    profile_id: int,
    full_name: str,
    phone: str,
    is_active: bool = True,
) -> None:
    id_column = "student_id" if role == "student" else "mentor_id"
    account = db.execute(
        f"SELECT id, phone FROM users WHERE {id_column} = ?",
        (profile_id,),
    ).fetchone()
    phone = str(phone or "").strip()
    if not phone:
        if account:
            db.execute(
                "UPDATE users SET full_name = ?, is_active = 0 WHERE id = ?",
                (full_name.strip(), account["id"]),
            )
        return
    normalized_phone = normalize_phone(phone)
    if account:
        try:
            db.execute(
                "UPDATE users SET phone = ?, full_name = ?, is_active = ? WHERE id = ?",
                (normalized_phone, full_name.strip(), int(is_active), account["id"]),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Этот номер телефона уже используется другой учётной записью") from exc
        return
    create_user(
        db,
        normalized_phone,
        os.environ.get("LMS_INITIAL_PASSWORD", DEFAULT_INITIAL_PASSWORD),
        role,
        full_name,
        student_id=profile_id if role == "student" else None,
        mentor_id=profile_id if role == "mentor" else None,
    )


def ensure_user_accounts(db: sqlite3.Connection) -> None:
    admin_phone = os.environ.get("LMS_ADMIN_PHONE", DEFAULT_ADMIN_PHONE)
    normalized_admin_phone = normalize_phone(admin_phone)
    admin = db.execute(
        "SELECT id FROM users WHERE role = 'admin' AND mentor_id IS NULL LIMIT 1"
    ).fetchone()
    if not admin:
        create_user(
            db,
            normalized_admin_phone,
            os.environ.get("LMS_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD),
            "admin",
            "Учебный центр",
        )
    for mentor in db.execute(
        "SELECT id, full_name, phone, is_archived FROM mentors"
    ).fetchall():
        sync_profile_account(
            db, "mentor", mentor["id"], mentor["full_name"], mentor["phone"],
            not bool(mentor["is_archived"]),
        )
    for student in db.execute(
        "SELECT id, full_name, phone, is_archived FROM students"
    ).fetchall():
        sync_profile_account(
            db, "student", student["id"], student["full_name"], student["phone"],
            not bool(student["is_archived"]),
        )


def public_user(user: sqlite3.Row | dict) -> dict:
    can_delete = bool(user["can_delete"])
    return {
        "id": user["id"],
        "phone": user["phone"],
        "role": user["role"],
        "full_name": user["full_name"],
        "student_id": user["student_id"],
        "mentor_id": user["mentor_id"],
        "must_change_password": bool(user["must_change_password"]),
        "can_delete": can_delete,
        "account_title": "Руководитель" if user["role"] == "admin" and not can_delete else None,
    }


def account_list(db: sqlite3.Connection) -> list[dict]:
    accounts = rows(
        db.execute(
            """SELECT id, phone, role, full_name, student_id, mentor_id,
                      must_change_password, is_active, created_at, last_login_at,
                      can_delete
               FROM users ORDER BY
               CASE role WHEN 'admin' THEN 0 WHEN 'mentor' THEN 1 ELSE 2 END,
               full_name"""
        )
    )
    for account in accounts:
        account["account_title"] = (
            "Руководитель"
            if account["role"] == "admin" and not bool(account["can_delete"])
            else None
        )
    return accounts


def ensure_safety_quiz_questions(db: sqlite3.Connection) -> None:
    """One-time migration that expands the built-in safety test to 15 questions."""
    migration_key = "safety_quiz_15_v1"
    if db.execute("SELECT 1 FROM app_meta WHERE key = ?", (migration_key,)).fetchone():
        return
    course = db.execute("SELECT id FROM courses WHERE id = 2").fetchone()
    if not course:
        return
    course_id = course["id"]
    existing_questions = {
        row["question"]
        for row in db.execute(
            "SELECT question FROM quiz_questions WHERE course_id = ?",
            (course_id,),
        )
    }
    question_count = len(existing_questions)
    for question, options, correct_index in SAFETY_QUIZ_QUESTIONS:
        if question_count >= 15:
            break
        if question in existing_questions:
            continue
        db.execute(
            """INSERT INTO quiz_questions
               (course_id, question, options_json, correct_index)
               VALUES (?, ?, ?, ?)""",
            (course_id, question, json.dumps(options, ensure_ascii=False), correct_index),
        )
        existing_questions.add(question)
        question_count += 1
    db.execute(
        "INSERT INTO app_meta (key, value) VALUES (?, ?)",
        (migration_key, str(question_count)),
    )


def seed_database(db: sqlite3.Connection) -> None:
    today = current_date()
    student_roster = [
        ("Костенко Максим Евгеньевич", "2006-12-14", "Кызылжарский район, с. Конд…", "+7 705 392 77 75", "Механизация сельского хозяйства", 4, "Поток 1", "2026-09-01", "2026-10-23", "CT Agro"),
        ("Куандықов Тимур Русланович", "2007-06-05", "г. Петропавловск, ул. Копай, 50", "+7 705 137 61 68", "Механизация сельского хозяйства", 4, "Поток 1", "2026-09-01", "2026-10-23", "CT Agro"),
        ("Дурников Илья Сергеевич", "2007-01-14", "г. Петропавловск, ул. Уалихано…", "+7 705 387 68 50", "Механизация сельского хозяйства", 4, "Поток 1", "2026-09-01", "2026-10-23", "CT Agro"),
        ("Сафонов Сергей Витальевич", "2007-04-03", "г. Петропавловск, ул. Интернац…", "+7 776 303 04 07", "Механизация сельского хозяйства", 4, "Поток 1", "2026-09-01", "2026-10-23", "CT Agro"),
        ("Усачев Дмитрий Юрьевич", "2007-07-22", "г. Петропавловск, ул. Сафроно…", "+7 705 373 49 43", "Механизация сельского хозяйства", 4, "Поток 1", "2026-09-01", "2026-10-23", "CT Agro"),
        ("Ашим Тимурлан Айдарханулы", "2007-09-13", "г. Петропавловск, ул. Студенче…", "+7 777 894 06 18", "Механизация сельского хозяйства", 4, "Поток 1", "2026-09-01", "2026-10-23", "CT Agro"),
        ("Девяткин Александр Сергеевич", "2007-04-28", "Кызылжарский район, с. Больш…", "+7 777 097 60 03", "Механизация сельского хозяйства", 4, "Поток 1", "2026-09-01", "2026-10-23", "CT Agro"),
        ("Дмитриев Илья Александрович", "2007-11-20", "г. Петропавловск, ул. Советска…", "+7 700 958 03 73", "Механизация сельского хозяйства", 4, "Поток 1", "2026-09-01", "2026-10-23", "CT Agro"),
        ("Исаенко Матвей Витальевич", "2008-06-02", "г. Петропавловск, ул. Мусрепова, 33", "+7 707 140 31 39", "Профессиональное обучение", 3, "Поток 2", "2026-09-01", "2026-10-23", "ТОО Reimann, CT Assembly"),
        ("Копылов Даниил Михайлович", "2008-08-11", "район Шал акына, г. Сергеевка, К…", "+7 705 192 51 09", "Профессиональное обучение", 3, "Поток 2", "2026-09-01", "2026-10-23", "ТОО Reimann, CT Assembly"),
        ("Лупенко Максим Иванович", "2008-11-17", "Жамбылский район, с. Святодух…", "+7 705 648 96 42", "Профессиональное обучение", 3, "Поток 2", "2026-09-01", "2026-10-23", "ТОО Reimann, CT Assembly"),
        ("Льгоцкий Алик Хасанович", "2008-02-06", "Кызылжарский район, с. Берёзов…", "+7 708 607 70 28", "Профессиональное обучение", 3, "Поток 2", "2026-09-01", "2026-10-23", "ТОО Reimann, CT Assembly"),
        ("Попов Илья Евгеньевич", "2008-01-01", "с. Прибрежное, ул. Советская, 49, …", "+7 700 087 27 23", "Профессиональное обучение", 3, "Поток 2", "2026-09-01", "2026-10-23", "ТОО Reimann, CT Assembly"),
        ("Мезгов Кирилл", "2008-07-10", "Кызылжарский район, с. Асаново", "+7 777 115 90 06", "Профессиональное обучение", 3, "Поток 2", "2026-09-01", "2026-10-23", "ТОО Reimann, CT Assembly"),
        ("Рукабер Валерий Владимирович", "2010-03-04", "Кызылжарский район, с. Асаново", "+7 705 216 03 29", "Механизация сельского хозяйства", 2, "Поток 3", "2026-11-02", "2026-12-25", "CT Assembly"),
        ("Верещагин Артем Евгеньевич", "2009-11-21", "район Шал акына, с. Акан-барак, …", "+7 705 960 85 33", "Механизация сельского хозяйства", 2, "Поток 3", "2026-11-02", "2026-12-25", "CT Assembly"),
        ("Сайлау Әділет Мұратұлы", "2010-08-05", "Есильский район, с. Орнек, ул. Ко…", "+7 705 545 62 46", "Механизация сельского хозяйства", 2, "Поток 3", "2026-11-02", "2026-12-25", "CT Assembly"),
        ("Федянин Никита Андреевич", "2009-06-07", "г. Петропавловск, ул. Восточна…", "+7 771 620 56 33", "Механизация сельского хозяйства", 2, "Поток 3", "2026-11-02", "2026-12-25", "CT Assembly"),
        ("Орынбасар Рустам Маратұлы", "2009-07-03", "Кызылжарский район, с. Соколов…", "+7 776 776 16 51", "Механизация сельского хозяйства", 2, "Поток 3", "2026-11-02", "2026-12-25", "CT Assembly"),
        ("Метелев Роман Васильевич", "2010-04-20", "г. Петропавловск, ул. Студенче…", "+7 775 835 79 95", "Механизация сельского хозяйства", 2, "Поток 3", "2026-11-02", "2026-12-25", "CT Assembly"),
        ("Гарбузов Артур Сергеевич", "2010-02-11", "г. Петропавловск, ул. Шмидта, …", "+7 747 929 17 44", "Механизация сельского хозяйства", 2, "Поток 3", "2026-11-02", "2026-12-25", "CT Assembly"),
        ("Галицкий Радион Иванович", "2009-09-16", "район Шал акына, с. Акан-барак, …", "+7 705 294 11 93", "Механизация сельского хозяйства", 2, "Поток 3", "2026-11-02", "2026-12-25", "CT Assembly"),
        ("Полын Анна Александровна", "2010-01-07", "Кызылжарский район, с. Архангел…", "+7 747 810 39 70", "Механизация сельского хозяйства", 2, "Поток 3", "2026-11-02", "2026-12-25", "CT Assembly"),
    ]
    colors = ["#D71920", "#3F474D", "#6F8F38", "#59636B", "#B20F16", "#2C3237"]
    student_rows = []
    for index, (name, birth_date, address, phone, specialty, course, stream, start_date, end_date, company) in enumerate(student_roster):
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        status = "На практике" if start <= today <= end else ("Ожидает начала практики" if today < start else "Завершил ротацию")
        if "Петропавловск" in address:
            base_city = "Петропавловск"
        elif "Шал акына" in address:
            base_city = "район Шал акына"
        elif "Жамбылский" in address:
            base_city = "Жамбылский район"
        elif "Есильский" in address:
            base_city = "Есильский район"
        else:
            base_city = "Кызылжарский район"
        student_rows.append((name, "Не указано", specialty, course, stream, base_city, status, None, colors[index % len(colors)], phone, birth_date, address, ""))
    db.executemany(
        """INSERT INTO students
        (full_name, institution, specialty, course, stream, base_city, status, mentor_id,
         avatar_color, phone, birth_date, address, additional_info)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        student_rows,
    )

    skills = [
        ("TB-01", "Вводный инструктаж по охране труда", "Теория", "Безопасность", 1, "Знает основные риски и правила поведения на предприятии."),
        ("TB-02", "Безопасная работа с оборудованием", "Практика", "Безопасность", 1, "Применяет СИЗ и выполняет проверку рабочего места."),
        ("DR-01", "Чтение технических чертежей", "Теория", "Техническая подготовка", 1, "Читает обозначения, размеры и допуски."),
        ("QM-01", "Контроль геометрических параметров", "Практика", "Контроль качества", 1, "Выполняет измерения штангенциркулем и рейсмасом."),
        ("WL-01", "Подготовка деталей к сварке", "Практика", "Сварочное дело", 1, "Подготавливает кромки и рабочее место."),
        ("WL-02", "Ручная дуговая сварка", "Практика", "Сварочное дело", 1, "Выполняет сварной шов в нижнем положении."),
        ("AS-01", "Сборка узла по техпроцессу", "Практика", "Сборочное производство", 1, "Собирает узел с соблюдением последовательности операций."),
        ("5S-01", "Стандарты 5S на рабочем месте", "Теория", "Производственная культура", 1, "Поддерживает сортировку, порядок и стандартизацию."),
        ("QC-01", "Выявление и регистрация дефектов", "Практика", "Контроль качества", 1, "Классифицирует дефект и оформляет запись."),
        ("CO-01", "Работа в производственной команде", "Практика", "Soft skills", 0, "Принимает обратную связь и сообщает о проблемах."),
    ]
    db.executemany(
        "INSERT INTO skills (code, title, category, module, required, description) VALUES (?, ?, ?, ?, ?, ?)",
        skills,
    )

    courses = [
        ("Вводный курс CT Assembly", "Адаптация", 2, "Структура предприятия, правила внутреннего распорядка и культура производства.", 80, "#3D6FC1"),
        ("Охрана труда и техника безопасности", "Обязательный", 4, "Безопасное поведение в цеху, СИЗ, опасные зоны и действия при инциденте.", 90, "#D71920"),
        ("Чтение технических чертежей", "Теория", 8, "Обозначения, проекции, размеры, допуски и чтение сборочного чертежа.", 80, "#7656B5"),
        ("Система 5S на рабочем месте", "Производственная культура", 3, "Сортировка, самоорганизация, содержание в чистоте, стандартизация и совершенствование.", 80, "#188564"),
        ("Основы сварочного производства", "Профессиональный модуль", 12, "Подготовка деталей, режимы сварки, выполнение соединений и визуальный контроль.", 80, "#BF4054"),
    ]
    db.executemany(
        "INSERT INTO courses (title, category, duration_hours, description, pass_score, color) VALUES (?, ?, ?, ?, ?, ?)",
        courses,
    )

    db.executemany(
        "INSERT INTO quiz_questions (course_id, question, options_json, correct_index) VALUES (?, ?, ?, ?)",
        [
            (2, question, json.dumps(options, ensure_ascii=False), correct_index)
            for question, options, correct_index in SAFETY_QUIZ_QUESTIONS
        ],
    )

    course_progress_rows = [
        (student_id, course_id, 0, "not_started")
        for student_id in range(1, len(student_roster) + 1)
        for course_id in range(1, 6)
    ]
    db.executemany(
        "INSERT INTO course_progress (student_id, course_id, percent, status) VALUES (?, ?, ?, ?)",
        course_progress_rows,
    )

    progress_rows = [
        (student_id, skill_id, "not_started", None)
        for student_id in range(1, len(student_roster) + 1)
        for skill_id in range(1, 11)
    ]
    db.executemany(
        "INSERT INTO progress (student_id, skill_id, status, mentor_id) VALUES (?, ?, ?, ?)",
        progress_rows,
    )

    rotation_data = []
    for student_id, roster_item in enumerate(student_roster, 1):
        start_date, end_date, company = roster_item[7], roster_item[8], roster_item[9]
        start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
        rotation_status = "Активна" if start <= today <= end else ("Запланирована" if today < start else "Завершена")
        rotation_city = student_rows[student_id - 1][5]
        rotation_data.append((student_id, rotation_city, company, "Производственная практика", start_date, end_date, rotation_status))
    db.executemany(
        """INSERT INTO rotations
        (student_id, city, company, workshop, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        rotation_data,
    )

    db.execute(
        """INSERT INTO notifications (role, title, message, kind, dedupe_key)
        VALUES ('admin', 'Список студентов загружен', 'В LMS добавлены 23 студента и периоды их производственной практики.', 'success', 'roster-import-2026')"""
    )
    db.commit()


def rotation_status_for_period(
    start_date: date | str,
    end_date: date | str,
    as_of: date | None = None,
) -> str:
    start = date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
    end = date.fromisoformat(end_date) if isinstance(end_date, str) else end_date
    today = as_of or current_date()
    if today < start:
        return "Запланирована"
    if today > end:
        return "Завершена"
    return "Активна"


def sync_rotation_statuses(db: sqlite3.Connection, as_of: date | None = None) -> int:
    today = (as_of or current_date()).isoformat()
    cursor = db.execute(
        """UPDATE rotations SET status = CASE
           WHEN start_date > ? THEN 'Запланирована'
           WHEN end_date < ? THEN 'Завершена'
           ELSE 'Активна' END
           WHERE status != CASE
           WHEN start_date > ? THEN 'Запланирована'
           WHEN end_date < ? THEN 'Завершена'
           ELSE 'Активна' END""",
        (today, today, today, today),
    )
    db.commit()
    return cursor.rowcount


def sync_rotation_notifications(db: sqlite3.Connection) -> None:
    today_date = current_date()
    today = today_date.isoformat()
    in_five_days = (today_date + timedelta(days=5)).isoformat()
    upcoming = db.execute(
        """SELECT r.id, r.end_date, r.city, r.workshop, s.full_name
           FROM rotations r JOIN students s ON s.id = r.student_id
           WHERE r.status = 'Активна' AND s.is_archived = 0 AND r.end_date BETWEEN ? AND ?""",
        (today, in_five_days),
    ).fetchall()
    active_keys: list[str] = []
    for rotation in upcoming:
        end_date = date.fromisoformat(rotation["end_date"])
        days_left = max((end_date - today_date).days, 0)
        if days_left == 0:
            title = "Ротация завершается сегодня"
        else:
            title = (
                f"Ротация завершается через {days_left} "
                f"{plural_ru(days_left, 'день', 'дня', 'дней')}"
            )
        dedupe_key = f"rotation-{rotation['id']}-{rotation['end_date']}"
        active_keys.append(dedupe_key)
        db.execute(
            """INSERT INTO notifications
               (role, title, message, kind, dedupe_key)
               VALUES ('admin', ?, ?, 'rotation', ?)
               ON CONFLICT(dedupe_key) DO UPDATE SET
                 is_read = CASE
                   WHEN notifications.title != excluded.title THEN 0
                   ELSE notifications.is_read END,
                 title = excluded.title,
                 message = excluded.message,
                 kind = excluded.kind""",
            (
                title,
                f"{rotation['full_name']}: подготовьте следующее рабочее место после {end_date.strftime('%d.%m.%Y')}.",
                dedupe_key,
            ),
        )
    if active_keys:
        placeholders = ",".join("?" for _ in active_keys)
        db.execute(
            f"""DELETE FROM notifications
                WHERE kind = 'rotation' AND dedupe_key LIKE 'rotation-%'
                  AND dedupe_key NOT IN ({placeholders})""",
            active_keys,
        )
    else:
        db.execute(
            "DELETE FROM notifications WHERE kind = 'rotation' AND dedupe_key LIKE 'rotation-%'"
        )
    db.commit()


def get_students(db: sqlite3.Connection, archived: bool = False) -> list[dict]:
    return rows(
        db.execute(
            """SELECT s.*, m.full_name AS mentor_name, m.workshop AS mentor_workshop,
               (SELECT COUNT(*) FROM progress p WHERE p.student_id = s.id) AS skills_total,
               (SELECT COUNT(*) FROM progress p WHERE p.student_id = s.id AND p.status = 'confirmed') AS skills_confirmed,
               COALESCE((SELECT t.score FROM safety_tests t WHERE t.student_id = s.id
                         ORDER BY t.completed_at DESC, t.id DESC LIMIT 1), 0) AS safety_score,
               COALESCE((SELECT t.passed FROM safety_tests t WHERE t.student_id = s.id
                         ORDER BY t.completed_at DESC, t.id DESC LIMIT 1), 0) AS safety_passed,
               (SELECT r.id FROM rotations r WHERE r.student_id = s.id
                ORDER BY CASE r.status WHEN 'Активна' THEN 0 WHEN 'Запланирована' THEN 1 ELSE 2 END,
                         CASE WHEN r.status = 'Запланирована' THEN r.start_date END ASC,
                         r.start_date DESC LIMIT 1) AS rotation_id,
               (SELECT r.city FROM rotations r WHERE r.student_id = s.id
                ORDER BY CASE r.status WHEN 'Активна' THEN 0 WHEN 'Запланирована' THEN 1 ELSE 2 END,
                         CASE WHEN r.status = 'Запланирована' THEN r.start_date END ASC,
                         r.start_date DESC LIMIT 1) AS rotation_city,
               (SELECT r.company FROM rotations r WHERE r.student_id = s.id
                ORDER BY CASE r.status WHEN 'Активна' THEN 0 WHEN 'Запланирована' THEN 1 ELSE 2 END,
                         CASE WHEN r.status = 'Запланирована' THEN r.start_date END ASC,
                         r.start_date DESC LIMIT 1) AS rotation_company,
               (SELECT r.workshop FROM rotations r WHERE r.student_id = s.id
                ORDER BY CASE r.status WHEN 'Активна' THEN 0 WHEN 'Запланирована' THEN 1 ELSE 2 END,
                         CASE WHEN r.status = 'Запланирована' THEN r.start_date END ASC,
                         r.start_date DESC LIMIT 1) AS rotation_workshop
               FROM students s
               LEFT JOIN mentors m ON m.id = s.mentor_id
               WHERE s.is_archived = ?
               ORDER BY s.full_name"""
            , (int(archived),)
        )
    )


def get_mentors(db: sqlite3.Connection, archived: bool = False) -> list[dict]:
    return rows(
        db.execute(
            """SELECT m.*, SUM(CASE WHEN s.is_archived = 0 THEN 1 ELSE 0 END) AS students_count
               FROM mentors m LEFT JOIN students s ON s.mentor_id = m.id
               WHERE m.is_archived = ?
               GROUP BY m.id ORDER BY m.full_name""",
            (int(archived),),
        )
    )


def get_skills(db: sqlite3.Connection) -> list[dict]:
    return rows(
        db.execute(
            """SELECT sk.*,
               (SELECT COUNT(*) FROM progress p JOIN students s ON s.id = p.student_id
                WHERE p.skill_id = sk.id AND p.status = 'confirmed' AND s.is_archived = 0) AS confirmed_count,
               (SELECT ROUND(AVG(sa.score), 2) FROM skill_assessments sa
                JOIN students s ON s.id = sa.student_id
                WHERE sa.skill_id = sk.id AND s.is_archived = 0) AS average_score,
               (SELECT COUNT(*) FROM skill_assessments sa
                JOIN students s ON s.id = sa.student_id
                WHERE sa.skill_id = sk.id AND s.is_archived = 0) AS assessments_count
               FROM skills sk WHERE sk.is_active = 1
               ORDER BY sk.display_order, sk.id"""
        )
    )


def get_skill_matrix(db: sqlite3.Connection, allowed_student_ids: set[int]) -> list[dict]:
    """Current competency level per student, with period and evaluating mentor."""
    if not allowed_student_ids:
        return []
    placeholders = ",".join("?" for _ in allowed_student_ids)
    return rows(
        db.execute(
            f"""SELECT s.id AS student_id, s.full_name AS student_name, s.stream,
                       sk.id AS skill_id, sk.code, sk.title, sk.category, sk.module,
                       COALESCE(sa.score, p.score) AS score,
                       p.status,
                       COALESCE(sa.assessed_at, p.updated_at) AS assessed_at,
                       COALESCE(b.mentor_name, m.full_name, '') AS mentor_name,
                       COALESCE(NULLIF(b.enterprise, ''), m.enterprise, '') AS enterprise,
                       (SELECT r.start_date FROM rotations r
                        WHERE r.student_id = s.id
                          AND substr(COALESCE(sa.assessed_at, p.updated_at), 1, 10)
                              BETWEEN r.start_date AND r.end_date
                        ORDER BY r.start_date DESC LIMIT 1) AS period_start,
                       (SELECT r.end_date FROM rotations r
                        WHERE r.student_id = s.id
                          AND substr(COALESCE(sa.assessed_at, p.updated_at), 1, 10)
                              BETWEEN r.start_date AND r.end_date
                        ORDER BY r.start_date DESC LIMIT 1) AS period_end
                FROM students s
                JOIN progress p ON p.student_id = s.id
                JOIN skills sk ON sk.id = p.skill_id AND sk.is_active = 1
                LEFT JOIN skill_assessments sa ON sa.id = (
                    SELECT sa2.id FROM skill_assessments sa2
                    WHERE sa2.student_id = s.id AND sa2.skill_id = sk.id
                    ORDER BY sa2.assessed_at DESC, sa2.id DESC LIMIT 1
                )
                LEFT JOIN skill_assessment_batches b ON b.id = sa.batch_id
                LEFT JOIN mentors m ON m.id = p.mentor_id
                WHERE s.is_archived = 0 AND s.id IN ({placeholders})
                ORDER BY CASE s.stream
                           WHEN 'Поток 1' THEN 1 WHEN 'Поток 2' THEN 2
                           WHEN 'Поток 3' THEN 3 ELSE 99 END,
                         s.stream, s.full_name, sk.display_order, sk.id""",
            tuple(sorted(allowed_student_ids)),
        )
    )


def get_rotations(db: sqlite3.Connection) -> list[dict]:
    return rows(
        db.execute(
            """SELECT r.*, s.full_name AS student_name, s.avatar_color
               FROM rotations r JOIN students s ON s.id = r.student_id
               WHERE s.is_archived = 0
               ORDER BY r.start_date"""
        )
    )


def get_attendance(
    db: sqlite3.Connection,
    attendance_date: str | None = None,
    student_id: int | None = None,
) -> list[dict]:
    conditions = []
    params: list[str | int] = []
    if attendance_date:
        conditions.append("a.attendance_date = ?")
        params.append(attendance_date)
    if student_id:
        conditions.append("a.student_id = ?")
        params.append(student_id)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    return rows(
        db.execute(
            f"""SELECT a.*, s.full_name AS student_name, s.stream, s.specialty,
                m.full_name AS marked_by_name
                FROM attendance a
                JOIN students s ON s.id = a.student_id
                LEFT JOIN mentors m ON m.id = a.marked_by_mentor_id
                {where}
                ORDER BY a.attendance_date DESC, s.full_name""",
            params,
        )
    )


def get_evaluations(db: sqlite3.Connection, student_id: int | None = None) -> list[dict]:
    where = "WHERE e.student_id = ?" if student_id else ""
    params = (student_id,) if student_id else ()
    return rows(
        db.execute(
            f"""SELECT e.*, s.full_name AS student_name, s.avatar_color,
                s.stream, s.specialty,
                m.full_name AS evaluator_name, r.company AS rotation_company,
                r.workshop AS rotation_workshop,
                c.title AS course_title, c.duration_hours AS course_hours,
                c.category AS course_category, c.description AS course_description,
                c.pass_score AS course_pass_score
                FROM evaluations e
                JOIN students s ON s.id = e.student_id
                LEFT JOIN mentors m ON m.id = e.evaluator_id
                LEFT JOIN rotations r ON r.id = e.rotation_id
                LEFT JOIN courses c ON c.id = e.course_id
                {where}
                ORDER BY e.evaluated_at DESC, e.id DESC""",
            params,
        )
    )


def get_student_profile(db: sqlite3.Connection, student_id: int) -> dict:
    student = db.execute(
        """SELECT s.*, m.full_name AS mentor_name, m.workshop AS mentor_workshop,
           (SELECT COUNT(*) FROM progress p WHERE p.student_id = s.id) AS skills_total,
           (SELECT COUNT(*) FROM progress p WHERE p.student_id = s.id AND p.status = 'confirmed') AS skills_confirmed,
           COALESCE((SELECT t.score FROM safety_tests t WHERE t.student_id = s.id
                     ORDER BY t.completed_at DESC, t.id DESC LIMIT 1), 0) AS safety_score,
           COALESCE((SELECT t.passed FROM safety_tests t WHERE t.student_id = s.id
                     ORDER BY t.completed_at DESC, t.id DESC LIMIT 1), 0) AS safety_passed
           FROM students s LEFT JOIN mentors m ON m.id = s.mentor_id WHERE s.id = ?""",
        (student_id,),
    ).fetchone()
    if not student:
        raise ValueError("Студент не найден")
    rotations = rows(
        db.execute(
            "SELECT * FROM rotations WHERE student_id = ? ORDER BY start_date DESC",
            (student_id,),
        )
    )
    progress = rows(
        db.execute(
            """SELECT p.*, sk.code, sk.title, sk.category, sk.module, sk.required,
                      sk.description, sk.display_order
               FROM progress p JOIN skills sk ON sk.id = p.skill_id
               WHERE p.student_id = ? AND sk.is_active = 1
               ORDER BY sk.display_order, sk.id""",
            (student_id,),
        )
    )
    attendance = get_attendance(db, student_id=student_id)[:90]
    evaluations = get_evaluations(db, student_id)
    quiz_attempts = rows(
        db.execute(
            """SELECT qa.*, c.title AS course_title, c.pass_score
               FROM quiz_attempts qa
               JOIN courses c ON c.id = qa.course_id
               WHERE qa.student_id = ?
               ORDER BY qa.attempted_at DESC, qa.id DESC""",
            (student_id,),
        )
    )
    attempt_totals: dict[int, int] = {}
    for attempt in reversed(quiz_attempts):
        course_id = int(attempt["course_id"])
        attempt_totals[course_id] = attempt_totals.get(course_id, 0) + 1
        attempt["attempt_number"] = attempt_totals[course_id]
    skill_batches = rows(
        db.execute(
            """SELECT b.*,
               (SELECT COUNT(*) FROM skill_assessments sa WHERE sa.batch_id = b.id) AS skills_count
               FROM skill_assessment_batches b
               WHERE b.student_id = ?
               ORDER BY b.assessed_at DESC, b.id DESC""",
            (student_id,),
        )
    )
    return {
        "student": dict(student),
        "rotations": rotations,
        "progress": progress,
        "attendance": attendance,
        "evaluations": evaluations,
        "quiz_attempts": quiz_attempts,
        "skill_assessment_batches": skill_batches,
    }


def get_courses(
    db: sqlite3.Connection,
    student_id: int | None = None,
    archived: bool = False,
) -> list[dict]:
    if student_id:
        return rows(
            db.execute(
                """SELECT c.*, COALESCE(cp.percent, 0) AS percent,
                   COALESCE(cp.status, 'not_started') AS status,
                   (SELECT COUNT(*) FROM quiz_questions q WHERE q.course_id = c.id) AS questions_count
                   FROM courses c LEFT JOIN course_progress cp
                   ON cp.course_id = c.id AND cp.student_id = ?
                   WHERE c.is_archived = ? ORDER BY c.id""",
                (student_id, int(archived)),
            )
        )
    return rows(
        db.execute(
            """SELECT c.*,
               ROUND(COALESCE(AVG(cp.percent), 0)) AS percent,
               SUM(CASE WHEN cp.status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
               COUNT(cp.id) AS assigned_count,
               (SELECT COUNT(*) FROM quiz_questions q WHERE q.course_id = c.id) AS questions_count
               FROM courses c LEFT JOIN course_progress cp ON cp.course_id = c.id
               AND cp.student_id IN (SELECT id FROM students WHERE is_archived = 0)
               WHERE c.is_archived = ?
               GROUP BY c.id ORDER BY c.id""",
            (int(archived),),
        )
    )


def get_dashboard(db: sqlite3.Connection) -> dict:
    students = get_students(db)
    active_students = sum(1 for student in students if student["status"] == "На практике")
    avg_progress = round(
        sum((student["skills_confirmed"] or 0) / max(student["skills_total"] or 1, 1) for student in students)
        / max(len(students), 1)
        * 100
    )
    next_rotation = db.execute(
        """SELECT start_date, COUNT(*) AS students_count
           FROM rotations
           WHERE status = 'Запланирована'
           GROUP BY start_date
           ORDER BY start_date
           LIMIT 1"""
    ).fetchone()
    next_rotation_days = None
    if next_rotation:
        next_rotation_days = (date.fromisoformat(next_rotation["start_date"]) - current_date()).days
    return {
        "as_of_date": current_date().isoformat(),
        "stats": {
            "students": len(students),
            "active_students": active_students,
            "mentors": db.execute("SELECT COUNT(*) AS n FROM mentors WHERE is_archived = 0 AND can_mentor = 1").fetchone()["n"],
            "supervisors": db.execute("SELECT COUNT(*) AS n FROM mentors WHERE is_archived = 0 AND role_type = 'supervisor'").fetchone()["n"],
            "active_rotations": db.execute("SELECT COUNT(*) AS n FROM rotations WHERE status = 'Активна'").fetchone()["n"],
            "avg_progress": avg_progress,
            "next_rotation_date": next_rotation["start_date"] if next_rotation else None,
            "next_rotation_days": next_rotation_days,
            "next_rotation_students": next_rotation["students_count"] if next_rotation else 0,
        },
        "students": students,
        "rotations": get_rotations(db),
        "notifications": rows(db.execute("SELECT * FROM notifications ORDER BY is_read, created_at DESC LIMIT 10")),
    }


def permitted_student_ids(db: sqlite3.Connection, user: dict) -> set[int]:
    if user["role"] == "admin":
        return {row["id"] for row in db.execute("SELECT id FROM students")}
    if user["role"] == "mentor":
        return {
            row["id"]
            for row in db.execute(
                "SELECT id FROM students WHERE mentor_id = ? AND is_archived = 0",
                (user["mentor_id"],),
            )
        }
    return {int(user["student_id"])} if user.get("student_id") else set()


def ensure_student_access(db: sqlite3.Connection, user: dict, student_id: int) -> None:
    if int(student_id) not in permitted_student_ids(db, user):
        raise PermissionError("Нет доступа к данным этого студента")


def scoped_notifications(db: sqlite3.Connection, user: dict) -> list[dict]:
    if user["role"] == "admin":
        return rows(
            db.execute(
                "SELECT * FROM notifications WHERE role = 'admin' ORDER BY is_read, created_at DESC LIMIT 10"
            )
        )
    recipient_id = user["mentor_id"] if user["role"] == "mentor" else user["student_id"]
    return rows(
        db.execute(
            """SELECT * FROM notifications
               WHERE role = ? AND (recipient_id = ? OR recipient_id IS NULL)
               ORDER BY is_read, created_at DESC LIMIT 10""",
            (user["role"], recipient_id),
        )
    )


def scoped_dashboard(db: sqlite3.Connection, user: dict) -> dict:
    dashboard = get_dashboard(db)
    if user["role"] == "admin":
        dashboard["notifications"] = scoped_notifications(db, user)
        return dashboard
    allowed = permitted_student_ids(db, user)
    dashboard["students"] = [item for item in dashboard["students"] if item["id"] in allowed]
    dashboard["rotations"] = [item for item in dashboard["rotations"] if item["student_id"] in allowed]
    dashboard["notifications"] = scoped_notifications(db, user)
    students = dashboard["students"]
    dashboard["stats"]["students"] = len(students)
    dashboard["stats"]["active_students"] = sum(item["status"] == "На практике" for item in students)
    dashboard["stats"]["active_rotations"] = sum(item["status"] == "Активна" for item in dashboard["rotations"])
    dashboard["stats"]["mentors"] = 1 if user["role"] == "mentor" else 0
    dashboard["stats"]["avg_progress"] = round(
        sum((item["skills_confirmed"] or 0) / max(item["skills_total"] or 1, 1) for item in students)
        / max(len(students), 1)
        * 100
    )
    return dashboard


def scoped_bootstrap(db: sqlite3.Connection, user: dict) -> dict:
    dashboard = scoped_dashboard(db, user)
    if user["role"] == "admin":
        mentors = get_mentors(db)
        archived_students = get_students(db, True)
        archived_mentors = get_mentors(db, True)
        courses = get_courses(db)
        archived_courses = get_courses(db, archived=True)
    elif user["role"] == "mentor":
        mentors = [item for item in get_mentors(db) if item["id"] == user["mentor_id"]]
        archived_students = []
        archived_mentors = []
        courses = get_courses(db)
        archived_courses = []
    else:
        student = dashboard["students"][0] if dashboard["students"] else None
        mentor_id = student["mentor_id"] if student else None
        mentors = [item for item in get_mentors(db) if item["id"] == mentor_id]
        archived_students = []
        archived_mentors = []
        courses = get_courses(db, user["student_id"])
        archived_courses = []
    return {
        "session": public_user(user),
        "dashboard": dashboard,
        "mentors": mentors,
        "archived_students": archived_students,
        "archived_mentors": archived_mentors,
        "skills": get_skills(db),
        "courses": courses,
        "archived_courses": archived_courses,
    }


def get_payload(path: str, query: dict[str, list[str]], user: dict) -> tuple[dict | list, int]:
    with db_connect() as db:
        sync_rotation_statuses(db)
        sync_rotation_notifications(db)
        if path == "/api/health":
            return {"ok": True, "service": "CT Assembly Learning Hub", "version": APP_VERSION, "date": current_date().isoformat()}, HTTPStatus.OK
        if path == "/api/dashboard":
            return scoped_dashboard(db, user), HTTPStatus.OK
        if path == "/api/students":
            result = get_students(db, query.get("archived", ["0"])[0] == "1")
            allowed = permitted_student_ids(db, user)
            return [item for item in result if item["id"] in allowed], HTTPStatus.OK
        if path == "/api/mentors":
            result = get_mentors(db, query.get("archived", ["0"])[0] == "1")
            if user["role"] == "admin":
                return result, HTTPStatus.OK
            mentor_id = user["mentor_id"]
            if user["role"] == "student" and user["student_id"]:
                student = db.execute("SELECT mentor_id FROM students WHERE id = ?", (user["student_id"],)).fetchone()
                mentor_id = student["mentor_id"] if student else None
            return [item for item in result if item["id"] == mentor_id], HTTPStatus.OK
        if path == "/api/skills":
            return get_skills(db), HTTPStatus.OK
        if path == "/api/skill-matrix":
            return get_skill_matrix(db, permitted_student_ids(db, user)), HTTPStatus.OK
        if path == "/api/rotations":
            allowed = permitted_student_ids(db, user)
            return [item for item in get_rotations(db) if item["student_id"] in allowed], HTTPStatus.OK
        if path == "/api/attendance":
            attendance_date = query.get("date", [None])[0]
            student_id = int(query["student_id"][0]) if query.get("student_id") else None
            if student_id:
                ensure_student_access(db, user, student_id)
            allowed = permitted_student_ids(db, user)
            result = get_attendance(db, attendance_date, student_id)
            return [item for item in result if item["student_id"] in allowed], HTTPStatus.OK
        if path == "/api/evaluations":
            student_id = int(query["student_id"][0]) if query.get("student_id") else None
            if student_id:
                ensure_student_access(db, user, student_id)
            allowed = permitted_student_ids(db, user)
            result = get_evaluations(db, student_id)
            return [item for item in result if item["student_id"] in allowed], HTTPStatus.OK
        if path == "/api/student-profile":
            student_id = int(query.get("student_id", ["0"])[0])
            ensure_student_access(db, user, student_id)
            return get_student_profile(db, student_id), HTTPStatus.OK
        if path == "/api/courses":
            student_id = int(query["student_id"][0]) if query.get("student_id") else None
            archived = query.get("archived", ["0"])[0] == "1"
            if user["role"] == "student":
                student_id = int(user["student_id"])
                archived = False
            elif student_id:
                ensure_student_access(db, user, student_id)
            return get_courses(db, student_id, archived), HTTPStatus.OK
        if path == "/api/quiz":
            course_id = int(query.get("course_id", ["0"])[0])
            course = db.execute(
                "SELECT id, title, pass_score FROM courses WHERE id = ? AND is_archived = 0",
                (course_id,),
            ).fetchone()
            if not course:
                raise ValueError("Курс не найден")
            questions = rows(db.execute("SELECT id, question, options_json FROM quiz_questions WHERE course_id = ? ORDER BY id", (course_id,)))
            for question in questions:
                question["options"] = json.loads(question.pop("options_json"))
            return {"course": dict(course), "questions": questions}, HTTPStatus.OK
        if path == "/api/course-questions":
            course_id = int(query.get("course_id", ["0"])[0])
            course = db.execute(
                """SELECT id, title, pass_score FROM courses
                   WHERE id = ? AND is_archived = 0""",
                (course_id,),
            ).fetchone()
            if not course:
                raise ValueError("Курс не найден")
            questions = rows(
                db.execute(
                    """SELECT id, course_id, question, options_json, correct_index
                       FROM quiz_questions WHERE course_id = ? ORDER BY id""",
                    (course_id,),
                )
            )
            for question in questions:
                question["options"] = json.loads(question.pop("options_json"))
            return {"course": dict(course), "questions": questions}, HTTPStatus.OK
        if path == "/api/notifications":
            return scoped_notifications(db, user), HTTPStatus.OK
        if path == "/api/progress":
            student_id = int(query.get("student_id", [str(user.get("student_id") or 0)])[0])
            ensure_student_access(db, user, student_id)
            data = rows(
                db.execute(
                    """SELECT p.*, sk.code, sk.title, sk.category, sk.module, sk.required,
                              sk.description, sk.display_order
                       FROM progress p JOIN skills sk ON sk.id = p.skill_id
                       WHERE p.student_id = ? AND sk.is_active = 1
                       ORDER BY sk.display_order, sk.id""",
                    (student_id,),
                )
            )
            return data, HTTPStatus.OK
        if path == "/api/bootstrap":
            return scoped_bootstrap(db, user), HTTPStatus.OK
        if path == "/api/users":
            return account_list(db), HTTPStatus.OK
    return {"error": "Маршрут не найден"}, HTTPStatus.NOT_FOUND


def validate_required(data: dict, fields: list[str]) -> None:
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValueError("Заполните обязательные поля: " + ", ".join(missing))


def normalize_person_name(value: str) -> str:
    translation = str.maketrans(
        {
            "ё": "е", "ә": "а", "ғ": "г", "қ": "к", "ң": "н",
            "ө": "о", "ұ": "у", "ү": "у", "һ": "х", "і": "и",
        }
    )
    text = str(value or "").strip().casefold().translate(translation)
    return " ".join(re.sub(r"[^a-zа-я0-9]+", " ", text).split())


def normalize_stream_number(value: object) -> int | None:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group()) if match else None


def normalize_assessment_timestamp(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return datetime.now(BUSINESS_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = None
        for pattern in ("%d.%m.%Y %H:%M", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(text, pattern)
                break
            except ValueError:
                continue
        if parsed is None:
            raise ValueError("Некорректная дата анкеты")
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def status_from_skill_score(score: int) -> str:
    if score >= 4:
        return "confirmed"
    if score >= 2:
        return "in_progress"
    return "not_started"


def import_dual_survey(data: dict) -> dict:
    validate_required(data, ["survey_id", "student_name", "mentor_name", "answers"])
    answers = data["answers"]
    if not isinstance(answers, list) or len(answers) != 15:
        raise ValueError("Анкета должна содержать 15 оценок")
    try:
        answers = [int(score) for score in answers]
    except (TypeError, ValueError) as exc:
        raise ValueError("Оценки анкеты должны быть числами от 1 до 5") from exc
    if any(score < 1 or score > 5 for score in answers):
        raise ValueError("Оценки анкеты должны быть от 1 до 5")

    source = str(data.get("source") or "dual-survey-bot").strip()[:80]
    external_id = str(data["survey_id"]).strip()[:100]
    student_key = normalize_person_name(data["student_name"])
    stream_number = normalize_stream_number(data.get("stream"))
    assessed_at = normalize_assessment_timestamp(data.get("survey_date"))
    mentor_name = str(data["mentor_name"]).strip()[:200]
    enterprise = str(data.get("enterprise") or "").strip()[:200]

    with db_connect() as db:
        existing = db.execute(
            "SELECT id, student_id FROM skill_assessment_batches WHERE source = ? AND external_id = ?",
            (source, external_id),
        ).fetchone()
        if existing:
            student = db.execute(
                "SELECT full_name FROM students WHERE id = ?", (existing["student_id"],)
            ).fetchone()
            return {
                "ok": True, "imported": False, "duplicate": True,
                "batch_id": existing["id"],
                "student_id": existing["student_id"],
                "student_name": student["full_name"] if student else data["student_name"],
            }

        candidates = db.execute(
            "SELECT id, full_name, stream FROM students WHERE is_archived = 0"
        ).fetchall()
        matches = [item for item in candidates if normalize_person_name(item["full_name"]) == student_key]
        if stream_number is not None:
            stream_matches = [
                item for item in matches
                if normalize_stream_number(item["stream"]) == stream_number
            ]
            if stream_matches:
                matches = stream_matches
        if not matches:
            raise ValueError(
                f"Студент «{data['student_name']}» не найден в LMS. Проверьте ФИО и поток."
            )
        if len(matches) > 1:
            raise ValueError("Найдено несколько студентов с одинаковым ФИО — укажите поток")
        student = matches[0]

        mentor = next(
            (
                item for item in db.execute(
                    "SELECT id, full_name FROM mentors WHERE is_archived = 0"
                ).fetchall()
                if normalize_person_name(item["full_name"]) == normalize_person_name(mentor_name)
            ),
            None,
        )
        average_score = round(sum(answers) / len(answers), 2)
        batch_cursor = db.execute(
            """INSERT INTO skill_assessment_batches
               (student_id, source, external_id, mentor_name, mentor_external_id,
                enterprise, assessed_at, average_score, best, improve, recommendation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                student["id"], source, external_id, mentor_name,
                str(data.get("mentor_external_id") or "")[:100], enterprise,
                assessed_at, average_score, str(data.get("best") or "").strip(),
                str(data.get("improve") or "").strip(),
                str(data.get("recommendation") or "").strip(),
            ),
        )
        batch_id = int(batch_cursor.lastrowid)
        imported = 0
        for question_index, score in enumerate(answers, 1):
            skill = db.execute(
                """SELECT id FROM skills
                   WHERE bot_question_index = ? AND is_active = 1""",
                (question_index,),
            ).fetchone()
            if not skill:
                raise ValueError(f"Для вопроса {question_index} не настроен навык LMS")
            status = status_from_skill_score(score)
            db.execute(
                """INSERT INTO skill_assessments
                   (batch_id, student_id, skill_id, score, status, assessed_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (batch_id, student["id"], skill["id"], score, status, assessed_at),
            )
            note = f"Telegram-анкета: {score}/5 · {mentor_name}"
            if enterprise:
                note += f" · {enterprise}"
            db.execute(
                """INSERT INTO progress
                   (student_id, skill_id, status, score, note, mentor_id, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(student_id, skill_id) DO UPDATE SET
                     status = excluded.status,
                     score = excluded.score,
                     note = excluded.note,
                     mentor_id = COALESCE(excluded.mentor_id, progress.mentor_id),
                     updated_at = excluded.updated_at
                   WHERE excluded.updated_at >= progress.updated_at""",
                (
                    student["id"], skill["id"], status, score, note,
                    mentor["id"] if mentor else None, assessed_at,
                ),
            )
            imported += 1
        db.execute(
            """INSERT OR IGNORE INTO notifications
               (role, recipient_id, title, message, kind, dedupe_key)
               VALUES ('student', ?, 'Новая оценка компетенций', ?, 'success', ?)""",
            (
                student["id"],
                f"Наставник {mentor_name} оценил {imported} навыков. Средний уровень: {average_score}/5.",
                f"dual-survey-{source}-{external_id}",
            ),
        )
        db.commit()
        return {
            "ok": True, "imported": True, "duplicate": False,
            "batch_id": batch_id, "student_id": student["id"],
            "student_name": student["full_name"], "assessments": imported,
            "average_score": average_score,
        }


def validate_mentor_capacity(
    db: sqlite3.Connection,
    mentor_id: int | str | None,
    seats: int = 1,
    exclude_student_id: int | None = None,
) -> int | None:
    if mentor_id in (None, ""):
        return None
    mentor_id = int(mentor_id)
    mentor = db.execute(
        "SELECT full_name, student_limit, is_archived, role_type, can_mentor FROM mentors WHERE id = ?",
        (mentor_id,),
    ).fetchone()
    if not mentor:
        raise ValueError("Наставник не найден")
    if mentor["is_archived"]:
        raise ValueError("Нельзя назначить архивного наставника")
    if not bool(mentor["can_mentor"]):
        raise ValueError("Для этого сотрудника не включено наставничество студентов")
    query = "SELECT COUNT(*) AS n FROM students WHERE mentor_id = ? AND is_archived = 0"
    params: list[int] = [mentor_id]
    if exclude_student_id is not None:
        query += " AND id != ?"
        params.append(exclude_student_id)
    occupied = db.execute(query, params).fetchone()["n"]
    if occupied + seats > mentor["student_limit"]:
        raise ValueError(
            f"У наставника {mentor['full_name']} превышен лимит: "
            f"занято {occupied} из {mentor['student_limit']} мест"
        )
    return mentor_id


def grade_from_score(score: int) -> int:
    if score >= 90:
        return 5
    if score >= 70:
        return 4
    if score >= 50:
        return 3
    return 2


EVALUATION_TYPE_LABELS = {
    "section": "раздела",
    "practical": "практической работы (ЛПЗ)",
    "rotation": "ротации",
    "practice": "практики",
    "demo_exam": "демонстрационного экзамена",
}

EVALUATION_EXPORT_LABELS = {
    "section": "Итоги раздела",
    "practical": "Практическая работа (ЛПЗ)",
    "rotation": "Итоги ротации",
    "practice": "Итоги практики",
    "demo_exam": "Демоэкзамен",
}

ATTENDANCE_EXPORT_LABELS = {
    "present": "Присутствовал",
    "late": "Опоздал",
    "excused": "Уважительная причина",
    "absent": "Отсутствовал",
}

GRADE_EXPORT_LABELS = {
    5: "Отлично",
    4: "Хорошо",
    3: "Удовлетворительно",
    2: "Неудовлетворительно",
}


def normalize_course(data: dict) -> dict:
    validate_required(
        data,
        ["title", "category", "duration_hours", "description", "pass_score", "color"],
    )
    title = str(data["title"]).strip()
    category = str(data["category"]).strip()
    description = str(data["description"]).strip()
    if not title or not category or not description:
        raise ValueError("Заполните название, категорию и описание курса")
    duration_hours = int(data["duration_hours"])
    if duration_hours < 1 or duration_hours > 2000:
        raise ValueError("Продолжительность курса должна быть от 1 до 2000 часов")
    pass_score = int(data["pass_score"])
    if pass_score < 0 or pass_score > 100:
        raise ValueError("Проходной балл должен быть от 0 до 100")
    color = str(data["color"]).strip()
    if (
        len(color) != 7
        or not color.startswith("#")
        or any(character not in "0123456789abcdefABCDEF" for character in color[1:])
    ):
        raise ValueError("Некорректный цвет курса")
    return {
        "title": title,
        "category": category,
        "duration_hours": duration_hours,
        "description": description,
        "pass_score": pass_score,
        "color": color,
    }


def normalize_quiz_question(db: sqlite3.Connection, data: dict) -> dict:
    validate_required(data, ["course_id", "question", "options", "correct_index"])
    course_id = int(data["course_id"])
    course = db.execute(
        "SELECT id FROM courses WHERE id = ? AND is_archived = 0",
        (course_id,),
    ).fetchone()
    if not course:
        raise ValueError("Курс не найден или находится в архиве")
    question = str(data["question"]).strip()
    if not question:
        raise ValueError("Введите текст вопроса")
    if len(question) > 1000:
        raise ValueError("Текст вопроса не должен превышать 1000 символов")
    options = data["options"]
    if not isinstance(options, list) or len(options) != 4:
        raise ValueError("Укажите ровно четыре варианта ответа")
    options = [str(option).strip() for option in options]
    if any(not option for option in options):
        raise ValueError("Все четыре варианта ответа должны быть заполнены")
    if any(len(option) > 500 for option in options):
        raise ValueError("Вариант ответа не должен превышать 500 символов")
    if len({option.casefold() for option in options}) != 4:
        raise ValueError("Варианты ответа не должны повторяться")
    correct_index = int(data["correct_index"])
    if correct_index not in range(4):
        raise ValueError("Выберите правильный вариант ответа")
    return {
        "course_id": course_id,
        "question": question,
        "options": options,
        "correct_index": correct_index,
    }


def normalize_rotation(
    db: sqlite3.Connection,
    data: dict,
    exclude_rotation_id: int | None = None,
) -> dict:
    validate_required(data, ["student_id", "city", "company", "workshop", "start_date", "end_date"])
    city = str(data["city"]).strip()
    company = str(data["company"]).strip()
    workshop = str(data["workshop"]).strip()
    if not city or not company or not workshop:
        raise ValueError("Укажите город, предприятие и цех ротации")
    student_id = int(data["student_id"])
    student = db.execute(
        "SELECT id FROM students WHERE id = ? AND is_archived = 0",
        (student_id,),
    ).fetchone()
    if not student:
        raise ValueError("Студент не найден или находится в архиве")
    try:
        start_date = date.fromisoformat(str(data["start_date"]))
        end_date = date.fromisoformat(str(data["end_date"]))
    except (TypeError, ValueError):
        raise ValueError("Некорректный период ротации")
    if end_date < start_date:
        raise ValueError("Дата окончания не может быть раньше даты начала")
    overlap_query = """SELECT start_date, end_date FROM rotations
                       WHERE student_id = ? AND start_date <= ? AND end_date >= ?"""
    overlap_params: list[int | str] = [student_id, end_date.isoformat(), start_date.isoformat()]
    if exclude_rotation_id is not None:
        overlap_query += " AND id != ?"
        overlap_params.append(exclude_rotation_id)
    overlap = db.execute(overlap_query, overlap_params).fetchone()
    if overlap:
        raise ValueError(
            "Период пересекается с другой ротацией студента: "
            f"{overlap['start_date']} — {overlap['end_date']}"
        )
    return {
        "student_id": student_id,
        "city": city,
        "company": company,
        "workshop": workshop,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "status": rotation_status_for_period(start_date, end_date),
    }


def normalize_evaluation(db: sqlite3.Connection, data: dict) -> dict:
    validate_required(data, ["student_id", "evaluation_type", "section_title", "score"])
    section_title = str(data["section_title"]).strip()
    if not section_title:
        raise ValueError("Укажите наименование работы, раздела или этапа")
    evaluation_type = data["evaluation_type"]
    if evaluation_type not in EVALUATION_TYPE_LABELS:
        raise ValueError("Некорректный вид оценки")
    student_id = int(data["student_id"])
    student = db.execute(
        "SELECT full_name FROM students WHERE id = ? AND is_archived = 0",
        (student_id,),
    ).fetchone()
    if not student:
        raise ValueError("Студент не найден или находится в архиве")
    course_id = int(data["course_id"]) if data.get("course_id") else None
    if course_id:
        course = db.execute(
            "SELECT id FROM courses WHERE id = ? AND is_archived = 0",
            (course_id,),
        ).fetchone()
        if not course:
            raise ValueError("Учебный курс не найден или находится в архиве")
    score = int(data["score"])
    if score < 0 or score > 100:
        raise ValueError("Оценка должна быть от 0 до 100")
    evaluated_at = data.get("evaluated_at") or current_date().isoformat()
    try:
        date.fromisoformat(evaluated_at)
    except (TypeError, ValueError):
        raise ValueError("Некорректная дата оценивания")
    rotation_id = int(data["rotation_id"]) if data.get("rotation_id") else None
    if rotation_id:
        rotation = db.execute(
            "SELECT id FROM rotations WHERE id = ? AND student_id = ?",
            (rotation_id, student_id),
        ).fetchone()
        if not rotation:
            raise ValueError("Выбранная ротация не принадлежит студенту")
    evaluator_id = int(data["evaluator_id"]) if data.get("evaluator_id") else None
    if evaluator_id:
        evaluator = db.execute(
            "SELECT id FROM mentors WHERE id = ? AND is_archived = 0",
            (evaluator_id,),
        ).fetchone()
        if not evaluator:
            raise ValueError("Наставник не найден или находится в архиве")
    return {
        "student_id": student_id,
        "student_name": student["full_name"],
        "course_id": course_id,
        "evaluation_type": evaluation_type,
        "section_title": section_title,
        "score": score,
        "grade": grade_from_score(score),
        "comment": str(data.get("comment", "")).strip(),
        "rotation_id": rotation_id,
        "evaluator_id": evaluator_id,
        "evaluated_at": evaluated_at,
    }


def post_payload(path: str, data: dict) -> tuple[dict, int]:
    with db_connect() as db:
        if path == "/api/quiz-questions":
            item = normalize_quiz_question(db, data)
            cursor = db.execute(
                """INSERT INTO quiz_questions
                   (course_id, question, options_json, correct_index)
                   VALUES (?, ?, ?, ?)""",
                (
                    item["course_id"], item["question"],
                    json.dumps(item["options"], ensure_ascii=False),
                    item["correct_index"],
                ),
            )
            db.commit()
            return {"ok": True, "id": cursor.lastrowid}, HTTPStatus.CREATED

        if path == "/api/courses":
            course = normalize_course(data)
            cursor = db.execute(
                """INSERT INTO courses
                   (title, category, duration_hours, description, pass_score, color)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    course["title"], course["category"], course["duration_hours"],
                    course["description"], course["pass_score"], course["color"],
                ),
            )
            course_id = cursor.lastrowid
            db.execute(
                """INSERT INTO course_progress (student_id, course_id)
                   SELECT id, ? FROM students WHERE is_archived = 0""",
                (course_id,),
            )
            db.commit()
            return {"ok": True, "id": course_id}, HTTPStatus.CREATED

        if path == "/api/attendance":
            validate_required(data, ["attendance_date", "items"])
            try:
                date.fromisoformat(data["attendance_date"])
            except (TypeError, ValueError):
                raise ValueError("Некорректная дата посещаемости")
            if not isinstance(data["items"], list) or not data["items"]:
                raise ValueError("Не выбраны студенты для отметки")
            allowed_statuses = {"present", "absent", "excused", "late"}
            saved = 0
            for item in data["items"]:
                status = item.get("status")
                if status not in allowed_statuses:
                    raise ValueError("Укажите статус посещаемости для каждого студента")
                student = db.execute(
                    "SELECT id FROM students WHERE id = ? AND is_archived = 0",
                    (item.get("student_id"),),
                ).fetchone()
                if not student:
                    raise ValueError("Один из студентов не найден или находится в архиве")
                default_hours = 8 if status in ("present", "late") else 0
                hours = float(item.get("hours", default_hours))
                if hours < 0 or hours > 12:
                    raise ValueError("Количество часов должно быть от 0 до 12")
                db.execute(
                    """INSERT INTO attendance
                       (student_id, attendance_date, status, hours, note, marked_by_mentor_id, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                       ON CONFLICT(student_id, attendance_date) DO UPDATE SET
                       status = excluded.status, hours = excluded.hours, note = excluded.note,
                       marked_by_mentor_id = excluded.marked_by_mentor_id, updated_at = CURRENT_TIMESTAMP""",
                    (
                        item["student_id"], data["attendance_date"], status, hours,
                        item.get("note", ""), data.get("mentor_id") or None,
                    ),
                )
                saved += 1
            db.commit()
            return {"ok": True, "saved": saved}, HTTPStatus.OK

        if path == "/api/evaluations":
            evaluation = normalize_evaluation(db, data)
            cursor = db.execute(
                """INSERT INTO evaluations
                   (student_id, course_id, evaluation_type, section_title, score, grade, comment,
                    rotation_id, evaluator_id, evaluated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    evaluation["student_id"], evaluation["course_id"], evaluation["evaluation_type"],
                    evaluation["section_title"], evaluation["score"], evaluation["grade"],
                    evaluation["comment"], evaluation["rotation_id"],
                    evaluation["evaluator_id"], evaluation["evaluated_at"],
                ),
            )
            db.execute(
                """INSERT INTO notifications (role, recipient_id, title, message, kind)
                   VALUES ('student', ?, ?, ?, 'success')""",
                (
                    evaluation["student_id"],
                    f"Добавлена оценка по итогам {EVALUATION_TYPE_LABELS[evaluation['evaluation_type']]}",
                    f"{evaluation['section_title']}: {evaluation['score']} баллов, оценка {evaluation['grade']}.",
                ),
            )
            db.commit()
            return {
                "ok": True,
                "id": cursor.lastrowid,
                "score": evaluation["score"],
                "grade": evaluation["grade"],
            }, HTTPStatus.CREATED

        if path == "/api/progress":
            validate_required(data, ["student_id", "mentor_id", "items"])
            for item in data["items"]:
                status = item.get("status", "not_started")
                if status not in ("not_started", "in_progress", "confirmed"):
                    raise ValueError("Некорректный статус навыка")
                db.execute(
                    """INSERT INTO progress (student_id, skill_id, status, note, mentor_id, updated_at)
                       VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                       ON CONFLICT(student_id, skill_id) DO UPDATE SET
                         status = excluded.status, note = excluded.note,
                         mentor_id = excluded.mentor_id, updated_at = CURRENT_TIMESTAMP""",
                    (data["student_id"], item["skill_id"], status, item.get("note", ""), data["mentor_id"]),
                )
            db.execute(
                """INSERT INTO notifications (role, recipient_id, title, message, kind)
                   VALUES ('student', ?, 'Матрица навыков обновлена', 'Наставник сохранил результаты практики.', 'success')""",
                (data["student_id"],),
            )
            db.commit()
            return {"ok": True, "message": "Результаты сохранены"}, HTTPStatus.OK

        if path == "/api/safety-tests":
            validate_required(data, ["student_id", "passed"])
            if str(data["passed"]) not in {"0", "1", "False", "True", "false", "true"}:
                raise ValueError("Укажите статус допуска")
            passed = int(str(data["passed"]).lower() in {"1", "true"})
            score = 100 if passed else 0
            db.execute(
                "INSERT INTO safety_tests (student_id, score, passed) VALUES (?, ?, ?)",
                (data["student_id"], score, passed),
            )
            student = db.execute("SELECT full_name, mentor_id FROM students WHERE id = ?", (data["student_id"],)).fetchone()
            if not student:
                raise ValueError("Студент не найден")
            if passed:
                db.execute("UPDATE students SET status = 'На практике' WHERE id = ?", (data["student_id"],))
                db.execute(
                    """INSERT INTO notifications (role, recipient_id, title, message, kind)
                       VALUES ('mentor', ?, 'Студент допущен к практике', ?, 'success')""",
                    (student["mentor_id"], f"{student['full_name']}: допуск по технике безопасности оформлен."),
                )
            else:
                db.execute("UPDATE students SET status = 'Ожидает допуска' WHERE id = ?", (data["student_id"],))
            db.commit()
            return {"ok": True, "passed": bool(passed), "status": "На практике" if passed else "Ожидает допуска"}, HTTPStatus.OK

        if path == "/api/rotations":
            rotation = normalize_rotation(db, data)
            cursor = db.execute(
                """INSERT INTO rotations (student_id, city, company, workshop, start_date, end_date, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    rotation["student_id"], rotation["city"], rotation["company"],
                    rotation["workshop"], rotation["start_date"], rotation["end_date"],
                    rotation["status"],
                ),
            )
            db.commit()
            return {"ok": True, "id": cursor.lastrowid}, HTTPStatus.CREATED

        if path == "/api/students":
            validate_required(data, ["full_name", "institution", "specialty", "course", "stream"])
            mentor_id = validate_mentor_capacity(db, data.get("mentor_id"))
            birth_date = data.get("birth_date", "")
            if birth_date:
                try:
                    date.fromisoformat(birth_date)
                except (TypeError, ValueError):
                    raise ValueError("Некорректная дата рождения")
            cursor = db.execute(
                """INSERT INTO students
                   (full_name, institution, specialty, course, stream, base_city, status,
                    mentor_id, avatar_color, phone, birth_date, address, additional_info)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["full_name"], data["institution"], data["specialty"], int(data["course"]),
                    data["stream"], data.get("base_city", ""), data.get("status", "Ожидает допуска"),
                    mentor_id, data.get("avatar_color", "#D71920"), data.get("phone", ""),
                    birth_date, data.get("address", ""), data.get("additional_info", ""),
                ),
            )
            student_id = cursor.lastrowid
            db.execute(
                "INSERT INTO progress (student_id, skill_id) SELECT ?, id FROM skills WHERE is_active = 1",
                (student_id,),
            )
            db.execute(
                """INSERT INTO course_progress (student_id, course_id)
                   SELECT ?, id FROM courses WHERE is_archived = 0""",
                (student_id,),
            )
            sync_profile_account(
                db, "student", student_id, data["full_name"], data.get("phone", "")
            )
            db.commit()
            return {"ok": True, "id": student_id}, HTTPStatus.CREATED

        if path == "/api/mentors":
            validate_required(
                data,
                ["full_name", "workshop", "qualification", "student_limit", "enterprise", "city", "role_type"],
            )
            student_limit = int(data["student_limit"])
            if student_limit < 1 or student_limit > 50:
                raise ValueError("Лимит должен быть от 1 до 50 студентов")
            role_type = str(data["role_type"])
            if role_type not in {"mentor", "supervisor"}:
                raise ValueError("Некорректная роль в программе")
            can_mentor = int(str(data.get("can_mentor", int(role_type == "mentor"))).lower() in {"1", "true", "yes", "on"})
            cursor = db.execute(
                """INSERT INTO mentors
                   (full_name, workshop, qualification, student_limit, phone,
                    enterprise, city, role_type, can_mentor)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["full_name"], data["workshop"], data["qualification"],
                    student_limit, data.get("phone", ""), data["enterprise"],
                    data["city"], role_type, can_mentor,
                ),
            )
            mentor_id = int(cursor.lastrowid)
            sync_profile_account(
                db, "mentor", mentor_id, data["full_name"], data.get("phone", "")
            )
            db.commit()
            return {"ok": True, "id": mentor_id}, HTTPStatus.CREATED

        if path == "/api/quiz-attempts":
            validate_required(data, ["student_id", "course_id", "answers"])
            student_id = int(data["student_id"])
            course_id = int(data["course_id"])
            answers = data["answers"]
            course = db.execute(
                "SELECT * FROM courses WHERE id = ? AND is_archived = 0",
                (course_id,),
            ).fetchone()
            questions = db.execute("SELECT * FROM quiz_questions WHERE course_id = ? ORDER BY id", (course_id,)).fetchall()
            if not course or not questions:
                raise ValueError("Тест для курса не найден")
            correct = sum(index < len(answers) and int(answers[index]) == question["correct_index"] for index, question in enumerate(questions))
            score = round(correct / len(questions) * 100)
            passed = score >= course["pass_score"]
            attempt_cursor = db.execute(
                """INSERT INTO quiz_attempts
                   (student_id, course_id, score, correct_answers, total_questions, passed)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (student_id, course_id, score, correct, len(questions), int(passed)),
            )
            best_score = db.execute(
                """SELECT MAX(score) AS score FROM quiz_attempts
                   WHERE student_id = ? AND course_id = ?""",
                (student_id, course_id),
            ).fetchone()["score"]
            course_completed = int(best_score) >= int(course["pass_score"])
            db.execute(
                """INSERT INTO course_progress (student_id, course_id, percent, status, updated_at)
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(student_id, course_id) DO UPDATE SET
                   percent = excluded.percent, status = excluded.status, updated_at = CURRENT_TIMESTAMP""",
                (
                    student_id,
                    course_id,
                    100 if course_completed else int(best_score),
                    "completed" if course_completed else "in_progress",
                ),
            )
            if course_id == 2:
                db.execute(
                    "INSERT INTO safety_tests (student_id, score, passed) VALUES (?, ?, ?)",
                    (student_id, score, int(course_completed)),
                )
                student = db.execute("SELECT full_name, mentor_id FROM students WHERE id = ?", (student_id,)).fetchone()
                db.execute("UPDATE students SET status = ? WHERE id = ?", ("На практике" if course_completed else "Ожидает допуска", student_id))
                if passed:
                    db.execute(
                        """INSERT INTO notifications (role, recipient_id, title, message, kind)
                           VALUES ('mentor', ?, 'Студент допущен к практике', ?, 'success')""",
                        (student["mentor_id"], f"{student['full_name']}: допуск по технике безопасности оформлен."),
                    )
            db.commit()
            return {
                "ok": True,
                "attempt_id": attempt_cursor.lastrowid,
                "score": score,
                "best_score": best_score,
                "passed": passed,
                "correct": correct,
                "total": len(questions),
                "pass_score": course["pass_score"],
            }, HTTPStatus.OK

    return {"error": "Маршрут не найден"}, HTTPStatus.NOT_FOUND


def patch_payload(path: str, data: dict) -> tuple[dict, int]:
    parts = path.strip("/").split("/")
    with db_connect() as db:
        if len(parts) == 3 and parts[:2] == ["api", "notifications"]:
            db.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (int(parts[2]),))
            db.commit()
            return {"ok": True}, HTTPStatus.OK
        if len(parts) == 3 and parts[:2] == ["api", "quiz-questions"]:
            question_id = int(parts[2])
            existing = db.execute(
                "SELECT id FROM quiz_questions WHERE id = ?",
                (question_id,),
            ).fetchone()
            if not existing:
                raise ValueError("Вопрос не найден")
            item = normalize_quiz_question(db, data)
            db.execute(
                """UPDATE quiz_questions SET course_id = ?, question = ?,
                   options_json = ?, correct_index = ? WHERE id = ?""",
                (
                    item["course_id"], item["question"],
                    json.dumps(item["options"], ensure_ascii=False),
                    item["correct_index"], question_id,
                ),
            )
            db.commit()
            return {"ok": True, "id": question_id}, HTTPStatus.OK
        if len(parts) == 3 and parts[:2] == ["api", "courses"]:
            course_id = int(parts[2])
            existing = db.execute(
                "SELECT * FROM courses WHERE id = ?",
                (course_id,),
            ).fetchone()
            if not existing:
                raise ValueError("Курс не найден")
            if "is_archived" in data:
                archive = bool(data["is_archived"])
                if archive and not existing["is_archived"]:
                    db.execute(
                        """UPDATE courses SET is_archived = 1,
                           archived_at = CURRENT_TIMESTAMP WHERE id = ?""",
                        (course_id,),
                    )
                elif not archive and existing["is_archived"]:
                    db.execute(
                        """UPDATE courses SET is_archived = 0,
                           archived_at = NULL WHERE id = ?""",
                        (course_id,),
                    )
                    db.execute(
                        """INSERT OR IGNORE INTO course_progress (student_id, course_id)
                           SELECT id, ? FROM students WHERE is_archived = 0""",
                        (course_id,),
                    )
                db.commit()
                return {"ok": True, "archived": archive}, HTTPStatus.OK
            course = normalize_course(data)
            db.execute(
                """UPDATE courses SET title = ?, category = ?, duration_hours = ?,
                   description = ?, pass_score = ?, color = ? WHERE id = ?""",
                (
                    course["title"], course["category"], course["duration_hours"],
                    course["description"], course["pass_score"], course["color"],
                    course_id,
                ),
            )
            db.commit()
            return {"ok": True, "id": course_id}, HTTPStatus.OK
        if len(parts) == 3 and parts[:2] == ["api", "evaluations"]:
            evaluation_id = int(parts[2])
            existing = db.execute(
                "SELECT id FROM evaluations WHERE id = ?",
                (evaluation_id,),
            ).fetchone()
            if not existing:
                raise ValueError("Оценка не найдена")
            evaluation = normalize_evaluation(db, data)
            db.execute(
                """UPDATE evaluations SET
                   student_id = ?, course_id = ?, evaluation_type = ?, section_title = ?, score = ?,
                   grade = ?, comment = ?, rotation_id = ?, evaluator_id = ?, evaluated_at = ?
                   WHERE id = ?""",
                (
                    evaluation["student_id"], evaluation["course_id"], evaluation["evaluation_type"],
                    evaluation["section_title"], evaluation["score"], evaluation["grade"],
                    evaluation["comment"], evaluation["rotation_id"],
                    evaluation["evaluator_id"], evaluation["evaluated_at"], evaluation_id,
                ),
            )
            db.commit()
            return {
                "ok": True,
                "id": evaluation_id,
                "score": evaluation["score"],
                "grade": evaluation["grade"],
            }, HTTPStatus.OK
        if len(parts) == 3 and parts[:2] == ["api", "rotations"]:
            rotation_id = int(parts[2])
            existing = db.execute(
                "SELECT id FROM rotations WHERE id = ?",
                (rotation_id,),
            ).fetchone()
            if not existing:
                raise ValueError("Ротация не найдена")
            rotation = normalize_rotation(db, data, exclude_rotation_id=rotation_id)
            db.execute(
                """UPDATE rotations SET student_id = ?, city = ?, company = ?, workshop = ?,
                   start_date = ?, end_date = ?, status = ? WHERE id = ?""",
                (
                    rotation["student_id"], rotation["city"], rotation["company"],
                    rotation["workshop"], rotation["start_date"], rotation["end_date"],
                    rotation["status"], rotation_id,
                ),
            )
            db.commit()
            return {"ok": True, "id": rotation_id}, HTTPStatus.OK
        if len(parts) == 3 and parts[:2] == ["api", "students"]:
            student_id = int(parts[2])
            student = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
            if not student:
                raise ValueError("Студент не найден")
            if "is_archived" in data:
                archive = bool(data["is_archived"])
                if archive and not student["is_archived"]:
                    db.execute(
                        """UPDATE students SET is_archived = 1, archived_at = CURRENT_TIMESTAMP,
                           archived_from_status = status, status = 'Архив' WHERE id = ?""",
                        (student_id,),
                    )
                elif not archive and student["is_archived"]:
                    restore_mentor_id = student["mentor_id"]
                    if restore_mentor_id:
                        restore_mentor = db.execute(
                            "SELECT is_archived FROM mentors WHERE id = ?", (restore_mentor_id,)
                        ).fetchone()
                        if not restore_mentor or restore_mentor["is_archived"]:
                            restore_mentor_id = None
                        else:
                            validate_mentor_capacity(db, restore_mentor_id)
                    db.execute(
                        """UPDATE students SET is_archived = 0, archived_at = NULL,
                           status = COALESCE(archived_from_status, 'Ожидает допуска'),
                           mentor_id = ? WHERE id = ?""",
                        (restore_mentor_id, student_id),
                    )
                db.execute(
                    "UPDATE users SET is_active = ? WHERE role = 'student' AND student_id = ?",
                    (int(not archive), student_id),
                )
                db.commit()
                return {"ok": True, "archived": archive}, HTTPStatus.OK
            rotation_fields_present = "rotation_city" in data or "rotation_company" in data
            rotation = None
            if rotation_fields_present:
                rotation_id = int(data.get("rotation_id") or 0)
                rotation = db.execute(
                    "SELECT id FROM rotations WHERE id = ? AND student_id = ?",
                    (rotation_id, student_id),
                ).fetchone()
                if not rotation:
                    raise ValueError("Текущая ротация студента не найдена")
                if not str(data.get("rotation_city", "")).strip():
                    raise ValueError("Укажите город ротации")
                if not str(data.get("rotation_company", "")).strip():
                    raise ValueError("Укажите предприятие ротации")
            allowed = {"full_name", "institution", "status", "mentor_id", "base_city", "specialty", "course", "stream", "phone", "birth_date", "address", "additional_info"}
            fields = [(key, value) for key, value in data.items() if key in allowed]
            if not fields and not rotation_fields_present:
                raise ValueError("Нет данных для обновления")
            normalized = []
            for key, value in fields:
                if key == "mentor_id":
                    value = validate_mentor_capacity(db, value, exclude_student_id=student_id)
                elif key == "course":
                    value = int(value)
                elif key == "birth_date" and value:
                    try:
                        date.fromisoformat(value)
                    except (TypeError, ValueError):
                        raise ValueError("Некорректная дата рождения")
                normalized.append((key, value))
            fields = normalized
            if fields:
                setters = ", ".join(f"{field} = ?" for field, _ in fields)
                values = [value for _, value in fields] + [student_id]
                db.execute(f"UPDATE students SET {setters} WHERE id = ?", values)
            if rotation_fields_present:
                db.execute(
                    "UPDATE rotations SET city = ?, company = ? WHERE id = ?",
                    (
                        str(data["rotation_city"]).strip(),
                        str(data["rotation_company"]).strip(),
                        rotation["id"],
                    ),
                )
            updated_student = db.execute(
                "SELECT full_name, phone, is_archived FROM students WHERE id = ?",
                (student_id,),
            ).fetchone()
            sync_profile_account(
                db, "student", student_id, updated_student["full_name"],
                updated_student["phone"], not bool(updated_student["is_archived"]),
            )
            db.commit()
            return {"ok": True}, HTTPStatus.OK
        if len(parts) == 3 and parts[:2] == ["api", "mentors"]:
            mentor_id = int(parts[2])
            mentor = db.execute("SELECT * FROM mentors WHERE id = ?", (mentor_id,)).fetchone()
            if not mentor:
                raise ValueError("Наставник не найден")
            if "is_archived" in data:
                archive = bool(data["is_archived"])
                assigned = 0
                if archive and not mentor["is_archived"]:
                    assigned = db.execute(
                        "SELECT COUNT(*) AS n FROM students WHERE mentor_id = ? AND is_archived = 0",
                        (mentor_id,),
                    ).fetchone()["n"]
                    replacement_id = data.get("replacement_mentor_id")
                    if assigned and replacement_id in (None, ""):
                        raise ValueError("Сначала выберите наставника для переназначения студентов")
                    if assigned:
                        if int(replacement_id) == mentor_id:
                            raise ValueError("Выберите другого наставника")
                        replacement_id = validate_mentor_capacity(db, replacement_id, seats=assigned)
                        db.execute(
                            "UPDATE students SET mentor_id = ? WHERE mentor_id = ? AND is_archived = 0",
                            (replacement_id, mentor_id),
                        )
                    db.execute(
                        "UPDATE mentors SET is_archived = 1, archived_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (mentor_id,),
                    )
                elif not archive and mentor["is_archived"]:
                    db.execute(
                        "UPDATE mentors SET is_archived = 0, archived_at = NULL WHERE id = ?",
                        (mentor_id,),
                    )
                db.execute(
                    "UPDATE users SET is_active = ? WHERE role = 'mentor' AND mentor_id = ?",
                    (int(not archive), mentor_id),
                )
                db.commit()
                return {"ok": True, "archived": archive, "reassigned_students": assigned if archive else 0}, HTTPStatus.OK

            allowed = {
                "full_name", "workshop", "qualification", "student_limit", "phone",
                "enterprise", "city", "role_type", "can_mentor",
            }
            fields = [(key, value) for key, value in data.items() if key in allowed]
            if not fields:
                raise ValueError("Нет данных для обновления")
            normalized = []
            for key, value in fields:
                if key == "student_limit":
                    value = int(value)
                    occupied = db.execute(
                        "SELECT COUNT(*) AS n FROM students WHERE mentor_id = ? AND is_archived = 0",
                        (mentor_id,),
                    ).fetchone()["n"]
                    if value < occupied:
                        raise ValueError(f"Лимит нельзя снизить ниже текущей нагрузки: {occupied}")
                    if value < 1 or value > 50:
                        raise ValueError("Лимит должен быть от 1 до 50 студентов")
                elif key == "role_type":
                    value = str(value)
                    if value not in {"mentor", "supervisor"}:
                        raise ValueError("Некорректная роль в программе")
                elif key == "can_mentor":
                    value = int(str(value).lower() in {"1", "true", "yes", "on"})
                    if not value:
                        occupied = db.execute(
                            "SELECT COUNT(*) AS n FROM students WHERE mentor_id = ? AND is_archived = 0",
                            (mentor_id,),
                        ).fetchone()["n"]
                        if occupied:
                            raise ValueError(
                                f"Сначала переназначьте закреплённых студентов: {occupied}"
                            )
                elif key in {"enterprise", "city"} and not str(value).strip():
                    raise ValueError("Укажите предприятие и город")
                normalized.append((key, value))
            setters = ", ".join(f"{field} = ?" for field, _ in normalized)
            values = [value for _, value in normalized] + [mentor_id]
            db.execute(f"UPDATE mentors SET {setters} WHERE id = ?", values)
            updated_mentor = db.execute(
                "SELECT full_name, phone, is_archived FROM mentors WHERE id = ?",
                (mentor_id,),
            ).fetchone()
            sync_profile_account(
                db, "mentor", mentor_id, updated_mentor["full_name"],
                updated_mentor["phone"], not bool(updated_mentor["is_archived"]),
            )
            db.commit()
            return {"ok": True}, HTTPStatus.OK
    return {"error": "Маршрут не найден"}, HTTPStatus.NOT_FOUND


def delete_payload(path: str) -> tuple[dict, int]:
    parts = path.strip("/").split("/")
    with db_connect() as db:
        if len(parts) == 3 and parts[:2] == ["api", "quiz-questions"]:
            question_id = int(parts[2])
            question = db.execute(
                "SELECT id, course_id FROM quiz_questions WHERE id = ?",
                (question_id,),
            ).fetchone()
            if not question:
                raise ValueError("Вопрос не найден")
            db.execute("DELETE FROM quiz_questions WHERE id = ?", (question_id,))
            db.commit()
            return {
                "ok": True,
                "deleted_id": question_id,
                "course_id": question["course_id"],
            }, HTTPStatus.OK
        if len(parts) == 3 and parts[:2] == ["api", "evaluations"]:
            evaluation_id = int(parts[2])
            evaluation = db.execute(
                "SELECT id FROM evaluations WHERE id = ?",
                (evaluation_id,),
            ).fetchone()
            if not evaluation:
                raise ValueError("Оценка не найдена")
            db.execute("DELETE FROM evaluations WHERE id = ?", (evaluation_id,))
            db.commit()
            return {"ok": True, "deleted_id": evaluation_id}, HTTPStatus.OK
    return {"error": "Маршрут не найден"}, HTTPStatus.NOT_FOUND


def excel_column_name(index: int) -> str:
    """Return the 1-based Excel column name (1 -> A, 27 -> AA)."""
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def safe_xml_text(value: object) -> str:
    text = str(value if value is not None else "")
    text = "".join(
        char for char in text
        if char in "\t\n\r" or ord(char) >= 32
    )
    return xml_escape(text)


def excel_cell(reference: str, value: object, style: int = 4) -> str:
    if isinstance(value, date):
        serial = (value - date(1899, 12, 30)).days
        return f'<c r="{reference}" s="5"><v>{serial}</v></c>'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{reference}" s="6"><v>{value}</v></c>'
    return (
        f'<c r="{reference}" s="{style}" t="inlineStr">'
        f'<is><t xml:space="preserve">{safe_xml_text(value)}</t></is></c>'
    )


def build_xlsx(
    sheet_name: str,
    title: str,
    headers: list[str],
    data_rows: list[list[object]],
    column_widths: list[float],
    subtitle: str,
) -> bytes:
    """Create a styled, filterable XLSX report using only the standard library."""
    last_column = excel_column_name(len(headers))
    last_row = max(3 + len(data_rows), 3)
    rows_xml = [
        (
            '<row r="1" ht="28" customHeight="1">'
            f'{excel_cell("A1", title, 1)}</row>'
        ),
        (
            '<row r="2" ht="20" customHeight="1">'
            f'{excel_cell("A2", subtitle, 2)}</row>'
        ),
        '<row r="3" ht="34" customHeight="1">'
        + "".join(
            excel_cell(f"{excel_column_name(index)}3", header, 3)
            for index, header in enumerate(headers, 1)
        )
        + "</row>",
    ]
    for row_index, values in enumerate(data_rows, 4):
        cells = "".join(
            excel_cell(f"{excel_column_name(column_index)}{row_index}", value)
            for column_index, value in enumerate(values, 1)
        )
        rows_xml.append(f'<row r="{row_index}">{cells}</row>')

    columns_xml = "".join(
        f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>'
        for index, width in enumerate(column_widths, 1)
    )
    worksheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>
  <dimension ref="A1:{last_column}{last_row}"/>
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="3" topLeftCell="A4" activePane="bottomLeft" state="frozen"/><selection pane="bottomLeft" activeCell="A4" sqref="A4"/></sheetView></sheetViews>
  <sheetFormatPr defaultRowHeight="18"/>
  <cols>{columns_xml}</cols>
  <sheetData>{''.join(rows_xml)}</sheetData>
  <autoFilter ref="A3:{last_column}{last_row}"/>
  <mergeCells count="2"><mergeCell ref="A1:{last_column}1"/><mergeCell ref="A2:{last_column}2"/></mergeCells>
  <pageMargins left="0.3" right="0.3" top="0.5" bottom="0.5" header="0.2" footer="0.2"/>
  <pageSetup orientation="landscape" fitToWidth="1" fitToHeight="0"/>
</worksheet>'''

    styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <numFmts count="1"><numFmt numFmtId="164" formatCode="dd.mm.yyyy"/></numFmts>
  <fonts count="4">
    <font><sz val="10"/><name val="Calibri"/><family val="2"/></font>
    <font><b/><color rgb="FFFFFFFF"/><sz val="16"/><name val="Calibri"/><family val="2"/></font>
    <font><i/><color rgb="FF64748B"/><sz val="9"/><name val="Calibri"/><family val="2"/></font>
    <font><b/><color rgb="FFFFFFFF"/><sz val="10"/><name val="Calibri"/><family val="2"/></font>
  </fonts>
  <fills count="4">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF202428"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFD71920"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border><left style="thin"><color rgb="FFE2E8F0"/></left><right style="thin"><color rgb="FFE2E8F0"/></right><top style="thin"><color rgb="FFE2E8F0"/></top><bottom style="thin"><color rgb="FFE2E8F0"/></bottom><diagonal/></border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="7">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="3" fillId="3" borderId="1" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''

    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    files = {
        "[Content_Types].xml": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>''',
        "_rels/.rels": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>''',
        "docProps/app.xml": f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>CT Assembly Learning Hub</Application><TitlesOfParts><vt:vector size="1" baseType="lpstr"><vt:lpstr>{safe_xml_text(sheet_name)}</vt:lpstr></vt:vector></TitlesOfParts></Properties>''',
        "docProps/core.xml": f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>{safe_xml_text(title)}</dc:title><dc:creator>CT Assembly Learning Hub</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified></cp:coreProperties>''',
        "xl/workbook.xml": f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><bookViews><workbookView/></bookViews><sheets><sheet name="{safe_xml_text(sheet_name[:31])}" sheetId="1" r:id="rId1"/></sheets></workbook>''',
        "xl/_rels/workbook.xml.rels": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>''',
        "xl/styles.xml": styles_xml,
        "xl/worksheets/sheet1.xml": worksheet_xml,
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as workbook:
        for path, contents in files.items():
            workbook.writestr(path, contents.encode("utf-8"))
    return output.getvalue()


def build_excel_export(path: str, query: dict[str, list[str]], user: dict) -> tuple[bytes, str]:
    stream = query.get("stream", [""])[0].strip()
    course_filter = query.get("course", [""])[0].strip()
    month_filter = query.get("month", [""])[0].strip()
    type_filter = query.get("type", [""])[0].strip()
    exported_at = datetime.now(BUSINESS_TIMEZONE).strftime("%d.%m.%Y %H:%M")
    stream_note = f" • поток: {stream}" if stream else " • все потоки"
    with db_connect() as db:
        sync_rotation_statuses(db)
        allowed = permitted_student_ids(db, user)
        if path == "/api/export/accounts.xlsx":
            if user["role"] != "admin":
                raise PermissionError("Выгрузка учётных записей доступна только администрации")
            role_labels = {"admin": "Администратор", "mentor": "Наставник", "student": "Студент"}
            records = account_list(db)
            data_rows = [
                [
                    index,
                    record["full_name"],
                    record.get("account_title") or role_labels.get(record["role"], record["role"]),
                    record["phone"],
                    "Активна" if record["is_active"] else "Отключена",
                    "Требуется" if record["must_change_password"] else "Изменён",
                    record["created_at"],
                    record["last_login_at"] or "Ещё не входил",
                    "Без удаления" if not record["can_delete"] else "Полный доступ",
                ]
                for index, record in enumerate(records, 1)
            ]
            workbook = build_xlsx(
                "Учётные записи",
                "Учётные записи CT Assembly Learning Hub",
                ["№", "ФИО", "Роль", "Телефон / логин", "Состояние", "Пароль", "Создана", "Последний вход", "Права"],
                data_rows,
                [6, 32, 20, 20, 14, 16, 22, 22, 18],
                f"Пароли не включаются в выгрузку • выгружено {exported_at}",
            )
            return workbook, f"accounts_{current_date().isoformat()}.xlsx"

        if path == "/api/export/attendance.xlsx":
            records = [record for record in get_attendance(db) if record["student_id"] in allowed]
            if stream:
                records = [record for record in records if record["stream"] == stream]
            data_rows = [
                [
                    index,
                    date.fromisoformat(record["attendance_date"]),
                    record["stream"],
                    record["student_name"],
                    record["specialty"],
                    ATTENDANCE_EXPORT_LABELS.get(record["status"], record["status"]),
                    record["hours"],
                    record["note"],
                    record["marked_by_name"] or "Учебный центр",
                ]
                for index, record in enumerate(records, 1)
            ]
            workbook = build_xlsx(
                "Посещаемость",
                "Журнал посещаемости",
                ["№", "Дата", "Поток", "ФИО", "Специальность", "Статус", "Часы", "Комментарий", "Отметил"],
                data_rows,
                [6, 13, 13, 30, 32, 23, 9, 32, 24],
                f"Сохранённые отметки{stream_note} • выгружено {exported_at}",
            )
            return workbook, f"attendance_{current_date().isoformat()}.xlsx"

        if path == "/api/export/evaluations.xlsx":
            records = [record for record in get_evaluations(db) if record["student_id"] in allowed]
            if stream:
                records = [record for record in records if record["stream"] == stream]
            if course_filter == "unassigned":
                records = [record for record in records if not record["course_id"]]
            elif course_filter:
                try:
                    course_id = int(course_filter)
                except ValueError as exc:
                    raise ValueError("Некорректный фильтр учебного курса") from exc
                records = [record for record in records if record["course_id"] == course_id]
            if month_filter:
                try:
                    datetime.strptime(month_filter, "%Y-%m")
                except ValueError as exc:
                    raise ValueError("Некорректный фильтр месяца") from exc
                records = [record for record in records if record["evaluated_at"].startswith(month_filter)]
            if type_filter:
                if type_filter not in EVALUATION_TYPE_LABELS:
                    raise ValueError("Некорректный фильтр вида контроля")
                records = [record for record in records if record["evaluation_type"] == type_filter]
            data_rows = [
                [
                    index,
                    date.fromisoformat(record["evaluated_at"]),
                    record["stream"],
                    record["student_name"],
                    record["specialty"],
                    record["course_title"] or "Без привязки к курсу",
                    EVALUATION_EXPORT_LABELS.get(record["evaluation_type"], record["evaluation_type"]),
                    record["section_title"],
                    record["score"],
                    record["grade"],
                    GRADE_EXPORT_LABELS.get(record["grade"], ""),
                    record["comment"],
                    record["evaluator_name"] or "Учебный центр",
                    record["rotation_company"] or "—",
                    record["rotation_workshop"] or "—",
                ]
                for index, record in enumerate(records, 1)
            ]
            workbook = build_xlsx(
                "Успеваемость",
                "Журнал успеваемости",
                ["№", "Дата", "Поток", "ФИО", "Специальность", "Учебный курс / модуль", "Вид контроля", "Работа / раздел / этап", "Балл", "Оценка", "Результат", "Комментарий", "Оценил", "Предприятие ротации", "Цех / отдел"],
                data_rows,
                [6, 13, 13, 30, 32, 34, 25, 34, 9, 10, 22, 32, 24, 24, 24],
                f"Результаты по выбранным фильтрам{stream_note} • выгружено {exported_at}",
            )
            return workbook, f"evaluations_{current_date().isoformat()}.xlsx"

    raise ValueError("Выгрузка не найдена")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def authenticated_user(token: str | None) -> dict | None:
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = utc_timestamp()
    with db_connect() as db:
        db.execute("DELETE FROM auth_sessions WHERE expires_at <= ?", (now,))
        user = db.execute(
            """SELECT u.* FROM auth_sessions s
               JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > ? AND u.is_active = 1""",
            (token_hash, now),
        ).fetchone()
        db.commit()
        return dict(user) if user else None


def ensure_endpoint_access(
    user: dict,
    method: str,
    path: str,
    query: dict[str, list[str]] | None = None,
    data: dict | None = None,
) -> None:
    if user["role"] == "admin":
        if not bool(user.get("can_delete", 1)):
            if method == "DELETE":
                raise PermissionError("Руководителю недоступно удаление записей")
            if method == "PATCH" and bool((data or {}).get("is_archived")):
                raise PermissionError("Руководителю недоступна архивация записей")
        return
    query = query or {}
    data = data or {}
    mentor_get = {
        "/api/bootstrap", "/api/students", "/api/mentors", "/api/skills",
        "/api/skill-matrix",
        "/api/rotations", "/api/attendance", "/api/evaluations",
        "/api/student-profile", "/api/courses", "/api/quiz",
        "/api/notifications", "/api/progress",
        "/api/export/attendance.xlsx", "/api/export/evaluations.xlsx",
    }
    student_get = {
        "/api/bootstrap", "/api/mentors", "/api/skills", "/api/rotations",
        "/api/attendance", "/api/evaluations", "/api/student-profile",
        "/api/courses", "/api/quiz", "/api/notifications", "/api/progress",
    }
    if method == "GET":
        allowed = mentor_get if user["role"] == "mentor" else student_get
        if path in allowed:
            return
    if method == "POST":
        if user["role"] == "mentor" and path in {"/api/attendance", "/api/evaluations", "/api/progress"}:
            return
        if user["role"] == "student" and path == "/api/quiz-attempts":
            return
    if method == "PATCH":
        if user["role"] == "mentor" and (path.startswith("/api/evaluations/") or path.startswith("/api/notifications/")):
            return
        if user["role"] == "student" and path.startswith("/api/notifications/"):
            return
    if method == "DELETE" and user["role"] == "mentor" and path.startswith("/api/evaluations/"):
        return
    raise PermissionError("Для вашей роли это действие недоступно")


def prepare_scoped_mutation(user: dict, method: str, path: str, data: dict) -> dict:
    prepared = dict(data)
    with db_connect() as db:
        if user["role"] == "mentor":
            mentor_id = int(user["mentor_id"])
            if path == "/api/attendance":
                for item in prepared.get("items", []):
                    ensure_student_access(db, user, int(item.get("student_id") or 0))
                prepared["mentor_id"] = mentor_id
            elif path in {"/api/evaluations", "/api/progress"}:
                ensure_student_access(db, user, int(prepared.get("student_id") or 0))
                prepared["evaluator_id" if path == "/api/evaluations" else "mentor_id"] = mentor_id
            elif path.startswith("/api/evaluations/"):
                evaluation_id = int(path.rsplit("/", 1)[1])
                evaluation = db.execute(
                    "SELECT student_id FROM evaluations WHERE id = ?", (evaluation_id,)
                ).fetchone()
                if not evaluation:
                    raise ValueError("Оценка не найдена")
                ensure_student_access(db, user, evaluation["student_id"])
                if method == "PATCH":
                    ensure_student_access(db, user, int(prepared.get("student_id") or 0))
                    prepared["evaluator_id"] = mentor_id
            elif path.startswith("/api/notifications/"):
                notification_id = int(path.rsplit("/", 1)[1])
                notification = db.execute(
                    """SELECT id FROM notifications WHERE id = ? AND role = 'mentor'
                       AND (recipient_id = ? OR recipient_id IS NULL)""",
                    (notification_id, mentor_id),
                ).fetchone()
                if not notification:
                    raise PermissionError("Нет доступа к этому уведомлению")
        elif user["role"] == "student":
            if path == "/api/quiz-attempts":
                prepared["student_id"] = int(user["student_id"])
            elif path.startswith("/api/notifications/"):
                notification_id = int(path.rsplit("/", 1)[1])
                notification = db.execute(
                    """SELECT id FROM notifications WHERE id = ? AND role = 'student'
                       AND (recipient_id = ? OR recipient_id IS NULL)""",
                    (notification_id, user["student_id"]),
                ).fetchone()
                if not notification:
                    raise PermissionError("Нет доступа к этому уведомлению")
    return prepared


class LMSHandler(BaseHTTPRequestHandler):
    server_version = "CTAssemblyLearningHub/2.0"

    def log_message(self, fmt: str, *args) -> None:
        sys.stdout.write(f"[{self.log_date_time_string()}] {fmt % args}\n")

    def send_json(
        self,
        payload: dict | list,
        status: int = HTTPStatus.OK,
        headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def send_download(self, body: bytes, filename: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header(
            "Content-Type",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def parse_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise ValueError("Слишком большой запрос")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8")) if raw else {}

    def session_token(self) -> str | None:
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            return None
        item = cookie.get("lms_session")
        return item.value if item else None

    def cookie_header(self, token: str, max_age: int) -> str:
        secure = (
            os.environ.get("LMS_COOKIE_SECURE") == "1"
            or self.headers.get("X-Forwarded-Proto", "").lower() == "https"
        )
        parts = [
            f"lms_session={token}", "Path=/", "HttpOnly", "SameSite=Lax",
            f"Max-Age={max_age}",
        ]
        if secure:
            parts.append("Secure")
        return "; ".join(parts)

    def require_user(self, allow_password_change: bool = False) -> dict:
        user = authenticated_user(self.session_token())
        if not user:
            raise PermissionError("Требуется вход в систему")
        if user["must_change_password"] and not allow_password_change:
            raise PermissionError("Сначала измените временный пароль")
        return user

    def handle_login(self) -> None:
        data = self.parse_body()
        phone = normalize_phone(data.get("phone", ""))
        password = str(data.get("password", ""))
        with db_connect() as db:
            user = db.execute(
                "SELECT * FROM users WHERE phone = ? AND is_active = 1", (phone,)
            ).fetchone()
            if not user or not verify_password(password, user["password_hash"], user["password_salt"]):
                raise PermissionError("Неверный номер телефона или пароль")
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            created_at = datetime.now(timezone.utc)
            expires_at = created_at + timedelta(hours=SESSION_HOURS)
            db.execute("DELETE FROM auth_sessions WHERE expires_at <= ?", (created_at.isoformat(),))
            db.execute(
                "INSERT INTO auth_sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (token_hash, user["id"], created_at.isoformat(), expires_at.isoformat()),
            )
            db.execute(
                "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],)
            )
            db.commit()
            self.send_json(
                {"ok": True, "user": public_user(user)},
                HTTPStatus.OK,
                {"Set-Cookie": self.cookie_header(token, SESSION_HOURS * 3600)},
            )

    def handle_logout(self) -> None:
        token = self.session_token()
        if token:
            with db_connect() as db:
                db.execute(
                    "DELETE FROM auth_sessions WHERE token_hash = ?",
                    (hashlib.sha256(token.encode("utf-8")).hexdigest(),),
                )
                db.commit()
        self.send_json(
            {"ok": True}, HTTPStatus.OK,
            {"Set-Cookie": self.cookie_header("", 0)},
        )

    def handle_change_password(self) -> None:
        user = self.require_user(allow_password_change=True)
        data = self.parse_body()
        current_password = str(data.get("current_password", ""))
        new_password = validate_password(data.get("new_password", ""))
        if current_password == new_password:
            raise ValueError("Новый пароль должен отличаться от текущего")
        with db_connect() as db:
            stored = db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
            if not stored or not verify_password(current_password, stored["password_hash"], stored["password_salt"]):
                raise PermissionError("Текущий пароль указан неверно")
            password_hash, password_salt = password_digest(new_password)
            db.execute(
                """UPDATE users SET password_hash = ?, password_salt = ?,
                   must_change_password = 0 WHERE id = ?""",
                (password_hash, password_salt, user["id"]),
            )
            db.commit()
            updated = db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.send_json({"ok": True, "user": public_user(updated)})

    def handle_change_phone(self) -> None:
        user = self.require_user()
        if user["role"] != "admin":
            raise PermissionError("Только администратор может изменить этот номер")
        data = self.parse_body()
        new_phone = normalize_phone(data.get("new_phone", ""))
        current_password = str(data.get("current_password", ""))
        with db_connect() as db:
            stored = db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
            if not stored or not verify_password(
                current_password, stored["password_hash"], stored["password_salt"]
            ):
                raise PermissionError("Текущий пароль указан неверно")
            try:
                db.execute("UPDATE users SET phone = ? WHERE id = ?", (new_phone, user["id"]))
            except sqlite3.IntegrityError as exc:
                raise ValueError("Этот номер телефона уже используется другой учётной записью") from exc
            db.commit()
            updated = db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.send_json({"ok": True, "user": public_user(updated)})

    def handle_reset_password(self, user_id: int) -> None:
        current = self.require_user()
        if current["role"] != "admin":
            raise PermissionError("Только администратор может сбрасывать пароли")
        password = temporary_password()
        password_hash, password_salt = password_digest(password)
        with db_connect() as db:
            target = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
            if not target:
                raise ValueError("Учётная запись не найдена")
            db.execute(
                """UPDATE users SET password_hash = ?, password_salt = ?,
                   must_change_password = 1 WHERE id = ?""",
                (password_hash, password_salt, user_id),
            )
            db.execute("DELETE FROM auth_sessions WHERE user_id = ?", (user_id,))
            db.commit()
        self.send_json({"ok": True, "temporary_password": password})

    def handle_dual_survey_import(self) -> None:
        expected = os.environ.get("LMS_BOT_INTEGRATION_TOKEN", "").strip()
        authorization = self.headers.get("Authorization", "")
        provided = authorization[7:].strip() if authorization.startswith("Bearer ") else ""
        if not expected:
            raise PermissionError("Интеграция с чат-ботом не настроена")
        if not provided or not hmac.compare_digest(provided, expected):
            raise PermissionError("Неверный ключ интеграции")
        result = import_dual_survey(self.parse_body())
        self.send_json(result, HTTPStatus.CREATED if result.get("imported") else HTTPStatus.OK)

    def send_request_error(self, exc: Exception) -> None:
        if isinstance(exc, PermissionError):
            status = HTTPStatus.FORBIDDEN if authenticated_user(self.session_token()) else HTTPStatus.UNAUTHORIZED
        else:
            status = HTTPStatus.BAD_REQUEST
        self.send_json({"error": str(exc)}, status)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json({"ok": True, "service": "CT Assembly Learning Hub", "version": APP_VERSION, "date": current_date().isoformat()})
            return
        if parsed.path == "/api/auth/session":
            user = authenticated_user(self.session_token())
            self.send_json({"authenticated": bool(user), "user": public_user(user) if user else None})
            return
        if parsed.path in {
            "/api/export/attendance.xlsx",
            "/api/export/evaluations.xlsx",
            "/api/export/accounts.xlsx",
        }:
            try:
                user = self.require_user()
                query = parse_qs(parsed.query)
                ensure_endpoint_access(user, "GET", parsed.path, query)
                body, filename = build_excel_export(parsed.path, query, user)
                self.send_download(body, filename)
            except (ValueError, PermissionError, sqlite3.Error) as exc:
                self.send_request_error(exc)
            return
        if parsed.path.startswith("/api/"):
            try:
                user = self.require_user()
                query = parse_qs(parsed.query)
                ensure_endpoint_access(user, "GET", parsed.path, query)
                payload, status = get_payload(parsed.path, query, user)
                self.send_json(payload, status)
            except (ValueError, PermissionError, sqlite3.Error) as exc:
                self.send_request_error(exc)
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/integrations/dual-survey":
                self.handle_dual_survey_import()
                return
            if path == "/api/auth/login":
                self.handle_login()
                return
            if path == "/api/auth/logout":
                self.handle_logout()
                return
            if path == "/api/auth/change-password":
                self.handle_change_password()
                return
            if path == "/api/auth/change-phone":
                self.handle_change_phone()
                return
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[:2] == ["api", "users"] and parts[3] == "reset-password":
                self.handle_reset_password(int(parts[2]))
                return
            user = self.require_user()
            data = self.parse_body()
            ensure_endpoint_access(user, "POST", path, data=data)
            data = prepare_scoped_mutation(user, "POST", path, data)
            payload, status = post_payload(path, data)
            self.send_json(payload, status)
        except (ValueError, PermissionError, KeyError, TypeError, json.JSONDecodeError, sqlite3.Error) as exc:
            self.send_request_error(exc)

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path
        try:
            user = self.require_user()
            data = self.parse_body()
            ensure_endpoint_access(user, "PATCH", path, data=data)
            data = prepare_scoped_mutation(user, "PATCH", path, data)
            payload, status = patch_payload(path, data)
            self.send_json(payload, status)
        except (ValueError, PermissionError, KeyError, TypeError, json.JSONDecodeError, sqlite3.Error) as exc:
            self.send_request_error(exc)

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        try:
            user = self.require_user()
            ensure_endpoint_access(user, "DELETE", path)
            prepare_scoped_mutation(user, "DELETE", path, {})
            payload, status = delete_payload(path)
            self.send_json(payload, status)
        except (ValueError, PermissionError, KeyError, TypeError, sqlite3.Error) as exc:
            self.send_request_error(exc)

    def serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in ("/", "") else request_path.lstrip("/")
        target = (STATIC_DIR / relative).resolve()
        if STATIC_DIR.resolve() not in target.parents and target != STATIC_DIR.resolve():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not target.is_file():
            target = STATIC_DIR / "index.html"
        body = target.read_bytes()
        mime_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if target.suffix in (".html", ".css", ".js"):
            mime_type += "; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' data: 'unsafe-inline'; "
            "script-src 'self'; img-src 'self' data:; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    reset = "--reset" in sys.argv
    init_database(reset=reset)
    host = "127.0.0.1"
    port = int(os.environ.get("PORT", "8000"))
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    for arg in sys.argv[1:]:
        if arg.startswith("--port="):
            port = int(arg.split("=", 1)[1])
        elif arg == "--host=0.0.0.0":
            host = "0.0.0.0"
    server = ThreadingHTTPServer((host, port), LMSHandler)
    print(f"CT Assembly Learning Hub запущен: http://{host}:{port}")
    print("Для остановки нажмите Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
