from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
import logging
from states import UserStates
from database import save_or_update_user
from handlers.main_menu import main_menu
from states import UserStates

router = Router()

# инициализация роутера для обработчика inline-кнопок. подключение состояния (ожидание согласия)
# и передача значений "agree"/"disagree" (выбор пользователя)
@router.callback_query(UserStates.waiting_for_consent, F.data.in_({"agree", "disagree"})) 
async def process_buttons(callback: CallbackQuery, state: FSMContext):
    """Обработчик inline-кнопок. Обработка согласие/отказ пользователя."""
    try:
        user_id = callback.from_user.id
        data = callback.data

        # если ползователь выбрал согласие
        if data == "agree":
            await save_or_update_user(user_id, {"is_consented": 1, "state": "main_menu"})

            await callback.message.edit_text(
                "Спасибо! Ваши согласия были приянты, и теперь вы можете ознакомиться со всеми разделами.\nВ следующем сообщении будет полное описание разделов."
            )
            await state.set_state(UserStates.main_menu)
            await main_menu(callback.message)# переход в главное меню

        # если отказался
        elif data == "disagree":
            await save_or_update_user(user_id, {"is_consented": 0, "state": "start"})

            await callback.message.edit_text(
                "К сожалению, без вашего согласия проведение исследования невозможно. Вы можете вернуться к боту в любое время, снова введя команду /start"
            )

            await state.set_state(UserStates.start) # остается в состоянии старта (без доступа к функционалу)
        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка при обработке inline-кнопок: {e}")
        await state.set_state(UserStates.error)