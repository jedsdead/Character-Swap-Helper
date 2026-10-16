"""Plugin settings, persisted to settings.json next to this file."""

import json
import os

_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

DEFAULTS = {
    "enabled": False,   # give the control video to H3 as <Video 1> in masked video-to-video generations
}

_settings = dict(DEFAULTS)


def load():
    try:
        with open(_SETTINGS_PATH, "r", encoding="utf-8") as handle:
            stored = json.load(handle)
        _settings.update({key: stored[key] for key in DEFAULTS if key in stored})
    except FileNotFoundError:
        pass
    except Exception as error:
        print(f"[H3 Character Swap] could not read settings.json, using defaults: {error}")


def save():
    try:
        with open(_SETTINGS_PATH, "w", encoding="utf-8") as handle:
            json.dump(_settings, handle, indent=2)
    except Exception as error:
        print(f"[H3 Character Swap] could not save settings.json: {error}")


def get():
    return dict(_settings)


def set_value(key, value):
    _settings[key] = value
    save()
