import aiosqlite

DB_PATH = 'data/database.db'

class DatabaseManager():
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def setup_database(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")

            # Create table users
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    points INTEGER DEFAULT 0
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    achievement_id TEXT,
                    FOREIGN KEY (user_ID) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)

            await db.commit()

    async def add_user_points(self, user_id: str, points: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (user_id, points) VALUES (?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET points = points + ?
            """, (user_id, points, points))

            await db.commit()

    async def remove_user_points(self, user_id: str, points: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users
                SET points = MAX(points - ?, 0)
                WHERE user_id = ?
            """, (points, user_id))

            await db.commit()

    async def check_achievement(self, user_id: str, achievement_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT 1 FROM user_achievements
                WHERE user_id = ? AND achievement_id = ?
            """, (user_id, achievement_id)) as cursor:

                candidat = await cursor.fetchone()

                if candidat:
                    return True
                return False

    async def unlock_achievement(self, user_id: str, achievement_id: str, points: int) -> bool:
        if await self.check_achievement(user_id, achievement_id):
            return False

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)
            """, (user_id, achievement_id))
            await db.commit()

            await self.add_user_points(user_id, points)

        return True

    async def remove_achievement(self, user_id: str, achievement_id: str, points: int) -> bool:
        if not await self.check_achievement(user_id, achievement_id):
            return False

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM user_achievements
                WHERE user_id = ? and achievement_id = ?
            """, (user_id, achievement_id))
            await db.commit()

            await self.remove_user_points(user_id, points)

        return True

    async def get_leaderboard(self, limit: int = -1) -> list[tuple[str, int]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, points FROM users
                ORDER BY points DESC LIMIT ?
            """, (limit,)) as cursor:

                return await cursor.fetchall()

    async def get_user_achievements(self, user_id: str) -> list[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT achievement_id FROM user_achievements
                WHERE user_id = ?
            """, (user_id,)) as cursor:

                rows = await cursor.fetchall()

                return [row[0] for row in rows]
