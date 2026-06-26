import json
from typing import Any, Dict, Mapping, Optional

import aiosqlite
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey


class SQLiteStorage(BaseStorage):
    def __init__(self, path: str):
        self.path = path
        self._ready = False

    async def _ensure_ready(self) -> None:
        if self._ready:
            return
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS fsm_storage (
                    bot_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    thread_id INTEGER NOT NULL DEFAULT 0,
                    business_connection_id TEXT NOT NULL DEFAULT '',
                    destiny TEXT NOT NULL DEFAULT 'default',
                    state TEXT,
                    data TEXT NOT NULL DEFAULT '{}',
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (
                        bot_id, chat_id, user_id, thread_id,
                        business_connection_id, destiny
                    )
                )
            """)
            await db.commit()
        self._ready = True

    @staticmethod
    def _key_tuple(key: StorageKey) -> tuple:
        return (
            key.bot_id,
            key.chat_id,
            key.user_id,
            key.thread_id or 0,
            key.business_connection_id or "",
            key.destiny,
        )

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        await self._ensure_ready()
        state_value = state.state if isinstance(state, State) else state
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                INSERT INTO fsm_storage (
                    bot_id, chat_id, user_id, thread_id,
                    business_connection_id, destiny, state, data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, '{}')
                ON CONFLICT(
                    bot_id, chat_id, user_id, thread_id,
                    business_connection_id, destiny
                )
                DO UPDATE SET state = excluded.state, updated_at = CURRENT_TIMESTAMP
            """, (*self._key_tuple(key), state_value))
            await db.commit()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        await self._ensure_ready()
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("""
                SELECT state FROM fsm_storage
                WHERE bot_id = ? AND chat_id = ? AND user_id = ?
                  AND thread_id = ? AND business_connection_id = ?
                  AND destiny = ?
            """, self._key_tuple(key)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        await self._ensure_ready()
        data_json = json.dumps(dict(data), ensure_ascii=False)
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                INSERT INTO fsm_storage (
                    bot_id, chat_id, user_id, thread_id,
                    business_connection_id, destiny, data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    bot_id, chat_id, user_id, thread_id,
                    business_connection_id, destiny
                )
                DO UPDATE SET data = excluded.data, updated_at = CURRENT_TIMESTAMP
            """, (*self._key_tuple(key), data_json))
            await db.commit()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        await self._ensure_ready()
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("""
                SELECT data FROM fsm_storage
                WHERE bot_id = ? AND chat_id = ? AND user_id = ?
                  AND thread_id = ? AND business_connection_id = ?
                  AND destiny = ?
            """, self._key_tuple(key)) as cursor:
                row = await cursor.fetchone()
                if not row or not row[0]:
                    return {}
                return json.loads(row[0])

    async def close(self) -> None:
        self._ready = False
