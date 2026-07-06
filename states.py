from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_fio = State()


class Survey(StatesGroup):

    choosing_student = State()

    confirm_student = State()

    answering = State()

    best = State()

    improve = State()

    recommendation = State()