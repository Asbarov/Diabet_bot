import datetime
from typing import Optional

import aiosqlite

from config import DB_PATH


CREATE_PATIENTS_TABLE = """
CREATE TABLE IF NOT EXISTS patients (
    user_id           INTEGER PRIMARY KEY,
    username          TEXT,
    full_name         TEXT NOT NULL,
    gender            TEXT NOT NULL,
    age               INTEGER NOT NULL,
    city              TEXT NOT NULL,
    diabetes_years    INTEGER NOT NULL,
    height_cm         REAL NOT NULL,
    weight_kg         REAL NOT NULL,
    therapy           TEXT NOT NULL,
    phone             TEXT NOT NULL,
    registered_at     TEXT NOT NULL
);
"""


CREATE_DOCTORS_TABLE = """
CREATE TABLE IF NOT EXISTS doctors (
    user_id            INTEGER PRIMARY KEY,
    username           TEXT,
    full_name          TEXT NOT NULL,
    city               TEXT NOT NULL,
    workplace          TEXT NOT NULL,
    specialty          TEXT NOT NULL,
    experience_years   INTEGER NOT NULL,
    status             TEXT NOT NULL DEFAULT 'pending',
    registered_at      TEXT NOT NULL
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_PATIENTS_TABLE)
        await db.execute(CREATE_DOCTORS_TABLE)

        # Миграция старой базы:
        # если таблицы были созданы раньше без username,
        # добавляем это поле.
        await add_column_if_missing(
            db,
            "patients",
            "username",
            "TEXT",
        )

        await add_column_if_missing(
            db,
            "doctors",
            "username",
            "TEXT",
        )

        await db.commit()


async def add_column_if_missing(
    db: aiosqlite.Connection,
    table_name: str,
    column_name: str,
    column_type: str,
) -> None:
    async with db.execute(f"PRAGMA table_info({table_name})") as cursor:
        columns = await cursor.fetchall()

    existing_columns = {column[1] for column in columns}

    if column_name not in existing_columns:
        await db.execute(
            f"ALTER TABLE {table_name} "
            f"ADD COLUMN {column_name} {column_type}"
        )


# ============================================================
# ПАЦИЕНТЫ
# ============================================================

async def get_patient(user_id: int) -> Optional[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT * FROM patients WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            return await cursor.fetchone()


async def add_patient(
    user_id: int,
    username: Optional[str],
    full_name: str,
    gender: str,
    age: int,
    city: str,
    diabetes_years: int,
    height_cm: float,
    weight_kg: float,
    therapy: str,
    phone: str,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO patients (
                user_id,
                username,
                full_name,
                gender,
                age,
                city,
                diabetes_years,
                height_cm,
                weight_kg,
                therapy,
                phone,
                registered_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                full_name,
                gender,
                age,
                city,
                diabetes_years,
                height_cm,
                weight_kg,
                therapy,
                phone,
                datetime.datetime.utcnow().isoformat(
                    timespec="seconds"
                ),
            ),
        )

        await db.commit()


async def list_all_patients() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
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
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT * FROM doctors WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            return await cursor.fetchone()


async def add_doctor(
    user_id: int,
    username: Optional[str],
    full_name: str,
    city: str,
    workplace: str,
    specialty: str,
    experience_years: int,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO doctors (
                user_id,
                username,
                full_name,
                city,
                workplace,
                specialty,
                experience_years,
                status,
                registered_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                user_id,
                username,
                full_name,
                city,
                workplace,
                specialty,
                experience_years,
                datetime.datetime.utcnow().isoformat(
                    timespec="seconds"
                ),
            ),
        )

        await db.commit()


async def list_approved_doctors() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT *
            FROM doctors
            WHERE status = 'approved'
            ORDER BY full_name
            """
        ) as cursor:
            return await cursor.fetchall()


async def get_pending_doctors() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT *
            FROM doctors
            WHERE status = 'pending'
            ORDER BY registered_at
            """
        ) as cursor:
            return await cursor.fetchall()


async def list_all_doctors() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT *
            FROM doctors
            ORDER BY status, full_name
            """
        ) as cursor:
            return await cursor.fetchall()


async def set_doctor_status(
    user_id: int,
    status: str,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE doctors
            SET status = ?
            WHERE user_id = ?
            """,
            (status, user_id),
        )

        await db.commit()


async def delete_doctor(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM doctors WHERE user_id = ?",
            (user_id,),
        )

        await db.commit()