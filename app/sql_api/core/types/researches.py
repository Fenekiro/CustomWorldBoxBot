from dataclasses import dataclass


@dataclass
class ResearchCore:
    id: int
    name: str
    minutes_to_complete: int
    required_researches: list[int]
    mutually_exclusive_researches: list[int]


@dataclass
class PlayerResearchCore:
    research: ResearchCore
    item_count: int
    researching_until_timestamp: float
    producing_item_until_timestamp: float | None
