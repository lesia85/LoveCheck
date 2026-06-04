from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

"""Файл со всеми клавиатурами для каждого состояния"""

def main_menu_board():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Удовлетворенность отношениями")],
                  [KeyboardButton(text="Идеальный партнер")],
                  [KeyboardButton(text="Чат с ИИ")],
                  [KeyboardButton(text="Мои результаты"),
                  KeyboardButton(text="О проекте")]],
                resize_keyboard=True, # подбор высоты панели под количество кнопок
                one_time_keyboard=False, # панель не скрывается после нажатия
                is_persistent=True # запрет сворачивать/прятать меню
    )

def get_rating_keyboard_ideal_partner():
    return ReplyKeyboardMarkup(
        keyboard = [[KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
                    [KeyboardButton(text="4"), KeyboardButton(text="5"), KeyboardButton(text="6")],
                    [KeyboardButton(text="7")]],
                    resize_keyboard=True,
                    one_time_keyboard=False
    )

def get_rating_keyboard_by_5():
    return ReplyKeyboardMarkup(
        keyboard = [[KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
                    [KeyboardButton(text="4"), KeyboardButton(text="5")]],
                    resize_keyboard=True,
                    one_time_keyboard=False
    )