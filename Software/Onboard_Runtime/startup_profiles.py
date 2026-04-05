from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StartupProfile(str, Enum):
    DEV = "dev"
    DEMO = "demo"
    HEADLESS = "headless"


@dataclass(frozen=True)
class ProfileSettings:
    log_level: str
    ui_enabled: bool
    stable_defaults: bool


PROFILE_PRESETS: dict[StartupProfile, ProfileSettings] = {
    StartupProfile.DEV: ProfileSettings(
        log_level="DEBUG",
        ui_enabled=True,
        stable_defaults=False,
    ),
    StartupProfile.DEMO: ProfileSettings(
        log_level="INFO",
        ui_enabled=True,
        stable_defaults=True,
    ),
    StartupProfile.HEADLESS: ProfileSettings(
        log_level="INFO",
        ui_enabled=False,
        stable_defaults=True,
    ),
}


def resolve_profile(profile: str) -> ProfileSettings:
    profile_key = StartupProfile(profile.lower())
    return PROFILE_PRESETS[profile_key]
