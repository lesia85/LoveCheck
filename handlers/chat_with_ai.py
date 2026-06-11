import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database import get_user_data, add_chat_message, get_chat_history
from handlers.gemini_api import generate_text_with_gemini
from states import UserStates
from keyboards.reply import main_menu_board

router = Router()


async def get_first_ai_message_time(user_id: int) -> datetime | None:
    """Возвращает время первого сообщения ИИ из базы данных"""
    try:
        history = await get_chat_history(user_id, limit=100)
        for msg in history:
            if msg['role'] == 'ai':
                return datetime.fromisoformat(msg['timestamp'])
    except Exception as e:
        logging.error(f"Ошибка получения времени первого сообщения ИИ: {e}")
    return None


async def start_chat_with_ai(message: Message, state: FSMContext):
    user_data = await get_user_data(message.from_user.id)

    if not user_data or not user_data.get('ideal_traits'):
        await message.answer(
            "Чтобы начать чат с ИИ, сначала пройди опрос «Идеальный партнер».",
            reply_markup=main_menu_board()
        )
        await state.set_state(UserStates.main_menu)
        return

    ideal_description = user_data['ideal_traits']

    system_prompt = (
        "Твоя роль - идеальный партнер.\n"
        "Я - человек, который хочет пообщаться с идеальным партнером, то есть с тобой. "
        "Для этого был пройден тест и были выявлены характеристики партнера. Они распределены "
        "по степени важности (партнер - это ты):\n"
        f"{ideal_description}"
        "\nПожалуйста, постарайся соответствовать характеристикам. Твое общение должно быть похоже "
        "на повседневное, только если я не укажу иной стиль общения. Не будь пассивным собеседником, "
        "инициатором общения должен быть как ты, так и я."
        "Твое первое сообщение должно быть началом диалога с партнером. Ты можешь начать с вопроса. "
        "Избегай длинных сообщений (не больше 2 предложений). Избегай резких переходов от темы к теме, "
        "списков, фраз \"давай рассмотрим...\", \"понял ваш запрос...\", \"хорошо, пользователь попросил...\" "
        "и так далее. Постарайся подстроиться под мой стиль общения (шутки, стиль общения, длина предложения, "
        "знаки препинания и так далее), но не спрашивай напрямую о том, как тебе следует общаться. Не отправляй "
        "ссылки на источники. Постарайся общаться как реальный человек. Не настаивай на своей теме или вопросе, "
        "если я отказываюсь отвечать на такие вопросы, в таком случае мягко переведи тему в другую область. "
        "Общайся без привязки к полу. Не используй прозвища для партнеров. Не хвастайся , не акцентируй внимание "
        "только на себе. Старайся не использовать слова, которые бы показали какого ты пола (нужно, чтобы было "
        "не понятно, что ты женского или мужского пола: например, не \"скучал\", а \"было скучно\"). Если я "
        "тебе спрашиваю о рецепте, прошу совет, хочу чтобы ты дал какую-то информацию, то не пиши свой ответ "
        "как инструкцию с ссылками на источники, постарайся ответить как-будто у человека спросили и он "
        "отвечает основываясь на своем опыте (например: -как приготовить шашлык? -Думаю было бы классно "
        "приготовить говядину в маринаде). Не пиши о том, что твои сообщения соответствуют требованиям, "
        "ты должен присылать только то сообщения, которое относиться к диалогу со мной."
    )

    await state.update_data(system_prompt=system_prompt)
    await state.set_state(UserStates.chat_with_ai)

    await message.answer(
        "\t⚠️ <b>Внимание</b>\n\n"
        "Чат с твоим идеальным партнером будет доступен <b>в течение 1 часа</b> "
        "с момента первого сообщения нейросети.\n"
        "После окончания времени чат автоматически завершится.",
        parse_mode="HTML",
        reply_markup=main_menu_board()
    )


def is_chat_expired(start_time: datetime | None) -> bool:
    if not start_time:
        return False
    return datetime.now() > start_time + timedelta(hours=1)


@router.message(StateFilter(UserStates.chat_with_ai))
async def handle_chat_message(message: Message, state: FSMContext):
    data = await state.get_data()
    system_prompt = data.get("system_prompt", "")

    # Получаем время первого сообщения ИИ из БД
    first_ai_time = await get_first_ai_message_time(message.from_user.id)

    if first_ai_time and is_chat_expired(first_ai_time):
        await message.answer(
            "⏰ Время чата истекло (прошло больше 1 часа).\nЧат завершен.",
            reply_markup=main_menu_board()
        )
        await state.set_state(UserStates.main_menu)
        return

    current_message = message.text

    # === Промпт только с текущим сообщением пользователя ===
    full_prompt = (
        f"{system_prompt}\n\n"
        f"Пользователь: {current_message}\n"
        f"Твой ответ:"
    )

    try:
        ai_response = await generate_text_with_gemini(full_prompt)

        # Если это первое сообщение ИИ — сохраняем его в БД
        if not first_ai_time:
            await add_chat_message(
                user_id=message.from_user.id,
                message_text=ai_response,
                role="ai",
                mark_like=0,
                mark_mission_complete=0
            )

        await message.answer(ai_response)

    except Exception as e:
        logging.error(f"Ошибка в чате: {e}")
        await message.answer("Извини, не могу ответить сейчас. Попробуй позже.")