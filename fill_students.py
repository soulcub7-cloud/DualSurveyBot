from openpyxl import load_workbook

from database import (
    add_student,
    delete_missing_students
)

FILE_NAME = "students.xlsx"

wb = load_workbook(FILE_NAME)
ws = wb.active

added = 0
updated = 0
actual_students = []

for row in ws.iter_rows(min_row=2, values_only=True):

    if not row[0]:
        continue

    try:
        fio = str(row[0]).strip()
        actual_students.append(fio)
        speciality = str(row[1]).strip()
        course = int(row[2])
        enterprise = str(row[3]).strip()

        if add_student(
            fio,
            speciality,
            course,
            enterprise
        ):
            added += 1
            print(f"➕ Добавлен: {fio}")
        else:
            updated += 1
            print(f"🔄 Обновлен: {fio}")

    except Exception as e:
        print(f"Ошибка в строке: {row}")
        print(e)

deleted = delete_missing_students(actual_students)
print("=" * 50)
print(f"➕ Добавлено: {added}")
print(f"🔄 Обновлено: {updated}")
print(f"🗑 Удалено: {deleted}")
print("✅ Синхронизация завершена")
print("=" * 50)