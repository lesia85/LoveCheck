import logging
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database import save_or_update_user
from handlers.gemini_api import generate_image_with_gemini, generate_text_with_gemini
from handlers.main_menu import main_menu
from states import UserStates
from keyboards.reply import get_rating_keyboard_ideal_partner, main_menu_board
from handlers.gigachat_api import generate_image_with_gigachat, generate_text_with_gigachat

router = Router()

QUESTIONS = [
    "Поддерживающий", "Заботливый", "Жизнерадостный", "Имеет высокий доход",
    "Верный", "Имеет привлекательную внешность", "Тактичный", "Честный",
    "Любознательный", "Образованный", "Коммуникабельный", "Внимательный",
    "Любящий", "Обладающий широким кругозором", "Надежный",
    "Имеет высокий социальный статус"
]

OPEN_QUESTIONS = ["Цвет волос", "Цвет глаз", "Этническая принадлежность"]

TOTAL_QUESTIONS = len(QUESTIONS) + len(OPEN_QUESTIONS)

def get_progress(current: int) -> str:
    return f"Вопрос {current}/{TOTAL_QUESTIONS}"


async def start_ideal_partner_survey(message: Message, state: FSMContext):
    await state.update_data(ideal_answers={}, current_question=0, open_index=0)
    await ask_next_question(message, state)


async def ask_next_question(message: Message, state: FSMContext):
    """Задает следующий вопрос"""
    data = await state.get_data() #
    q_index = data.get("current_question", 0)

    if q_index < len(QUESTIONS):
        # закрытые вопросы (оценка 1-7)
        question = QUESTIONS[q_index]
        await message.answer(
            f"{get_progress(q_index + 1)}\n\n"
            f"Насколько важно, чтобы идеальный партнер был:\n\n"
            f"\t{question}?",
            parse_mode="HTML",
            reply_markup=get_rating_keyboard_ideal_partner()
        )
    else:
        # открытые вопросы
        await ask_open_question(message, state)


async def ask_open_question(message: Message, state: FSMContext):
    """Задает открытый вопрос и скрывает клавиатуру с цифрами"""
    data = await state.get_data()
    open_index = data.get("open_index", 0)

    if open_index < len(OPEN_QUESTIONS):
        question = OPEN_QUESTIONS[open_index]
        await message.answer(
            f"{get_progress(len(QUESTIONS) + open_index + 1)}\n\n"
            f"{question} идеального партнера?\n\n"
            f"Напишите ответ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()  # <-- Скрываем панель с кнопками-цифрами
        )
    else:
        await finish_ideal_survey(message, state)


@router.message(StateFilter(UserStates.survey_ideal_partner))
async def process_ideal_partner_input(message: Message, state: FSMContext):
    """Единый хэндлер для обработки всех ответов в опросе идеального партнера"""
    data = await state.get_data()
    q_index = data.get("current_question", 0)

    # обработка закрытые вопросы
    if q_index < len(QUESTIONS):
        valid_ratings = {"1", "2", "3", "4", "5", "6", "7"}
        
        # корректная цифра
        if message.text in valid_ratings:
            rating = int(message.text)
            answers = data.get("ideal_answers", {})
            answers[QUESTIONS[q_index]] = rating

            await state.update_data(ideal_answers=answers, current_question=q_index + 1)
            await ask_next_question(message, state)
            
        # неправильный ввод
        else:
            await message.answer("Пожалуйста, выберите оценку от 1 до 7 с помощью кнопок.")
            await ask_next_question(message, state)  # повтор текущего вопроса отдельным сообщением

    # обработка открытых вопросов 
    else:
        open_index = data.get("open_index", 0)

        if open_index < len(OPEN_QUESTIONS):
            answers = data.get("ideal_answers", {})
            answers[OPEN_QUESTIONS[open_index]] = message.text.strip()

            await state.update_data(ideal_answers=answers, open_index=open_index + 1)
            await ask_open_question(message, state)

@router.message(StateFilter(UserStates.survey_ideal_partner))
async def process_open_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    answers = data.get("ideal_answers", {})
    open_index = data.get("open_index", 0)

    answers[OPEN_QUESTIONS[open_index]] = message.text.strip()

    await state.update_data(ideal_answers=answers, open_index=open_index + 1)
    await ask_open_question(message, state)
    

async def finish_ideal_survey(message: Message, state: FSMContext):
    answers = (await state.get_data()).get("ideal_answers", {})

    # Разделение по важности (остается без изменений)
    very_important, important, not_important, not_important_at_all = [], [], [], []
    for trait, score in answers.items():
        if isinstance(score, int):
            if score == 7: very_important.append(trait)
            elif score in (5, 6): important.append(trait)
            elif score in (2, 3): not_important.append(trait)
            elif score in (1, 4): not_important_at_all.append(trait)

    hair = answers.get("Цвет волос", "не указан")
    eyes = answers.get("Цвет глаз", "не указан")
    ethnicity = answers.get("Этническая принадлежность", "не указан")

    # промпт для текстовой интерпритации
    text_prompt = (
        "Тебе необходимо составить краткое текстовое описание партнера по приведенным ниже качествам. "
        "Учитывай важность характеристик партнера. Напиши цельный текст, не выделяя пункты. "
        "Начни свой ответ со слов: \"Вы представляете своего идеального партнера как\". "
        "Избегай простого перечисления характеристик подряд. Также избегай научный стиль речи. "
        "При описании используй нейтральные слова (без пола), например - партнер. "
        "Описание должно содержать от пяти до семи предложений без повторения написанной информации.\n"
        f"Очень важно: {', '.join(very_important)}\n"
        f"Важно: {', '.join(important)}\n"
        f"Не важно: {', '.join(not_important)}\n"
        f"Совсем не важно: {', '.join(not_important_at_all)}\n"
        f"Цвет волос: {answers.get('Цвет волос')}, Цвет глаз: {answers.get('Цвет глаз')}, Этнос: {answers.get('Этническая принадлежность')}"
    )

    # промпт для изображения
    img_prompt = ("Ты должен создать одно изображение идеальных партнеров по одному описанию и отправить "
              "только картинку без дополнительного текста, в котором сообщается о выполненном задании:\n"
              "На левой половине изображения Мужчина 25 лет, а на правой половине изображения Женщина "
              "25 лет. Изображения не должны накладываться друг на друга. Чтобы они не выглядели как единое фото, "
              "добавь разделяющую линии между половинами изображения. Оба человека должны быть в расслабленной "
              "позе стоя и смотреть прямо, в анфас, быть обязательно в повседневной одежде и обуви. "
              "Люди на изображениях должны быть полностью одетыми. Рост людей на изображении должен быть средним. "
              "Изображение должно быть прямое. Добавь подходящий под описание изображения фон.\n"
              "Важно, чтобы люди на изображениях отображали следующие качества и характеристики. "
              "Ты можешь создавать фон, чтобы указать на очень важные и важные качества. Важно, чтобы люди стояли на полу.\n"
        )
    
    if very_important:
        img_prompt += f"Очень важно: {', '.join(very_important)}\n"
        text_prompt += f"Очень важно: {', '.join(very_important)}\n"
    if important:
        img_prompt += f"Важно: {', '.join(important)}\n"
        text_prompt += f"Очень важно: {', '.join(very_important)}\n"
    if not_important:
        img_prompt += f"Не важно: {', '.join(not_important)}\n"
        text_prompt += f"Очень важно: {', '.join(very_important)}\n"
    if not_important_at_all:
        img_prompt += f"Совсем не важно: {', '.join(not_important_at_all)}\n"
        text_prompt += f"Очень важно: {', '.join(very_important)}\n"

    img_prompt += f"\nЦвет волос: {hair}\nЦвет глаз: {eyes}\nЭтническая принадлежность: {ethnicity}"
    text_prompt += f"\nЦвет волос: {hair}\nЦвет глаз: {eyes}\nЭтническая принадлежность: {ethnicity}"

    await message.answer("Изображение вашего идеального партнера генерируется...")

    try:
        # Генерация только текста
        text_desc = await generate_text_with_gemini(text_prompt)
        await message.answer(text_desc, parse_mode="HTML")
        
        # Сохранение текста в БД
        await save_or_update_user(message.from_user.id, {"ideal_traits": text_desc})
        
    except Exception as e:
        logging.error(f"Ошибка при завершении опроса: {e}")
        await message.answer("Произошла ошибка при составлении описания. Попробуйте еще раз позже.")

    await state.set_state(UserStates.main_menu)
    await save_or_update_user(message.from_user.id, {"state": "main_menu"})
    await message.answer("Вы вернулись в главное меню.", reply_markup=main_menu_board())