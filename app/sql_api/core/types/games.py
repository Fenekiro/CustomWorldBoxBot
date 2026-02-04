from dataclasses import dataclass

from app.sql_api.core.types.researches import ResearchCore


@dataclass
class GameCore:
    id: int
    name: str
    start_date_timestamp: float
    end_date_timestamp: float
    researches: list[ResearchCore]
    researches_image_link: str
    winners: list[int]
    image: str
    is_open_for_registration: bool
    is_finished: bool
