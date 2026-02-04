from dataclasses import dataclass


@dataclass
class WarCore:
    aggressor: int
    defender: int


@dataclass
class PlayerWarsCore:
    cant_declare_war_until_timestamp: float
    wars: list[WarCore]
