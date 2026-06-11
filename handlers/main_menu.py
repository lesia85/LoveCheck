from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from database import save_or_update_user
from handlers.all_results import get_user_results
from handlers.chat_with_ai import start_chat_with_ai
from states import UserStates
from keyboards.reply import main_menu_board
from handlers.about_project import send_about_project

router = Router()

async def main_menu(message: Message, warning: str = None):
    """
    Отправляет приветственное сообщение главного меню ОДИН раз и закрепляет его.
    Если передан warning, отправляет его отдельным обычным сообщением.
    """
    if warning:
        await message.answer(f"<b>{warning}</b>", parse_mode="HTML")
        return

    text = (
        "Вы сейчас на главном меню, можете выбрать одну из опций:\n\n"
        "• <b>Удовлетворенность отношениями</b> - опрос о ваших взаимоотношениях с партнером\n"
        "• <b>Идеальный партнер</b> - опрос о чертах характера и внешности человека, которого хотели бы видеть рядом\n"
        "• <b>Чат с ИИ</b> - чат с вашим идеальным партнером (доступен после прохождения опроса \"Идеальный партнер\")\n"
        "• <b>Мои результаты</b> - вывод одним сообщением всех результатов пройденных вами опросов\n"
        "• <b>О проекте</b> - описание проекта, его цели, источники и связь с поддержкой"
    )
    
    # сообщение меню
    sent_message = await message.answer(text, parse_mode="HTML", reply_markup=main_menu_board())
    
    try:
        # сообщение главного меню закрепляется
        await sent_message.pin(disable_notification=True)
    except Exception as e:
        import logging
        logging.warning(f"Не удалось закрепить сообщение (возможно, у бота нет прав): {e}")


@router.message(StateFilter(UserStates.main_menu), F.text == "Удовлетворенность отношениями")
async def go_to_satisfaction_survey(message: Message, state: FSMContext):
    await state.set_state(UserStates.survey_satisfaction)
    await save_or_update_user(message.from_user.id, {"state": "survey_satisfaction"})
    from .satisfaction import start_satisfaction_survey
    await start_satisfaction_survey(message, state)


@router.message(StateFilter(UserStates.main_menu), F.text == "Идеальный партнер")
async def go_to_ideal_partner_survey(message: Message, state: FSMContext):
    await state.set_state(UserStates.survey_ideal_partner)
    await save_or_update_user(message.from_user.id, {"state": "survey_ideal_partner"})
    from .ideal_partner import start_ideal_partner_survey
    await start_ideal_partner_survey(message, state)


@router.message(StateFilter(UserStates.main_menu), F.text == "Чат с ИИ")
async def go_to_chat_with_ai(message: Message, state: FSMContext):
    await start_chat_with_ai(message, state)


@router.message(StateFilter(UserStates.main_menu), F.text == "Мои результаты")
async def go_to_my_results(message: Message, state: FSMContext):
    """Хэндлер кнопки «Мои результаты»"""
    result_text = await get_user_results(message.from_user.id)
    await message.answer(result_text, parse_mode="HTML", reply_markup=main_menu_board())
    await state.set_state(UserStates.main_menu)


@router.message(StateFilter(UserStates.main_menu), F.text == "О проекте")
async def go_to_about_project(message: Message, state: FSMContext):
    await send_about_project(message, state)


@router.message(StateFilter(UserStates.main_menu))
async def unknown_in_main_menu(message: Message):
    await main_menu(message, warning="Пожалуйста, используйте кнопки меню ниже.")