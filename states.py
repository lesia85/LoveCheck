from aiogram.fsm.state import StatesGroup, State


class UserStates(StatesGroup):
    """Конечный автомат состояний Telegram-бота"""
    start = State()
    waiting_for_consent = State()
    main_menu = State()
    survey_satisfaction = State()
    survey_ideal_partner = State()
    generating_portrait = State()
    chat_with_ai = State()
    survey_impression = State()
    view_results = State()
    error = State()

# Дополнительные группы состояний (если понадобятся в будущем)
class SurveyStates(StatesGroup):
    """Состояния для прохождения опросов"""
    waiting_for_answer = State()