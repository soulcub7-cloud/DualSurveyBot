from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    choosing_role = State()
    waiting_for_fio = State()
    choosing_student_stream = State()
    choosing_student = State()


class Survey(StatesGroup):

    choosing_stream = State()

    choosing_student = State()

    choosing_enterprise = State()

    confirm_student = State()

    answering = State()

    best = State()

    improve = State()

    recommendation = State()


class MentorFeedback(StatesGroup):
    choosing_mentor = State()
    entering_module = State()
    confirming = State()
    answering = State()
    open_answer = State()
