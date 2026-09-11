"""Non-blocking integration with CT Assembly Learning Hub."""

import asyncio
import json
from urllib import error, request

from config import LMS_API_URL, LMS_BOT_INTEGRATION_TOKEN
from database import get_surveys_for_lms_sync


def integration_enabled():
    return bool(LMS_API_URL and LMS_BOT_INTEGRATION_TOKEN)


def _post_survey(payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        f"{LMS_API_URL}/api/integrations/dual-survey",
        data=body,
        headers={
            "Authorization": f"Bearer {LMS_BOT_INTEGRATION_TOKEN}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(message).get("error", message)
        except json.JSONDecodeError:
            pass
        raise RuntimeError(f"LMS вернула ошибку {exc.code}: {message}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"LMS недоступна: {exc.reason}") from exc


async def sync_survey(survey_id):
    if not integration_enabled():
        return False
    surveys = get_surveys_for_lms_sync(survey_id)
    if not surveys:
        return False
    try:
        result = await asyncio.to_thread(_post_survey, surveys[0])
        state = "импортирована" if result.get("imported") else "уже была импортирована"
        print(f"LMS: анкета #{survey_id} {state}")
        return True
    except Exception as exc:
        print(f"LMS: анкета #{survey_id} пока не синхронизирована: {exc}")
        return False


async def sync_all_surveys():
    if not integration_enabled():
        return {"enabled": False, "sent": 0, "failed": 0}
    sent = 0
    failed = 0
    for survey in get_surveys_for_lms_sync():
        try:
            await asyncio.to_thread(_post_survey, survey)
            sent += 1
        except Exception as exc:
            failed += 1
            print(f"LMS: анкета #{survey['survey_id']} пока не синхронизирована: {exc}")
    print(f"LMS: проверка анкет завершена — успешно {sent}, ошибок {failed}")
    return {"enabled": True, "sent": sent, "failed": failed}


async def periodic_lms_sync(interval_seconds=900):
    """Retry all saved surveys; the LMS ignores duplicates by survey ID."""
    if not integration_enabled():
        print("LMS: синхронизация отключена — переменные Railway не заданы")
        return
    while True:
        await sync_all_surveys()
        await asyncio.sleep(interval_seconds)
