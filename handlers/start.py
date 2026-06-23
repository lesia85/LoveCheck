from aiogram import Router
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.media_group import MediaGroupBuilder
import aiosqlite
import logging
import os
from config import DATABASE_NAME
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from states import UserStates
from keyboards.reply import main_menu_board

router = Router()

@router.message(Command("start"))
async def button_start(message: Message, state: FSMContext):
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    try:
        user_id = message.from_user.id

        async with aiosqlite.connect(DATABASE_NAME) as db:
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()

        # 1 - подтверждение согласия, 3 - результаты "удовлетворенности отношениями" 4 - результаты "идеальный партнер"
        if result and result[1] == 1:  # пользователь уже давал согласие
            text = (
                "Ранее вы приняли согласие. Рады, что вы вернулись.\n"
            )
            
            if result[3] is None and result[4] is None:  # нет результатов ни по одному опросу 
                text += "У вас еще не записано ни одного результата по опросам, сейчас вы можете начать любой из опросов."
            else:
                text += ( 
                "Вы уже проходили опрос(-ы), вы можете посмотреть свои предыдущие результаты или перепройти опрос(-ы).\n" \
                "ВАЖНО: ваши предыдущие результаты при перепрохождении будут удалены и заменены новыми."
                    )
            await message.answer(
                text,
                reply_markup=main_menu_board()
            )
            await state.set_state(UserStates.main_menu)
            return
        else:
            #Отправка двух пдф файлов
            BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) # передача пути к файлу, т.к. не лежат в корне проекта
            privacy_path = os.path.join(BASE_DIR, "privacy_policy.pdf")
            consent_path = os.path.join(BASE_DIR, "consent.pdf")

            # проверка наличия файлов
            if not os.path.exists(privacy_path):
                logging.error(f"Файл не найден: {privacy_path}")
                await message.answer("Ошибка: не найден файл политики конфиденциальности.")
                await state.set_state(UserStates.error)
                return

            if not os.path.exists(consent_path):
                logging.error(f"Файл не найден: {consent_path}")
                await message.answer("Ошибка: не найден файл согласия.")
                await state.set_state(UserStates.error)
                return

            media = MediaGroupBuilder() # группа медиафайлов (отправка файлов в 1 сообщении)

            media.add_document(FSInputFile(privacy_path), caption="Политика конфиденциальности") # добавление файла в группу с подписью
            media.add_document(FSInputFile(consent_path), caption="Информированное добровольное согласие")

            await message.answer_media_group(media.build())
            
            #Формирование inline кнопок
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Согласен ✅", callback_data="agree"),
                        InlineKeyboardButton(text="Не согласен ❌", callback_data="disagree")
                    ]
                ]
            )

            #Отправка сообщения 
            await message.answer(
                "Для продолжения работы с ботом, вам нужно прочитать политику конфиденциальности " \
                "и информированное добровольное согласие. Нажимая кнопку “Согласен”, вы подтверждаете, " \
                "что полностью прочли документы и соглашаетесь с их условиями",
                reply_markup = keyboard
            )

            await state.set_state(UserStates.waiting_for_consent)

    except Exception as e:
        logging.error(f"Произошла ошибка при обработке команды /start: {e}")
        await state.set_state(UserStates.error)

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "Столкнулись с ошибкой?\n\n"
        "Напишите об этом нам в форму:\n<b>https://forms.gle/HQwUZ2hYwaxmoDLU7</b>\n"
        "Обязательно подробно объясните вашу проблему. "
        "Мы постараемся в скором времени ее исправить"
    )
    await message.answer(help_text, parse_mode="HTML")