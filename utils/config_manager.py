from utils import is_file_exist, is_folder_exist, check_file_extension, print_log
import json
from pydantic import BaseModel, ConfigDict, Field, ValidationError, RootModel
from pathlib import Path
from enum import Enum

CONFIG_PATH = "data/config.json"
ACHIEVEMENT_PATH = "data/achievements_list.json"

KEYS = [
    'channel_id', 'channel_log'
]


# :-------------------:
#        CONFIG
# :------------------:


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    channel_id: str = Field(
        min_length=19, max_length=19, pattern=r"^\d+$"
    )
    channel_log: str = Field(
        min_length=19, max_length=19, pattern=r"^\d+$"
    )
    pisciners_role: str = Field(
        min_length=1, pattern=r"^\d+$"
    )
    admins: list[str] = Field(
        default_factory=list[str]
    )


def load_config() -> dict[str, str]:
    """
    Load the config file in 'data/config.json', verify informations and return a dictionnary.
    """

    filepath = Path(CONFIG_PATH)

    # Checking 'data' folder
    if not is_folder_exist(filepath.parent):
        raise ValueError("'data' folder does not exist.")

    # Checking config file
    if not is_file_exist(filepath):
        raise ValueError("'config.json' does not exist. Copy 'config.example.json' and rename it to 'config.json'. Don't forget to modify the config!")
    if not check_file_extension(filepath, 'json'):
        raise ValueError(f"wrong extension for {filepath}")

    try:
        config_data = filepath.read_text(encoding="utf-8")
        config_validation = ConfigModel.model_validate_json(config_data)
    except ValidationError as e:
        raise ValueError(f"Invalid config file: {e}") from e

    return config_validation.model_dump()


def update_config(key: str, value: str) -> dict[str, str]:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)

        if key not in config:
            print_log("Key doesn't exist")
            return load_config()

        config[key] = value
        try:
            config_data = ConfigModel.model_validate(config)  # noqa: F841
        except ValidationError as e:
            print_log(e)
            return

    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

    return load_config()


# :-------------------:
#     ACHIEVEMENTS
# :------------------:


class Difficulty(str, Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'


class AchievementModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name_en: str = Field(
        min_length=1
    )
    name_fr: str = Field(
        min_length=1
    )
    description_en: str = Field(
        min_length=1
    )
    description_fr: str = Field(
        min_length=1
    )
    difficulty: Difficulty
    points: int


class AchievementListModel(RootModel[list[AchievementModel]]):
    pass


def load_achievements() -> list[dict[str, str]]:
    """
    Load the achivement file in 'data/achievements_list.json', verify and return a dict
    """

    filepath = Path(ACHIEVEMENT_PATH)

    # Checking 'data' folder
    if not is_folder_exist(filepath.parent):
        raise ValueError("'data' folder does not exist.")

    # Checking achievement file
    if not is_file_exist(filepath):
        raise ValueError("'achievements_list.json' does not exist. Copy 'achievements_list.example.json' and rename it to 'achievements_list.json'. Don't forget to modify the file!")
    if not check_file_extension(filepath, 'json'):
        raise ValueError(f"wrong extension for {filepath}")

    try:
        achievement_data = filepath.read_text(encoding="utf-8")
        achievement_file_validation = AchievementListModel.model_validate_json(achievement_data)
    except ValidationError as e:
        raise ValueError(f"Invalid config file: {e}") from e

    return achievement_file_validation.model_dump()
