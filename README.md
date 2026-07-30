# 42 Achievements discord bot for 42 Piscine

## 📝 Table of contents
1. [❓ What is this bot?](#-what-is-this-bot)
2. [📚 Dependencies](#-dependencies)
3. [✏️ Commands](#️-commands)
4. [📒 Setup](#-setup)

---

## ❓ What is this bot?

This Discord bot, written in **Python**, was built for the main Piscine at **42 Le Havre**. Its goal is to make the experience even more fun by adding gamified achievements to complete along the way.

Whether tied to the core Piscine projects, tutor events, or Discord interactions, you can easily create achievements for just about anything!

⚠️ If you have an issue, please report it [here](https://github.com/Overtekk/42-achievements-piscine/issues?q=sort%3Aupdated-desc+is%3Aissue+state%3Aopen+).

---

## 📚 Dependencies

- **Python >= 3.10**
- **discord.py**
-  **dotenv**
- **pydantic**
- **rich**
- **aiosqlite**

📍 Install using `venv`.
```bash
uv sync
```

---

## ✏️ Commands

**`/leaderboard`**: access to the global leaderboard. Showing the 20 top users page per page.

**`/achievements <language>(optional) <user>(optional)`**: see your own achievement page. Default show all achievements but you can organize it by completed or not completed.\
By default the language is `english`, the second language is `french`.\
Specify an user to see his own achievement list.

**`/information <language>(optional)`**: see the information page about the bot and available commands.

**`/send_message <message> <image>(optional)`**: send a message to the private tutors channel. You can send a picture with this.

**`/secret <code>`**: used for custom achievements on discord.

#### Commands available for tutors (need the `manage_guild` permission)

**`/add_achivement <user> <achievement_name>`**: add the achievement to the specify user.

**`/remove_achivement <user> <achievement_name>`**: remove the achievement to the specify user.

**`/list_nb_messages`**: show the leaderboard of the top numbers of messages sent.

**`/show_informations_for_all`**: show the information panel for everyone.

---

## 📒 Setup

You can setup the bot for your own!

First step: create the discord bot and get the bot token. Paste in the `.env` file at the root.

In the data folder you have two files to configure:
- `config.json`

```json
{
	"server_id": ID OF THE SERVER,
	"channel_id": CHANNEL ID WHERE ACHIEVEMENT UNLOCK WILL BE SEND,
	"channel_log_id": CHANNEL ID FOR THE TUTORS (logs + message from the command `send_message`),
	"pisciners_role_id": ROLE OF THE PISCINERS,
	"admin_role_id": ROLES OF THE TUTORS/ADMINS
}
```

- `achievement_list.json`

You can configure your own achievement list.

```json
[
	{
		"name": NAME OF THE ACHIEVEMENT,
		"description_en": DESCRIPTION IN ENGLISH,
		"description_fr": DESCRIPTION IN FRENCH (or other language),
		"points": POINTS OF THE SUCCESS
	},
	{
		"name": "Example Success",
		"description_en": "This is an example",
		"description_fr": "Ceci est un example",
		"points": 5
	}
]
```

In `cogs/custom` you can add your own custom achievement system. Delete the content of the `custon_achievements.py` and write your own thing!

---
