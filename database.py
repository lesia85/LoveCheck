import aiosqlite
import logging
from config import DATABASE_NAME

async def create_db():
    """
    Создаёт базу данных и две таблицы, если они не существуют.
    Таблицы:
        users — данные пользователя и результаты опросов.
        chat_history — история переписки с ИИ.
    """
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            # Таблица 1: пользователи и их результаты
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    is_consented BOOLEAN DEFAULT 0,
                    state TEXT,
                    satisfaction_result TEXT,
                    ideal_traits TEXT
                )
            ''')

            # Таблица 2: история диалога с ИИ
            await db.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    user_id INTEGER PRIMARY KEY,
                    message_text TEXT,
                    role TEXT,
                    timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                    mark_like INTEGER,
                    mark_mission_complete INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            async with db.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
                tables = await cursor.fetchall()
            logging.info(f"Таблицы в БД: {[t[0] for t in tables]}")
            logging.info("База данных и таблицы успешно созданы/проверены")
    except Exception as e:
        logging.error(f"Ошибка при создании базы данных: {e}")
        raise


async def save_or_update_user(user_id: int, data: dict):
    """
    Сохраняет или обновляет информацию о пользователе в таблице users.
    Если пользователь уже существует — выполняется UPDATE, иначе INSERT.

    :user_id: Telegram ID пользователя
    :data: словарь с полями для обновления/вставки.
                 Допустимые ключи: is_consented, state,
                 satisfaction_result, ideal_traits.
    """
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            # Проверка: существует ли пользователь
            async with db.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,)) as cursor:
                exists = await cursor.fetchone() is not None

            if exists:
                #Обновление существующей записи
                update_fields = []
                values = []
                for key in ['is_consented', 'state', 'satisfaction_result', 'ideal_traits']:
                    if key in data:
                        update_fields.append(f"{key} = ?")
                        values.append(data[key])
                if update_fields:
                    query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = ?"
                    values.append(user_id)
                    await db.execute(query, values)
            else:
                #Вставка новой записи
                await db.execute('''
                    INSERT INTO users (user_id, is_consented, state, satisfaction_result, ideal_traits)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    data.get('is_consented', 0),
                    data.get('state'),
                    data.get('satisfaction_result'),
                    data.get('ideal_traits'),
                ))
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных пользователя {user_id}: {e}")
        raise


async def add_chat_message(user_id: int, message_text: str, role: str, 
    mark_like: int = 0, mark_mission_complete: int = 0):
    """
    Сохраняет или обновляет последнюю запись пользователя.
    timestamp записывается ТОЛЬКО при первом сообщении и больше не меняется.
    """
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            await db.execute('''
                INSERT INTO chat_history (user_id, message_text, role, mark_like, mark_mission_complete)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    message_text = excluded.message_text,
                    role = excluded.role,
                    mark_like = excluded.mark_like,
                    mark_mission_complete = excluded.mark_mission_complete
            ''', (user_id, message_text, role, mark_like, mark_mission_complete))
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка при сохранении сообщения пользователя {user_id}: {e}")
        raise


async def get_user_data(user_id: int) -> dict | None:
    """
    Возвращает данные пользователя из таблицы users в виде словаря.
    Если пользователь не найден, возвращает None.
    """
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            async with db.execute('''
                SELECT is_consented, state, satisfaction_result, ideal_traits
                FROM users WHERE user_id = ?
            ''', (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'is_consented': bool(row[0]),
                        'state': row[1],
                        'satisfaction_result': row[2],
                        'ideal_traits': row[3]
                    }
                return None
    except Exception as e:
        logging.error(f"Ошибка при получении данных пользователя {user_id}: {e}")
        return None


async def get_chat_history(user_id: int, limit: int = 5) -> list[dict]:
    """
    Возвращает последние сообщения из истории диалога с ИИ для указанного пользователя.
    Сортировка по возрастанию времени (от старых к новым).

    :param user_id: Telegram ID пользователя
    :param limit: максимальное количество возвращаемых сообщений
    :return: список словарей с ключами 'role', 'message_text', 'timestamp'
    """
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            async with db.execute('''
                SELECT role, message_text, timestamp
                FROM chat_history
                WHERE user_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (user_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [{'role': row[0], 
                         'message_text': row[1], 
                         'timestamp': row[2]} 
                         for row in rows]
    except Exception as e:
        logging.error(f"Ошибка при получении истории диалога пользователя {user_id}: {e}")
        return []
