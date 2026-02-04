import ujson

from app.utils.types.config import ConfigData


CONFIG_PATH = __file__.replace(r"utils\config.py", "config.json")


class Config:
    def __init__(self, data: ConfigData) -> None:
        self.data: ConfigData = data

    def update_json_file(self) -> None:
        with open(__file__.replace(r"utils\config.py", "config.json"), "w") as file:
            file.write(self.data.to_json())


def get_config() -> Config:
    with open(__file__.replace(r"utils\config.py", "config.json"), "r") as file:
        config_dict: dict = ujson.loads(file.read())
        config_data = ConfigData(
            config_dict["current_game_id"],
            config_dict["game_session_is_open"],
            config_dict["commands_chat_id"],
            config_dict["events_chat_id"],
            config_dict["registration_for_game_chat_id"],
            config_dict["admin_ids"],
            config_dict["debug_chat_id"],
            config_dict["game_role_id"]
        )

        return Config(config_data)


config_class = get_config()
