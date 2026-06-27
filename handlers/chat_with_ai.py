import logging
from datetime import datetime, timedelta
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database import add_chat_message, get_user_data
from handlers.gemini_api import generate_text_with_gemini
from states import UserStates
from keyboards.reply import get_rating_keyboard_by_5, main_menu_board
from google.genai import types

router = Router()

import re

def _md_bold_to_html(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    return text

IMPRESSION_QUESTIONS = [
    "Насколько вам понравилось общение с ии?\n\n"
    "Ответ дайте по шкале от 1 до 5, где\n"
    "1 — вообще не понравилось\n5 — очень понравилось",

    "Насколько ии справился с ролью идеального партнера?\n\n"
    "Ответ дайте по шкале от 1 до 5, где\n"
    "1 — у него вообще не получилось стать \"идеальным партнером\"\n"
    "5 — он отлично справился с этой ролью"
]

TOTAL_IMPRESSION_QUESTIONS = len(IMPRESSION_QUESTIONS)


def get_impression_progress(current: int) -> str:
    return f"Вопрос {current}/{TOTAL_IMPRESSION_QUESTIONS}"


async def ask_impression_question(message: Message, state: FSMContext):
    data = await state.get_data()
    q_index = data.get("current_impression_question", 0)

    if q_index < TOTAL_IMPRESSION_QUESTIONS:
        question = IMPRESSION_QUESTIONS[q_index]
        try:
            await message.edit_reply_markup(reply_markup=None)
        except:
            pass

        await message.answer(
            f"<b>{get_impression_progress(q_index + 1)}</b>\n{question}",
            parse_mode="HTML",
            reply_markup=get_rating_keyboard_by_5()
        )
    else:
        await finish_impression_survey(message, state)


async def finish_impression_survey(message: Message, state: FSMContext):
    thank_you_text = (
        "Еще раз благодарим вас за участие и обратную связь 🙏\n\n"
        "Если вы хотите рассказать подробнее про ваши впечатления общения с \"идеальным партнером\", "
        "то можете это сделать в Google формах:\n"
        "<b>https://forms.gle/siieKkatG4eCunVW9</b>"
    )

    await message.answer(thank_you_text, parse_mode="HTML", reply_markup=main_menu_board())
    await state.set_state(UserStates.main_menu)

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

    chat_start_time = datetime.now()
    await state.update_data(
        system_prompt=system_prompt,
        chat_start_time=chat_start_time,
        chat_history=[],
        system_instruction_sent=False
    )
    await state.set_state(UserStates.chat_with_ai)

    await message.answer(
        "📌 <b>Внимание</b>\n\n"
        "Чат с твоим идеальным партнером будет доступен <b>в течение 1 часа</b> "
        "с момента первого сообщения нейросети.\n"
        "После окончания времени чат автоматически завершится.\n\n"
        "<i>Этот чат временный. История сообщений не сохраняется.</i>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

    first_prompt = (
        "Сейчас ты отправляешь САМОЕ ПЕРВОЕ сообщение в этом диалоге, "
        "которое должно начинаться с приветствия. "
        "Начни разговор естественно и тепло. Можешь задать лёгкий вопрос. "
        "Не упоминай, что это первое сообщение. Не используй любые списки. " \
        "Пиши обычным текстом без слэшей. Не заканчивай разговор или не "
        "заводи разговор в тупиковую сидуацию, когда пользователь не знает, "
        "что тебе ответить."
    )

    try:
        first_ai_message = await generate_text_with_gemini(
            prompt=first_prompt,
            system_instruction=system_prompt
        )

        safe_text = _md_bold_to_html(first_ai_message)
        await message.answer(f"{safe_text}", parse_mode="HTML")

        # сохранение первого сообщения ии
        await add_chat_message(
            user_id=message.from_user.id,
            message_text=first_ai_message,
            role="model",
            mark_like=0,
            mark_mission_complete=0
        )

    except Exception as e:
        logging.error(f"Ошибка генерации первого сообщения ИИ: {e}")
        await message.answer("Не получилось начать чат. Попробуйте позже.", reply_markup=main_menu_board())
        await state.set_state(UserStates.main_menu)


def is_chat_expired(start_time: datetime | None) -> bool:
    if not start_time:
        return False
    return datetime.now() > start_time + timedelta(minutes=60)


@router.message(StateFilter(UserStates.chat_with_ai))
async def handle_chat_message(message: Message, state: FSMContext):
    data = await state.get_data()
    system_prompt = data.get("system_prompt", "")
    chat_start_time = data.get("chat_start_time")
    chat_history: list = data.get("chat_history", [])
    system_instruction_sent = data.get("system_instruction_sent", False)

    # Проверка на истечение времени чата
    if chat_start_time and is_chat_expired(chat_start_time):
        
        #сохранение в бд
        if chat_history:
            last_msg = chat_history[-1]
            last_text = last_msg.parts[0].text if last_msg.parts else ""
            last_role = last_msg.role  # user или model

            await add_chat_message(
                user_id=message.from_user.id,
                message_text=last_text,
                role=last_role,
                mark_like=0,
                mark_mission_complete=0
            )
        
        await message.answer(
            "К сожалению, время общения с нейросетью вышло...\n"
            "Благодарим вас за участие в эксперименте. Хотели бы получить от вас обратную связь, для этого ответьте на 2 вопроса",
            parse_mode="HTML"
        )
        await state.update_data(impression_answers=[], current_impression_question=0)
        await state.set_state(UserStates.survey_impression)
        await ask_impression_question(message, state)
        return

    current_message = message.text

    await add_chat_message(
        user_id=message.from_user.id,
        message_text=current_message,
        role="user",
        mark_like=0,
        mark_mission_complete=0
    )

    # добавление сообщения пользователя в историю
    chat_history.append(
        types.Content(role="user", parts=[types.Part.from_text(text=current_message)])
    )

    # последние 6 сообщений для контекста
    recent_history = chat_history[-6:]

    anti_repeat_instruction = (
        "Не приветствуй пользователя еще раз. Продолжай разговор естественно, как обычный человек. " \
        "Не пересказывай и не повторяй то, что уже говорилось в диалоге. " \
        "Отвечай коротко и по делу. Не начинай сообщение с перефразирования слов пользователя. " \
        "Не используй любые списки. Пиши обычным текстом без выделений слов и слэшей. " \
        "Не заканчивай разговор или не заводи разговор в тупиковую сидуацию, " \
        "когда пользователь не знает, что тебе ответить. Не пиши сообщение больше, чем " \
        "2 преложения, диалог должен быть похож на общение двух людей. Старайся адаптироваться " \
        "под стиль пользователя и его объем напсиания сообщений."
    )

    try:
        if not system_instruction_sent:
            ai_response = await generate_text_with_gemini(
                prompt=None,
                system_instruction=system_prompt + "\n\n" + anti_repeat_instruction,
                contents=recent_history
            )
            await state.update_data(system_instruction_sent=True)
        else:
            ai_response = await generate_text_with_gemini(
                prompt=None,
                system_instruction=anti_repeat_instruction,
                contents=recent_history
            )

        safe_text = _md_bold_to_html(ai_response)
        await message.answer(f"{safe_text}", parse_mode="HTML")

        await add_chat_message(
            user_id=message.from_user.id,
            message_text=ai_response,
            role="model",
            mark_like=0,
            mark_mission_complete=0
        )

        # Добавляем ответ ИИ в историю
        chat_history.append(
            types.Content(role="model", parts=[types.Part.from_text(text=ai_response)])
        )
        await state.update_data(chat_history=chat_history)

    except Exception as e:
        logging.error(f"Ошибка в чате: {e}")
        await state.set_state(UserStates.main_menu)
        await message.answer(
            "Извините, нейросеть не может ответить сейчас, возникли ошибка при генерации ответа. Попробуйте позже. 🙏",
            reply_markup=main_menu_board()
        )

# вопросы после общения с ИИ
@router.message(StateFilter(UserStates.survey_impression))
async def process_impression_rating(message: Message, state: FSMContext):
    data = await state.get_data()
    q_index = data.get("current_impression_question", 0)

    if message.text not in {"1", "2", "3", "4", "5"}:
        await message.answer("Пожалуйста, выберите оценку от 1 до 5 с помощью кнопок.")
        await ask_impression_question(message, state)
        return

    rating = int(message.text)

    if q_index == 0:
        # первый вопрос после чата с ИИ
        await add_chat_message(
            user_id=message.from_user.id,
            message_text="",
            role="",
            mark_like=rating,
            mark_mission_complete=0
        )

        await state.update_data(current_impression_question=1, mark_like=rating)
        await ask_impression_question(message, state)

    else:
        # второй вопрос
        mark_like = data.get("mark_like", 0)

        await add_chat_message(
            user_id=message.from_user.id,
            message_text="",
            role="",
            mark_like=mark_like,
            mark_mission_complete=rating
        )

        await finish_impression_survey(message, state)