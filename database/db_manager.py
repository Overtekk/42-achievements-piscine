class DatabaseManager():
    pass


# setup_database()
# create tables if does not exist

# add_user_points(user_id, points) / remove_user_points(user_id, points)
# add or remove points to an user

# unlock_achievement(user_id, achievement_id)
# valid an achievement

# check_achievement(user_id, achievement_id)
# check if user already have the achievement

# get_leaderboard(limit)
# get the best player from the leaderboard

# learn > aiosqlite
# INSERT INTO users (user_id, points) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET points = points + ?
# SELECT user_id, points FROM users ORDER BY points DESC LIMIT ?
