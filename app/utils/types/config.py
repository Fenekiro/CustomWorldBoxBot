from dataclasses import dataclass
import ujson


@dataclass
class ConfigData:
    current_game_id: int | None
    game_session_is_open: bool
    commands_chat_id: int | None
    events_chat_id: int | None
    registration_for_game_chat_id: int | None
    admin_ids: list[int]
    debug_chat_id: int | None
    game_role_id: int

    def to_json(self) -> str:
        return ujson.dumps(self.__dict__, indent=2)
