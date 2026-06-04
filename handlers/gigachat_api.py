import logging
import asyncio
import base64
from gigachat import GigaChat
from config import GIGACHAT_CREDENTIALS

async def generate_text_with_gigachat(prompt: str, max_retries: int = 3) -> str:
    """
    Генерация текста через официальную библиотеку GigaChat 
    с подробным логированием каждого шага.
    """
    for attempt in range(max_retries):
        logging.info(f"GigaChat Текст: Попытка {attempt + 1}/{max_retries}. Подготовка к отправке...")
        try:
            # Инициализируем асинхронный клиент официальной библиотеки
            async with GigaChat(
                credentials=GIGACHAT_CREDENTIALS, 
                scope="GIGACHAT_API_PERS", 
                verify_ssl_certs=False
            ) as gigachat:
                
                messages = [
                    {"role": "system", "content": "Ты — полезный и эмпатичный психологический помощник."},
                    {"role": "user", "content": prompt}
                ]
                
                logging.info(f"GigaChat Текст: Сессия создана. Отправка промпта: '{prompt[:60]}...'")
                
                # Вызов метода официальной библиотеки
                response = await gigachat.achat(messages=messages)
                
                # Проверяем, что ответ успешно получен и содержит текст
                if response and response.choices:
                    reply_text = response.choices[0].message.content.strip()
                    logging.info("GigaChat Текст: Ответ от сервера Сбера успешно получен и обработан.")
                    return reply_text
                else:
                    logging.warning("GigaChat Текст: Сервер вернул пустой ответ или некорректную структуру choices.")
                    
        except Exception as e:
            error_str = str(e).lower()
            logging.error(f"GigaChat Текст: Ошибка на попытке {attempt + 1}: {e}")
            
            # Если ошибка связана с лимитами или сетью — делаем паузу перед следующей попыткой
            if any(x in error_str for x in ["rate limit", "overload", "timeout", "connection", "busy"]):
                wait_time = (2 ** attempt) * 3
                logging.info(f"GigaChat Текст: Сетевая пауза. Повтор через {wait_time} сек...")
                await asyncio.sleep(wait_time)
            else:
                # Если ошибка критическая (например, неверный токен), прерываем цикл
                logging.error("GigaChat Текст: Критическая ошибка конфигурации. Прерывание генерации.")
                break
                
    raise Exception("GigaChat Текст: Не удалось получить текстовый ответ после серии попыток.")


async def generate_image_with_gigachat(prompt: str, max_retries: int = 3) -> bytes:
    """
    Генерация изображения через официальную библиотеку GigaChat
    с возвратом бинарных данных (bytes).
    """
    for attempt in range(max_retries):
        logging.info(f"GigaChat Картинка: Попытка {attempt + 1}/{max_retries}. Подготовка к генерации...")
        try:
            async with GigaChat(
                credentials=GIGACHAT_CREDENTIALS, 
                scope="GIGACHAT_API_PERS", 
                verify_ssl_certs=False
            ) as gigachat:
                
                logging.info(f"GigaChat Картинка: Отправка промпта рисования: '{prompt[:60]}...'")
                
                # Запрос генерации в формате base64
                response = await gigachat.aimages(
                    prompt=prompt,
                    response_format="base64"
                )
                
                if response and response.images and len(response.images) > 0:
                    logging.info("GigaChat Картинка: Сервер успешно вернул base64-строку изображения. Декодирование...")
                    
                    # Декодируем base64 в байты для отправки через aiogram
                    image_bytes = base64.b64decode(response.images[0].data)
                    logging.info("GigaChat Картинка: Декодирование завершено успешно. Байты готовы к отправке.")
                    return image_bytes
                else:
                    logging.warning("GigaChat Картинка: Ответ получен, но поле images оказалось пустым.")
                    
        except Exception as e:
            error_str = str(e).lower()
            logging.error(f"GigaChat Картинка: Ошибка на попытке {attempt + 1}: {e}")
            
            if any(x in error_str for x in ["rate limit", "overload", "timeout", "connection", "busy"]):
                wait_time = (2 ** attempt) * 5
                logging.info(f"GigaChat Картинка: Сетевая пауза. Повтор через {wait_time} сек...")
                await asyncio.sleep(wait_time)
            else:
                logging.error("GigaChat Картинка: Критическая ошибка конфигурации. Прерывание генерации.")
                break
                
    raise Exception("GigaChat Картинка: Не удалось сгенерировать изображение после серии попыток.")