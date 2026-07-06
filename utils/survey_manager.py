from questions import QUESTIONS


def get_question(index):

    return (
        f"<b>Вопрос {index + 1} из {len(QUESTIONS)}</b>\n\n"
        f"{QUESTIONS[index]}"
    )
def format_question(question_index):

    total = len(__import__("questions").QUESTIONS)

    current = question_index + 1

    percent = int(current / total * 100)

    filled = round(current / total * 10)

    progress = "🟩" * filled + "⬜" * (10 - filled)

    return (
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 <b>Анкета наставника</b>\n\n"
        f"Вопрос <b>{current}</b> из <b>{total}</b>\n\n"
        f"{progress}\n"
        f"{percent}%\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{get_question(question_index)}"
    )