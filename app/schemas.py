"""Pydantic schemas for API request validation."""
import datetime as dt
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

EventType = Literal["tariff", "military", "geopolitical"]
SignalClass = Literal["red", "amber", "green"]


class Signal(BaseModel):
    label: str = Field(..., min_length=1, max_length=80)
    val: str = Field(..., min_length=1, max_length=120)
    cls: SignalClass = "amber"


class EventCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9\-]*$")
    date: dt.date
    name: str = Field(..., min_length=1, max_length=200)
    type: EventType
    type_label: str = Field(..., min_length=1, max_length=20)
    summary: str = Field(..., min_length=1, max_length=2000)
    score: int = Field(..., ge=0, le=100)
    signals: list[Signal] = Field(default_factory=list)
    is_candidate: bool = False

    @field_validator("signals")
    @classmethod
    def at_least_one_signal(cls, v):
        if len(v) == 0:
            raise ValueError("At least one signal is required")
        return v


class EventUpdate(BaseModel):
    date: Optional[dt.date] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[EventType] = None
    type_label: Optional[str] = Field(None, min_length=1, max_length=20)
    summary: Optional[str] = Field(None, min_length=1, max_length=2000)
    score: Optional[int] = Field(None, ge=0, le=100)
    signals: Optional[list[Signal]] = None
    is_candidate: Optional[bool] = None
