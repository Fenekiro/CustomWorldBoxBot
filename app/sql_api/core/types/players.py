from dataclasses import dataclass

from app.sql_api.core.types.wars import PlayerWarsCore
from app.sql_api.core.types.researches import PlayerResearchCore


@dataclass
class PlayerCore:
    game_id: int
    discord_id: int
    registration_message_discord_id: str
    country_name: str
    capital_name: str
    race: str
    culture_name: str
    researches: list[PlayerResearchCore]
    wars: PlayerWarsCore
    is_eliminated: bool


@dataclass
class PlayerRegisterData:
    discord_id: int
    registration_message_discord_id: str
    country_name: str
    capital_name: str
    race: str
    culture_name: str
