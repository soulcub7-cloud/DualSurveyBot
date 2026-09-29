from questions import SECTION_TITLES, get_questions


def get_question(questionnaire_key, index):
    questions = get_questions(questionnaire_key)
    return questions[index]


def format_question(questionnaire_key, question_index):
    questions = get_questions(questionnaire_key)
    question = questions[question_index]
    total = len(questions)
    current = question_index + 1
    percent = int(current / total * 100)
    filled = round(current / total * 10)
    progress = "🟩" * filled + "⬜" * (10 - filled)
    section = SECTION_TITLES.get(question.get("section"), "Оценка")

    return (
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 <b>Анкета наставника</b>\n\n"
        f"Раздел: <b>{section}</b>\n"
        f"Вопрос <b>{current}</b> из <b>{total}</b>\n\n"
        f"{progress}\n"
        f"{percent}%\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{question['text']}</b>\n\n"
        "1 — не проявляется · 2 — слабо · 3 — удовлетворительно\n"
        "4 — хорошо · 5 — отлично"
    )
