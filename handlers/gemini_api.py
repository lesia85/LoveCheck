import logging
import asyncio
from google import genai
from google.genai import types
from config import GEMINI_TOKEN

client = genai.Client(api_key=GEMINI_TOKEN)

TEXT_MODEL = 'gemini-3.1-flash-lite'


async def generate_text_with_gemini(prompt: str, system_instruction: str | None = None, contents: list | None = None, max_retries: int = 3) -> str:
    """
    Генерация текста через Gemini с правильной логикой повторных попыток.
    """
    attempt = 0
    reply_text = ""
    success = False

    config = types.GenerateContentConfig(
        system_instruction=system_instruction or "Ты — полезный и эмпатичный психологический помощник.",
        temperature=0.7
    )

    if contents is not None:
        request_contents = contents
    else:
        request_contents = prompt

    while attempt < max_retries and not success:
        logging.info(f"Gemini Текст: Попытка {attempt + 1}/{max_retries}...")

        try:
            response = await client.aio.models.generate_content(
                model=TEXT_MODEL,
                contents=request_contents,
                config=config
            )

            if response and response.text:
                reply_text = response.text.strip()
                logging.info("Gemini Текст: Ответ успешно получен и обработан.")
                success = True
            else:
                logging.warning("Gemini Текст: Пустой ответ от сервера.")
                attempt += 1

        except Exception as e:
            error_str = str(e).lower()
            logging.error(f"Gemini Текст: Ошибка на попытке {attempt + 1}: {e}")

            retry_keywords = [
                "rate limit", "overload", "timeout", "connection", "busy",
                "429", "503", "unavailable", "high demand", "overloaded"
            ]

            if any(keyword in error_str for keyword in retry_keywords):
                wait_time = (2 ** attempt) * 4
                logging.info(f"Gemini Текст: Временная ошибка. Повтор через {wait_time} сек...")
                await asyncio.sleep(wait_time)
                attempt += 1
            else:
                logging.error("Gemini Текст: Критическая ошибка. Прерывание.")
                break

    if not success:
        raise Exception("Gemini Текст: Не удалось получить ответ после нескольких попыток.")

    return reply_text