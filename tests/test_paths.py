"""
Resolution des chemins : ressources livrees avec l'application et fichier de
preferences de l'utilisateur.
"""

import os

import pyVexr_paths as paths
from conftest import ROOT


def test_resourcesAreResolvedNextToTheApplication():
    assert paths.resource("imgs") == os.path.join(ROOT, "imgs")
    assert os.path.isdir(paths.resource("imgs"))


def test_theShippedOcioConfigIsFound():
    assert os.path.isfile(paths.ocioConfigPath())


def test_resourcesDoNotDependOnTheCurrentDirectory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert os.path.isfile(paths.ocioConfigPath())


def test_userConfigFollowsXdg(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    assert paths.userConfigPath() == str(tmp_path / "PyVexr" / "config.json")


def test_writableConfigCreatesItsDirectory(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "fresh"))

    path = paths.writableConfigPath()

    assert os.path.isdir(os.path.dirname(path))


def test_readableConfigFallsBackToTheApplicationDirectory(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Nothing in the user directory : an install from a previous version keeps
    # its config.json next to the application.
    assert paths.readableConfigPath() == paths.legacyConfigPath()


def test_readableConfigPrefersTheUserFile(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    os.makedirs(str(tmp_path / "PyVexr"))
    (tmp_path / "PyVexr" / "config.json").write_text("{}")

    assert paths.readableConfigPath() == paths.userConfigPath()
