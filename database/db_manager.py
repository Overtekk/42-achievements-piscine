import aiosqlite
from utils import is_file_exist, print_log

DB_PATH = "data/database.db"


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _connect(self) -> aiosqlite.Connection:
        return aiosqlite.connect(self.db_path)

    async def setup_database(self) -> None:
        if is_file_exist(DB_PATH):
            print_log("Database found. Loading.")
        else:
            print_log("Database not found. Creating it.")

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")

            # Create table users + points
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    points INTEGER DEFAULT 0
                );
            """)

            # Create table users + achievements
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    achievement_id TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_discord_messages (
                    user_id TEXT PRIMARY KEY,
                    nb_messages INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_42_links (
                    user_id TEXT PRIMARY KEY,
                    login_42 TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_42_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    login_42 TEXT NOT NULL,
                    level INTEGER DEFAULT 0,
                    total_logtime_hours REAL DEFAULT 0,
                    projects_validated TEXT DEFAULT '[]',
                    exams_done INTEGER DEFAULT 0,
                    rush_done INTEGER DEFAULT 0,
                    corrections_done INTEGER DEFAULT 0,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)

            await db.commit()

    async def add_user_points(self, user_id: str, points: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO users (user_id, points) VALUES (?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET points = points + ?
            """,
                (user_id, points, points),
            )

            await db.commit()

    async def remove_user_points(self, user_id: str, points: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE users
                SET points = MAX(points - ?, 0)
                WHERE user_id = ?
            """,
                (points, user_id),
            )

            await db.commit()

    async def check_achievement(self, user_id: str, achievement_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT 1 FROM user_achievements
                WHERE user_id = ? AND achievement_id = ?
            """,
                (user_id, achievement_id),
            ) as cursor:
                candidat = await cursor.fetchone()

                if candidat:
                    return True
                return False

    async def unlock_achievement(
        self, user_id: str, achievement_id: str, points: int
    ) -> bool:
        if await self.check_achievement(user_id, achievement_id):
            return False

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)
            """,
                (user_id, achievement_id),
            )
            await db.commit()

            await self.add_user_points(user_id, points)

        return True

    async def remove_achievement(
        self, user_id: str, achievement_id: str, points: int
    ) -> bool:
        if not await self.check_achievement(user_id, achievement_id):
            return False

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM user_achievements
                WHERE user_id = ? and achievement_id = ?
            """,
                (user_id, achievement_id),
            )
            await db.commit()

            await self.remove_user_points(user_id, points)

        return True

    async def get_leaderboard(self, limit: int = 999999) -> list[tuple[str, int]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT user_id, points FROM users
                ORDER BY points DESC LIMIT ?
            """,
                (limit,),
            ) as cursor:
                return await cursor.fetchall()

    async def get_user_achievements(self, user_id: str) -> list[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT achievement_id FROM user_achievements
                WHERE user_id = ?
            """,
                (user_id,),
            ) as cursor:
                rows = await cursor.fetchall()

                return [row[0] for row in rows]

    async def increment_user_message_count(self, user_id: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                INSERT INTO user_discord_messages (user_id, nb_messages)
                VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET nb_messages = nb_messages + 1
                RETURNING nb_messages
            """,
                (user_id,),
            ) as cursor:
                nb_msg = await cursor.fetchone()
                await db.commit()

                return nb_msg[0] if nb_msg else 0

    async def check_user_message_count(self, user_id: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT nb_messages FROM user_discord_messages
                WHERE user_id = ?
            """,
                (user_id,),
            ) as cursor:
                nb_msg = await cursor.fetchone()

                return nb_msg[0] if nb_msg else 0

    async def get_users_message_count(
        self, limit: int = 999999
    ) -> list[tuple[str, int]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT user_id, nb_messages FROM user_discord_messages
                ORDER BY nb_messages DESC LIMIT ?
            """,
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()

                return rows

    async def link_42_account(self, user_id: str, login_42: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO user_42_links (user_id, login_42) VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET login_42 = ?
            """,
                (user_id, login_42, login_42),
            )
            await db.commit()

    async def get_42_login(self, user_id: str) -> str | None:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT login_42 FROM user_42_links WHERE user_id = ?
            """,
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def get_all_linked_users(self) -> list[tuple[str, str]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT user_id, login_42 FROM user_42_links"
            ) as cursor:
                return await cursor.fetchall()

    async def save_42_snapshot(
        self,
        user_id: str,
        login_42: str,
        level: int,
        total_logtime_hours: float,
        projects_validated: str,
        exams_done: int,
        rush_done: int,
        corrections_done: int,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO user_42_snapshots
                    (user_id, login_42, level, total_logtime_hours, projects_validated,
                     exams_done, rush_done, corrections_done)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    login_42,
                    level,
                    total_logtime_hours,
                    projects_validated,
                    exams_done,
                    rush_done,
                    corrections_done,
                ),
            )
            await db.commit()

    async def get_last_42_snapshot(
        self, user_id: str
    ) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT level, total_logtime_hours, projects_validated,
                       exams_done, rush_done, corrections_done, checked_at
                FROM user_42_snapshots
                WHERE user_id = ?
                ORDER BY checked_at DESC LIMIT 1
            """,
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return {
                    "level": row[0],
                    "total_logtime_hours": row[1],
                    "projects_validated": row[2],
                    "exams_done": row[3],
                    "rush_done": row[4],
                    "corrections_done": row[5],
                    "checked_at": row[6],
                }
