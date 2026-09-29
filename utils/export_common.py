import json
import re

from database import load_survey_questions
from questions import get_questionnaire_title, score_summary


def unpack_survey(data):
    answers = json.loads(data[7]) if isinstance(data[7], str) else list(data[7] or [])
    questionnaire_key = data[12] if len(data) > 12 and data[12] else "legacy"
    questions_json = data[13] if len(data) > 13 else None
    questions = load_survey_questions(questionnaire_key, questions_json)
    summary = score_summary(questions, answers)
    hard_average = data[14] if len(data) > 14 and data[14] is not None else summary["hard_average"]
    soft_average = data[15] if len(data) > 15 and data[15] is not None else summary["soft_average"]
    suitability_score = data[16] if len(data) > 16 and data[16] is not None else summary["suitability_score"]

    return {
        "id": data[0],
        "date": data[1],
        "student": data[2],
        "speciality": data[3] or "-",
        "course": data[4] or "-",
        "enterprise": data[5] or "-",
        "mentor": data[6],
        "answers": answers,
        "average": float(data[8] or 0),
        "best": data[9] or "-",
        "improve": data[10] or "-",
        "recommendation": data[11] or "-",
        "questionnaire_key": questionnaire_key,
        "questionnaire_title": get_questionnaire_title(questionnaire_key),
        "questions": questions,
        "hard_average": hard_average,
        "soft_average": soft_average,
        "suitability_score": suitability_score,
        "responses": [
            {**question, "score": int(score)}
            for question, score in zip(questions, answers)
        ],
    }


def safe_filename(value):
    return re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9_.-]+", "_", str(value)).strip("_")
