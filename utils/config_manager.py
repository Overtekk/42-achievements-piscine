from utils import is_file_exist, is_folder_exist, check_file_extension

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pathlib import Path

CONFIG_PATH = "data/config.json"

KEYS = [
    'channel_id', 'channel_log'
]


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_id: str = Field(
        min_length=19, max_length=19, pattern=r"^\d+$"
    )
    channel_log: str = Field(
        min_length=19, max_length=19, pattern=r"^\d+$"
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

