import json
from datetime import UTC, datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utils import print_error, print_log
from utils.api_42 import CURSUS_ID, FourtyTwoAPI


def _parse_locations(locations: list[dict]) -> list[tuple[datetime, datetime]]:
    result = []
    for loc in locations:
        if not loc.get("begin_at"):
            continue
        begin = datetime.fromisoformat(loc["begin_at"])
        end_str = loc.get("end_at")
        if end_str:
            end = datetime.fromisoformat(end_str)
        else:
            end = datetime.now(UTC)
        result.append((begin, end))
    return result


def _compute_daily_logtime(
    sessions: list[tuple[datetime, datetime]],
) -> dict[str, float]:
    daily: dict[str, float] = {}
    for begin, end in sessions:
        hours = (end - begin).total_seconds() / 3600
        date_str = begin.strftime("%Y-%m-%d")
        daily[date_str] = daily.get(date_str, 0) + hours
    return daily


def _compute_weekly_logtime(
    sessions: list[tuple[datetime, datetime]],
) -> dict[str, float]:
    weekly: dict[str, float] = {}
    for begin, end in sessions:
        hours = (end - begin).total_seconds() / 3600
        iso_year, iso_week, _ = begin.isocalendar()
        key = f"{iso_year}-W{iso_week:02d}"
        weekly[key] = weekly.get(key, 0) + hours
    return weekly


def _count_consecutive_days(daily: dict[str, float]) -> int:
    dates = sorted(daily.keys())
    if not dates:
        return 0
    max_streak = 1
    current_streak = 1
    for i in range(1, len(dates)):
        prev = datetime.strptime(dates[i - 1], "%Y-%m-%d").replace(tzinfo=UTC)
        curr = datetime.strptime(dates[i], "%Y-%m-%d").replace(tzinfo=UTC)
        if (curr - prev).days == 1:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    return max_streak


def _get_project_name_lower(project: dict) -> str:
    p = project.get("project", {})
    return p.get("name", "").lower()


def _is_rush_project(project: dict) -> bool:
    return "rush" in _get_project_name_lower(project)


def _is_exam_project(project: dict) -> bool:
    p = project.get("project", {})
    if p.get("exam"):
        return True
    return "exam" in p.get("name", "").lower()


def _match_module(project: dict, module_name: str) -> bool:
    name = _get_project_name_lower(project)
    normalized = module_name.lower().replace(" ", " ")
    return normalized in name


def _count_projects_validated(projects: list[dict]) -> set[str]:
    validated = set()
    for p in projects:
        if p.get("validated?") and p.get("final_mark") is not None:
            name = p.get("project", {}).get("name", "")
            if name:
                validated.add(name)
    return validated


def _has_perfect_score(projects: list[dict]) -> bool:
    return any(
        p.get("final_mark") == 100 and p.get("validated?")
        for p in projects
    )


def _count_exams(projects: list[dict]) -> int:
    return sum(1 for p in projects if _is_exam_project(p))


def _count_rush(projects: list[dict]) -> int:
    return sum(1 for p in projects if _is_rush_project(p) and p.get("validated?"))


def _has_resilience(projects: list[dict]) -> bool:
    by_project: dict[int, list[dict]] = {}
    for p in projects:
        pid = p.get("project", {}).get("id")
        if pid is not None:
            by_project.setdefault(pid, []).append(p)
    for attempts in by_project.values():
        if len(attempts) < 2:
            continue
        sorted_attempts = sorted(attempts, key=lambda a: a.get("marked_at", ""))
        had_failure = any(not a.get("validated?", False) for a in sorted_attempts)
        has_pass = any(a.get("validated?", False) for a in sorted_attempts)
        if had_failure and has_pass:
            return True
    return False


def _has_perfectionist(projects: list[dict]) -> bool:
    by_project: dict[int, list[dict]] = {}
    for p in projects:
        pid = p.get("project", {}).get("id")
        if pid is not None:
            by_project.setdefault(pid, []).append(p)
    for attempts in by_project.values():
        if len(attempts) < 2:
            continue
        sorted_attempts = sorted(attempts, key=lambda a: a.get("marked_at", ""))
        marks = [
            a.get("final_mark", 0) or 0
            for a in sorted_attempts
            if a.get("final_mark") is not None
        ]
        if len(marks) >= 2 and max(marks) > marks[0]:
            return True
    return False


def _count_peer_evaluations(projects: list[dict], user_login: str) -> int:
    count = 0
    for p in projects:
        for team in p.get("teams", []):
            for member in team.get("users", []):
                if member.get("login") == user_login and member.get("leader?", False):
                    pass
        for scale in p.get("reviews", []):
            if scale.get("corrector", {}).get("login") == user_login:
                count += 1
    return count


def _count_different_evaluators(projects: list[dict], user_login: str) -> set[str]:
    evaluators: set[str] = set()
    for p in projects:
        for review in p.get("reviews", []):
            corrector = review.get("corrector", {})
            if corrector.get("login") != user_login:
                evaluators.add(corrector.get("login", ""))
    return evaluators


class ApiAchievements(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.api: FourtyTwoAPI | None = None
        self.achievement_sys = self.bot.get_cog("AchievementSystem")
        self.pisciners_role = int(self.bot.config["pisciners_role_id"])

        uid = self.bot.config.get("api_42_uid")
        secret = self.bot.config.get("api_42_secret")
        if uid and secret:
            self.api = FourtyTwoAPI(uid, secret)
            self.check_all_users.start()
        else:
            print_error(
                "42 API credentials not found. "
                "Add API_42_UID and API_42_SECRET to .env. "
                "API-based achievements will not work."
            )

    def cog_unload(self) -> None:
        if self.api and self.check_all_users.is_running():
            self.check_all_users.cancel()

    # :-------------------:
    #    Slash commands
    # :-------------------:

    @app_commands.command(
        name="check_achievements",
        description="Manually trigger achievement check for a user [ADMIN]",
    )
    @app_commands.default_permissions(manage_guild=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def check_achievements(
        self, interaction: discord.Interaction, user: discord.Member
    ) -> None:
        if not self.api:
            await interaction.response.send_message(
                "42 API is not configured.", ephemeral=True, delete_after=15
            )
            return

        await interaction.response.defer(ephemeral=True)
        count, api_calls = await self._check_user(user)
        await interaction.followup.send(
            f"Checked achievements for {user.mention}. Unlocked: **{count}** new achievement(s). (~{api_calls} API calls)",
            ephemeral=True,
        )

    # :-------------------:
    #    Periodic task
    # :-------------------:

    @tasks.loop(hours=1)
    async def check_all_users(self) -> None:
        if not self.bot.is_ready() or not self.api:
            return

        linked = await self.bot.db.get_all_linked_users()
        if not linked:
            return

        MAX_CALLS_PER_CHECK = 1000
        calls_used = 0
        total_unlocked = 0

        for user_id, login_42 in linked:
            if calls_used >= MAX_CALLS_PER_CHECK:
                print_log(
                    f"Rate limit safety: stopping after {calls_used} API calls "
                    f"({len(linked) - linked.index((user_id, login_42))} users skipped). "
                    f"Increase MAX_CALLS_PER_CHECK or reduce the check interval."
                )
                break

            member = self.bot.get_guild(int(self.bot.config["server_id"]))
            if not member:
                continue
            discord_user = member.get_member(int(user_id))
            if not discord_user:
                continue

            pisciners_role = int(self.bot.config["pisciners_role_id"])
            if not any(role.id == pisciners_role for role in discord_user.roles):
                continue

            count, api_calls = await self._check_user(discord_user)
            calls_used += api_calls
            total_unlocked += count

        if total_unlocked > 0:
            print_log(f"Periodic check: {total_unlocked} new achievement(s) unlocked. Used ~{calls_used} API calls.")

    @check_all_users.before_loop
    async def before_check(self) -> None:
        await self.bot.wait_until_ready()

    # :-------------------:
    #    Core logic
    # :-------------------:

    async def _check_user(self, member: discord.Member) -> tuple[int, int]:
        user_id = str(member.id)
        login = await self.bot.db.get_42_login(user_id)
        if not login or not self.api:
            return 0, 0

        user_data = await self.api.get_user(login)
        if not user_data:
            return 0, self.api.get_and_reset_call_count()

        projects = await self.api.get_user_projects(login)
        locations = await self.api.get_user_locations(login)
        cutoff = (datetime.now(UTC) - timedelta(days=30)).isoformat()
        locations = [
            loc for loc in locations
            if loc.get("begin_at") and loc["begin_at"] >= cutoff
        ]

        level = 0
        for cu in user_data.get("cursus_users", []):
            if cu.get("cursus", {}).get("id") == CURSUS_ID:
                level = int(cu.get("level", 0))
                break

        sessions = _parse_locations(locations)
        daily = _compute_daily_logtime(sessions)
        weekly = _compute_weekly_logtime(sessions)
        consecutive = _count_consecutive_days(daily)
        total_hours = sum(daily.values())

        validated_names = _count_projects_validated(projects)
        exams = _count_exams(projects)
        rush_count = _count_rush(projects)
        resilience = _has_resilience(projects)
        perfectionist = _has_perfectionist(projects)
        evaluators = _count_different_evaluators(projects, login)

        await self.bot.db.save_42_snapshot(
            user_id,
            login,
            level,
            total_hours,
            json.dumps(list(validated_names)),
            exams,
            rush_count,
            0,
        )

        unlocked = 0

        if max(daily.values(), default=0) >= 8:
            unlocked += await self._try_unlock(member, "A long day!")

        if max(weekly.values(), default=0) >= 35:
            unlocked += await self._try_unlock(member, "Weekly Warrior")

        if consecutive >= 4:
            unlocked += await self._try_unlock(member, "I Love Coding")

        if level >= 2:
            unlocked += await self._try_unlock(member, "Beginner")
        if level >= 4:
            unlocked += await self._try_unlock(member, "Apprentice")
        if level >= 6:
            unlocked += await self._try_unlock(member, "Learner")

        for module in [
            "Shell 00",
            "Shell 01",
            "C 00",
            "C 01",
            "C 02",
            "C 03",
            "C 04",
            "C 05",
            "C 06",
            "C 07",
            "C 08",
        ]:
            achievement_name = f"Complete {module.replace(' ', '')}"
            if any(module.lower() in name.lower() for name in validated_names):
                unlocked += await self._try_unlock(member, achievement_name)

        if rush_count >= 1:
            unlocked += await self._try_unlock(member, "Time to rush!")
        if rush_count >= 2:
            unlocked += await self._try_unlock(member, "Time to double rush!")

        if exams >= 1:
            unlocked += await self._try_unlock(member, "Exam Discoverer")
        if exams >= 2:
            unlocked += await self._try_unlock(member, "Exam Beginner")
        if exams >= 3:
            unlocked += await self._try_unlock(member, "Exam Master")

        if _has_perfect_score(projects):
            unlocked += await self._try_unlock(member, "Perfection")

        if resilience:
            unlocked += await self._try_unlock(member, "Resilience")

        if perfectionist:
            unlocked += await self._try_unlock(member, "Perfectionist")

        if projects:
            unlocked += await self._try_unlock(member, "The Moulinette")

        if len(evaluators) >= 5:
            unlocked += await self._try_unlock(member, "The Peer Reviewer")
        if len(evaluators) >= 10:
            unlocked += await self._try_unlock(member, "The Goat Reviewer")

        api_calls = self.api.get_and_reset_call_count()
        return unlocked, api_calls

    async def _try_unlock(
        self, member: discord.Member, achievement_name: str
    ) -> int:
        target = None
        for a in self.bot.achievements_list:
            if a["name"] == achievement_name:
                target = a
                break
        if not target:
            return 0

        unlocked = await self.bot.db.unlock_achievement(
            member.id, target["id"], target["points"]
        )
        if unlocked:
            achievement_sys = self.bot.get_cog("AchievementSystem")
            if achievement_sys:
                await achievement_sys.send_unlock_success_message(member, target)
        return 1 if unlocked else 0


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ApiAchievements(bot))
