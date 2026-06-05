import logging
import asyncio
from google import genai
from google.genai import types
from config import GEMINI_TOKEN

client = genai.Client(api_key=GEMINI_TOKEN)

# Используем актуальные флагманские модели мультимодального семейства Gemini 2.5
TEXT_MODEL = 'gemini-2.5-flash'
IMAGE_MODEL = 'imagen-4.0-generate-001'

async def generate_text_with_gemini(prompt: str, max_retries: int = 3) -> str:
    """
    Генерация текста через официальную библиотеку google-genai
    с подробным логированием каждого шага.
    """
    attempt = 0
    success = False
    reply_text = ""

    config = types.GenerateContentConfig(
        system_instruction="Ты — полезный и эмпатичный психологический помощник.",
        temperature=0.7
    )

    while attempt < max_retries and not success:
        logging.info(f"Gemini Текст: Попытка {attempt + 1}/{max_retries}. Подготовка к отправке...")
        try:
            logging.info(f"Gemini Текст: Инициализация асинхронного запроса. Отправка промпта: '{prompt[:60]}...'")
            
            # Вызов метода официальной библиотеки через асинхронный интерфейс (.aio)
            response = await client.aio.models.generate_content(
                model=TEXT_MODEL,
                contents=prompt,
                config=config
            )
            
            # Проверяем, что ответ успешно получен и содержит текст
            if response and response.text:
                reply_text = response.text.strip()
                logging.info("Gemini Текст: Ответ от сервера Google успешно получен и обработан.")
                success = True
            else:
                logging.warning("Gemini Текст: Сервер вернул пустой ответ или некорректную структуру.")
                attempt += 1

        except Exception as e:
            error_str = str(e).lower()
            logging.error(f"Gemini Текст: Ошибка на попытке {attempt + 1}: {e}")
            attempt += 1
            
            # Если ошибка связана с лимитами или сетью — делаем паузу перед следующей попыткой
            if any(x in error_str for x in ["rate limit", "overload", "timeout", "connection", "busy", "429"]):
                wait_time = (2 ** (attempt - 1)) * 3
                logging.info(f"Gemini Текст: Сетевая пауза. Повтор через {wait_time} сек...")
                if attempt < max_retries:
                    await asyncio.sleep(wait_time)
            else:
                # Если ошибка критическая (например, неверный токен API), прерываем цикл
                logging.error("Gemini Текст: Критическая ошибка конфигурации или валидации. Прерывание генерации.")
                break
                
    if not success:
        raise Exception("Gemini Текст: Не удалось получить текстовый ответ после серии попыток.")
        
    return reply_text


async def generate_image_with_gemini(prompt: str, max_retries: int = 3) -> bytes:
    """
    Генерация изображения через официальную модель Imagen 3 в Gemini SDK
    с возвратом бинарных данных (bytes).
    """
    attempt = 0
    success = False
    image_bytes = b""

    while attempt < max_retries and not success:
        logging.info(f"Gemini Картинка: Попытка {attempt + 1}/{max_retries}. Подготовка к генерации...")
        try:
            logging.info(f"Gemini Картинка: Отправка промпта рисования: '{prompt[:60]}...'")
            
            # Запрос генерации изображения через асинхронный интерфейс Imagen
            response = await client.aio.models.generate_images(
                model=IMAGE_MODEL,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",
                    output_mime_type="image/jpeg"
                )
            )
            
            if response and response.generated_images:
                logging.info("Gemini Картинка: Сервер успешно вернул данные изображения. Обработка байтов...")
                
                # В google-genai байты картинки лежат непосредственно в поле image.image_bytes
                image_bytes = response.generated_images[0].image.image_bytes
                logging.info("Gemini Картинка: Данные успешно получены. Байты готовы к отправке.")
                success = True
            else:
                logging.warning("Gemini Картинка: Ответ получен, но поле generated_images оказалось пустым.")
                attempt += 1
                    
        except Exception as e:
            error_str = str(e).lower()
            logging.error(f"Gemini Картинка: Ошибка на попытке {attempt + 1}: {e}")
            attempt += 1
            
            if any(x in error_str for x in ["rate limit", "overload", "timeout", "connection", "busy", "429"]):
                wait_time = (2 ** (attempt - 1)) * 5
                logging.info(f"Gemini Картинка: Сетевая пауза. Повтор через {wait_time} сек...")
                if attempt < max_retries:
                    await asyncio.sleep(wait_time)
            else:
                logging.error("Gemini Картинка: Критическая ошибка конфигурации. Прерывание генерации.")
                break
                
    if not success:
        raise Exception("Gemini Картинка: Не удалось сгенерировать изображение после серии попыток.")
        
    return image_bytes