from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from states import UserStates
from keyboards.reply import main_menu_board


async def get_about_project_text() -> str:
    """Возвращает текст раздела «О проекте»."""
    text = (
        "<b>О проекте</b> ℹ️\n\n"
        "Данный бот является научно-исследовательским инструментом, "
        "разработанным студентами образовательной программы "
        "<b>«Разработка информационных систем для бизнеса»</b> "
        "НИУ ВШЭ Пермь в рамках курсового проекта 1 курса.\n\n"

        "<b>Цели проекта</b> 🎯\n"
        "Помочь вам объективно оценить текущие отношения и личный комфорт, "
        "а также проверить, может ли нейросеть воссоздать образ «идеального партнера» "
        "и поддерживать с ним осмысленный диалог.\n\n"

        "<b>Методика исследования</b> 🔬\n"
        "В основе лежат два опросника:\n"
        "• Триангулярная теория любви Стернберга (TLS-15)\n"
        "• Опросник черт идеального партнера (IPRS)\n\n"
        "Для генерации текстовых интерпретаций используется нейросеть <b>Gemini</b>.\n\n"

        "<b>Поддержка</b> 💬\n"
        "Заметили ошибку или есть вопрос?\n"
        "Заполните форму, мы обязательно ее рассмотрим: <b>ссылка на гугл форму</b>"
    )
    return text


async def send_about_project(message: Message, state: FSMContext):
    """Отправляет раздел «О проекте»"""
    text = await get_about_project_text()
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_board())
    await state.set_state(UserStates.main_menu)