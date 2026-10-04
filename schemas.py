from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RPGModel(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_assignment=True)


class Stats(RPGModel):
    ninjutsu: int = Field(default=10, ge=0, le=999)
    taijutsu: int = Field(default=10, ge=0, le=999)
    genjutsu: int = Field(default=10, ge=0, le=999)
    defense: int = Field(default=10, ge=0, le=999)
    speed: int = Field(default=10, ge=0, le=999)


class InventoryItem(RPGModel):
    name: str = Field(min_length=1, max_length=80)
    quantity: int = Field(default=1, ge=0, le=999)
    description: str = Field(default="", max_length=240)


class Relationship(RPGModel):
    name: str = Field(min_length=1, max_length=80)
    sentiment: int = Field(default=0, ge=-100, le=100)
    note: str = Field(default="", max_length=240)


class Quest(RPGModel):
    title: str = Field(min_length=1, max_length=120)
    status: Literal["نشطة", "مكتملة", "فاشلة"] = "نشطة"
    description: str = Field(default="", max_length=400)
    reward_ryo: int = Field(default=0, ge=0, le=1_000_000)


class Player(RPGModel):
    name: str = Field(default="نينجا مجهول", min_length=1, max_length=40)
    village: str = Field(default="كونوها", max_length=40)
    nindo: str = Field(default="حماية الرفاق", max_length=120)
    alignment: Literal["شينوبي القرية", "نينجا مارق", "مرتزق"] = "شينوبي القرية"


class GameState(RPGModel):
    version: int = 1
    player: Player = Field(default_factory=Player)
    level: int = Field(default=1, ge=1, le=999)
    exp: int = Field(default=0, ge=0, le=1_000_000_000)
    stats: Stats = Field(default_factory=Stats)

    hp: int = Field(default=100, ge=0, le=999_999)
    max_hp: int = Field(default=100, ge=1, le=999_999)
    chakra: int = Field(default=100, ge=0, le=999_999)
    max_chakra: int = Field(default=100, ge=1, le=999_999)

    ryo: int = Field(default=250, ge=0, le=1_000_000_000)
    bounty: int = Field(default=0, ge=0, le=1_000_000_000)
    anbu_heat: int = Field(default=0, ge=0, le=100)
    storm_gauge: int = Field(default=0, ge=0, le=100)
    kawarimi: int = Field(default=2, ge=0, le=99)
    max_kawarimi: int = Field(default=2, ge=0, le=99)

    awakening: Optional[str] = None
    inventory: List[InventoryItem] = Field(default_factory=list)
    relationships: Dict[str, Relationship] = Field(default_factory=dict)
    quests: List[Quest] = Field(default_factory=list)
    log: List[str] = Field(default_factory=list)
    defeated: bool = False

    @field_validator("log")
    @classmethod
    def keep_recent_log_entries(cls, value: List[str]) -> List[str]:
        return value[-100:]


class GameResponse(RPGModel):
    narration: str = Field(default="الصمت يخيّم على المكان.", max_length=5000)
    choices: List[str] = Field(default_factory=list, max_length=5)
    npc_name: Optional[str] = Field(default=None, max_length=80)
    relationship_delta: int = Field(default=0, ge=-10, le=10)
    atmosphere: str = Field(default="متوتر", max_length=80)


def sanitize_json_schema(value: Any) -> Any:
    """Remove schema keywords that some provider APIs reject."""
    if isinstance(value, dict):
        result: Dict[str, Any] = {}
        for key, item in value.items():
            if key in {"additionalProperties", "default", "title"}:
                continue
            result[key] = sanitize_json_schema(item)
        return result
    if isinstance(value, list):
        return [sanitize_json_schema(item) for item in value]
    return value
