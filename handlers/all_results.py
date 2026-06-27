from aiogram import Router
from database import get_user_data

router = Router()


async def get_user_results(user_id: int) -> str:
    """
    Получает результаты из бд и формирует сообщение с цитатой (чтобы свернуть текст).
    """
    user_data = await get_user_data(user_id)

    if not user_data:
        return (
            "У вас пока нет сохраненных результатов.\n"
            "Пройдите один из опросов: \"Удовлетворенность отношениями\" или \"Идеальный партнер\"."
        )

    satisfaction = user_data.get('satisfaction_result')
    ideal = user_data.get('ideal_traits')

    text = "📝 Вы прошли следующие опросы:\n"

    if satisfaction and ideal:
        # Оба результата есть
        text += (
            "\n<b>Удовлетворенность отношениями и Идеальный партнер</b>\n\n"
            "❤️ Удовлетворенность отношениями:\n"
            f"<blockquote expandable>{satisfaction}</blockquote>\n\n"
            "❤️ Идеальный партнер:\n"
            f"<blockquote expandable>{ideal}</blockquote>"
        )
    elif satisfaction:
        # Только удовлетворенность
        text += (
            "\n❤️ Удовлетворенность отношениями\n"
            f"<blockquote expandable>{satisfaction}</blockquote>"
        )
    elif ideal:
        # Только идеальный партнер
        text += (
            "\n❤️ Идеальный партнер\n"
            f"<blockquote expandable>{ideal}</blockquote>"
        )
    else:
        text = (
            "У вас пока нет сохраненных результатов опросов.\n"
            "Пройдите один из опросов: \"Удовлетворенность отношениями\" или \"Идеальный партнер\"."
        )

    return text