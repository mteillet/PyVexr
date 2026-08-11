"""
Where PyVexr finds its files.

pyVexr_gui.py and pyVexr_main.py each used to derive their own root from
sys.argv[0], with two different formulas (absPath and realPath) that disagree
as soon as the current directory is not the one holding the script : the OCIO
preferences were written to one and read from the other. Launching through a
symlink or from another directory broke the splash screen, the icon and the
OCIO config, and the manual split on "/" did not hold on Windows.

Everything goes through this module now.
"""

import json
import os
import sys


def applicationDir():
    """
    Directory holding imgs/, ocio/ and the modules.

    In a PyInstaller bundle the resources sit next to the executable (the spec
    uses contents_directory='.'), everywhere else next to this file.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = applicationDir()


def resource(*parts):
    """Absolute path of a file shipped with the application."""
    return os.path.join(APP_DIR, *parts)


def ocioConfigPath():
    """The OCIO config shipped with PyVexr."""
    return resource("ocio", "config.ocio")


def userConfigDir():
    """
    Where the user preferences belong, following the platform conventions.

    Writing next to the executable fails on any read only install (system
    package, /opt, the Rocky bundle unpacked as root) and dirties the source
    tree during development.
    """
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "PyVexr")


def userConfigPath():
    """Preferences file that PyVexr writes."""
    return os.path.join(userConfigDir(), "config.json")


def legacyConfigPath():
    """Preferences file of the previous versions, next to the application."""
    return resource("config.json")


def readableConfigPath():
    """
    Preferences to read : the user file, or the one of a previous version so
    an existing setup keeps working.
    """
    userPath = userConfigPath()
    if os.path.exists(userPath):
        return userPath
    return legacyConfigPath()


def writableConfigPath():
    """Preferences file to write, creating its directory if needed."""
    path = userConfigPath()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def readPreferences():
    """
    Saved preferences, or None when they are missing, unreadable, incomplete,
    or point at an OCIO config that no longer exists.

    This runs while the main window is being built, so anything raising here
    used to make the application impossible to start.
    """
    jsonPath = readableConfigPath()
    if not os.path.exists(jsonPath):
        return None

    try:
        with open(jsonPath, "r") as handle:
            preferences = json.load(handle)
    except (OSError, ValueError) as error:
        print("Ignoring unreadable config.json : {}".format(error))
        return None

    expected = ["ocioVar", "ocioIn", "ocioOut", "ocioDisplay", "ocioLook"]
    missing = [key for key in expected if key not in preferences]
    if missing:
        print("Ignoring incomplete config.json, missing {}".format(
            ", ".join(missing)))
        return None

    if not os.path.exists(preferences["ocioVar"]):
        print("Ignoring config.json, the ocio config {} is gone".format(
            preferences["ocioVar"]))
        return None

    return preferences
