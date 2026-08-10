import datetime
from typing import Optional

import aiosqlite

from config import DB_PATH


CREATE_PATIENTS_TABLE = """
CREATE TABLE IF NOT EXISTS patients (
    user_id           INTEGER PRIMARY KEY,
    full_name         TEXT NOT NULL,
    gender            TEXT NOT NULL,
    age               INTEGER NOT NULL,
    city              TEXT NOT NULL,
    diabetes_years    INTEGER NOT NULL,
    height_cm         REAL NOT NULL,
    weight_kg         REAL NOT NULL,
    therapy           TEXT NOT NULL,
    phone             TEXT NOT NULL,
    username          TEXT,
    registered_at     TEXT NOT NULL
);
"""


CREATE_DOCTORS_TABLE = """
CREATE TABLE IF NOT EXISTS doctors (
    user_id            INTEGER PRIMARY KEY,
    full_name          TEXT NOT NULL,
    city               TEXT NOT NULL,
    workplace          TEXT NOT NULL,
    specialty          TEXT NOT NULL,
    experience_years   INTEGER NOT NULL,
    status             TEXT NOT NULL DEFAULT 'pending',
    username           TEXT,
    registered_at      TEXT NOT NULL
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as database:
        await database.execute(CREATE_PATIENTS_TABLE)
        await database.execute(CREATE_DOCTORS_TABLE)

        # Добавляем новые колонки в старую БД, если их ещё нет.
        for table in ("patients", "doctors"):
            async with database.execute(f"PRAGMA table_info({table})") as cursor:
                columns = await cursor.fetchall()

            column_names = {row[1] for row in columns}

            if "username" not in column_names:
                await database.execute(
                    f"ALTER TABLE {table} ADD COLUMN username TEXT"
                )

        await database.commit()


# ============================================================
# ПАЦИЕНТЫ
# ============================================================

async def get_patient(user_id: int) -> Optional[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as database:
        database.row_factory = aiosqlite.Row

        async with database.execute(
            "SELECT * FROM patients WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            return await cursor.fetchone()


async def add_patient(
    user_id: int,
    full_name: str,
    gender: str,
    age: int,
    city: str,
    diabetes_years: int,
    height_cm: float,
    weight_kg: float,
    therapy: str,
    phone: str,
    username: Optional[str] = None,
) -> None:

    registered_at = datetime.datetime.utcnow().isoformat(
        timespec="seconds"
    )

    async with aiosqlite.connect(DB_PATH) as database:
        await database.execute(
            """
            INSERT OR REPLACE INTO patients (
                user_id,
                full_name,
                gender,
                age,
                city,
                diabetes_years,
                height_cm,
                weight_kg,
                therapy,
                phone,
                username,
                registered_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                full_name,
                gender,
                age,
                city,
                diabetes_years,
                height_cm,
                weight_kg,
                therapy,
                phone,
                username,
                registered_at,
            ),
        )

        await database.commit()


async def list_all_patients() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as database:
        database.row_factory = aiosqlite.Row

        async with database.execute(
            """
            SELECT *
            FROM patients
            ORDER BY full_name
            """
        ) as cursor:
            return await cursor.fetchall()


# ============================================================
# ВРАЧИ
# ============================================================

async def get_doctor(user_id: int) -> Optional[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as database:
        database.row_factory = aiosqlite.Row

        async with database.execute(
            "SELECT * FROM doctors WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            return await cursor.fetchone()


async def add_doctor(
    user_id: int,
    full_name: str,
    city: str,
    workplace: str,
    specialty: str,
    experience_years: int,
    username: Optional[str] = None,
) -> None:

    registered_at = datetime.datetime.utcnow().isoformat(
        timespec="seconds"
    )

    async with aiosqlite.connect(DB_PATH) as database:
        await database.execute(
            """
            INSERT OR REPLACE INTO doctors (
                user_id,
                full_name,
                city,
                workplace,
                specialty,
                experience_years,
                status,
                username,
                registered_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (
                user_id,
                full_name,
                city,
                workplace,
                specialty,
                experience_years,
                username,
                registered_at,
            ),
        )

        await database.commit()


async def list_approved_doctors() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as database:
        database.row_factory = aiosqlite.Row

        async with database.execute(
            """
            SELECT *
            FROM doctors
            WHERE status = 'approved'
            ORDER BY full_name
            """
        ) as cursor:
            return await cursor.fetchall()


async def get_pending_doctors() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as database:
        database.row_factory = aiosqlite.Row

        async with database.execute(
            """
            SELECT *
            FROM doctors
            WHERE status = 'pending'
            ORDER BY registered_at
            """
        ) as cursor:
            return await cursor.fetchall()


async def list_all_doctors() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as database:
        database.row_factory = aiosqlite.Row

        async with database.execute(
            """
            SELECT *
            FROM doctors
            WHERE status = 'approved'
            ORDER BY full_name
            """
        ) as cursor:
            return await cursor.fetchall()


async def set_doctor_status(
    user_id: int,
    status: str,
) -> None:

    async with aiosqlite.connect(DB_PATH) as database:
        await database.execute(
            """
            UPDATE doctors
            SET status = ?
            WHERE user_id = ?
            """,
            (status, user_id),
        )

        await database.commit()


async def delete_doctor(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as database:
        await database.execute(
            "DELETE FROM doctors WHERE user_id = ?",
            (user_id,),
        )

        await database.commit()

async def list_all_patients() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT * FROM patients ORDER BY full_name"
        ) as cursor:
            return await cursor.fetchall()
