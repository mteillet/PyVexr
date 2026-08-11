"""
Regressions des plantages corriges : chaque test echouerait sur le code
d'origine avec une exception (AttributeError, UnboundLocalError, TypeError,
IndexError...).
"""

import json
import types

import numpy as np
import pyVexr_gui as gui
import pyVexr_main as main
from conftest import writeExr


def contactSheetDict(path, ocioConfigPath, saturation=1, exposure=0):
    return {
        "path": [path],
        "saturation": saturation,
        "exposure": exposure,
        "ocioVar": ocioConfigPath,
        "ocioToggle": False,
        "ocio": {
            "ocioIn": "Linear",
            "ocioOut": "sRGB",
            "ocioLook": "None",
            "ocioDisplay": "sRGB,Standard",
        },
    }


def test_alphaOnAnExrWithoutAlphaGivesBlackInsteadOfCrashing(tmp_path):
    # No alpha anywhere in the file : the branch that used to leave
    # channelR/G/B unbound and raise UnboundLocalError.
    path = writeExr(
        tmp_path / "noalpha.exr",
        {"R": 0.2, "G": 0.4, "B": 0.6,
         "diffuse.R": 0.1, "diffuse.G": 0.2, "diffuse.B": 0.3},
    )

    red, green, blue = main.exrSwitchChannel([path], "diffuse", "alpha")

    assert red.shape == (12, 16)
    assert np.allclose(red, 0.0)
    assert np.allclose(green, 0.0)
    assert np.allclose(blue, 0.0)


def test_alphaIsStillReadWhenTheFileHasOne(rgbaExr):
    red, green, blue = main.exrSwitchChannel([rgbaExr], None, "alpha")

    assert np.allclose(red, 1.0)


def test_contactSheetWithASingleLayer(tmp_path, ocioConfigPath):
    path = writeExr(
        tmp_path / "one.exr",
        {"R": 0.2, "G": 0.4, "B": 0.6,
         "diffuse.R": 0.1, "diffuse.G": 0.2, "diffuse.B": 0.3},
    )

    pixels, width, height, bytesPerLine = main.layerContactSheetBackend(
        ["diffuse"], contactSheetDict(path, ocioConfigPath)
    )

    assert (width, height) == (16, 12)
    assert len(bytes(pixels)) == bytesPerLine * height


def test_contactSheetWithSaturation(tmp_path, ocioConfigPath):
    path = writeExr(
        tmp_path / "one.exr",
        {"R": 0.2, "G": 0.4, "B": 0.6,
         "diffuse.R": 0.1, "diffuse.G": 0.2, "diffuse.B": 0.3},
    )

    # saturationTweak was called with two arguments out of three here.
    result = main.layerContactSheetBackend(
        ["diffuse"], contactSheetDict(path, ocioConfigPath, saturation=0.3)
    )

    assert result[1:] == (16, 12, 48)


def bufferWidget(painted=None, epoch=1):
    painted = painted if painted is not None else []
    widget = types.SimpleNamespace(
        imgDict={"buffer": [None, None, None]},
        bufferEpoch=epoch,
        bufferBytes=0,
        bufferBudgetBytes=1024 ** 3,
        frameNumber=types.SimpleNamespace(
            slider=types.SimpleNamespace(value=lambda: 0),
            _timeline=types.SimpleNamespace(
                paintBuffer=lambda position, size: painted.append(position),
                unpaintBuffer=lambda position: None,
            ),
        ),
    )
    # Les vraies methodes, liees a ce faux widget.
    widget.frameByteSize = lambda image: gui.MyWidget.frameByteSize(widget, image)
    widget.enforceBufferBudget = lambda: gui.MyWidget.enforceBufferBudget(widget)
    return widget


FRAME = (b"", 2, 2, 6)


def test_bufferResultOutOfRangeIsDropped():
    widget = bufferWidget()

    assert gui.MyWidget.storeBufferResult(widget, FRAME, 7, 1) is False
    assert gui.MyWidget.storeBufferResult(widget, FRAME, -1, 1) is False
    assert widget.imgDict["buffer"] == [None, None, None]


def test_bufferResultFromAPreviousBufferIsDropped():
    widget = bufferWidget(epoch=3)

    # Worker started before a resetBuffer : its pixels belong to another shot.
    assert gui.MyWidget.storeBufferResult(widget, FRAME, 1, 2) is False
    assert widget.imgDict["buffer"] == [None, None, None]


def test_bufferResultInRangeIsStored():
    painted = []
    widget = bufferWidget(painted)

    assert gui.MyWidget.storeBufferResult(widget, FRAME, 1, 1) is True
    assert widget.imgDict["buffer"] == [None, FRAME, None]
    assert painted == [1]


def test_bufferEvictsTheFramesFurthestFromThePlayhead():
    widget = bufferWidget()
    widget.bufferBudgetBytes = 2 * 12  # deux images de 12 octets

    for position in range(3):
        gui.MyWidget.storeBufferResult(widget, FRAME, position, 1)

    cached = [index for index, image in enumerate(widget.imgDict["buffer"])
              if image is not None]
    assert widget.bufferBytes <= widget.bufferBudgetBytes
    # La tete de lecture est en 0, c'est la derniere image conservee.
    assert 0 in cached
    assert 2 not in cached


def fakeTimeline(width, maximum, minimum=0):
    return types.SimpleNamespace(
        _timeline=types.SimpleNamespace(width=lambda: width),
        slider=types.SimpleNamespace(
            maximum=lambda: maximum, minimum=lambda: minimum
        ),
    )


def test_timelineClickOnTheLeftEdgeGivesTheFirstFrame():
    from pyVexr_timelineGui import Timeline

    position = types.SimpleNamespace(x=lambda: 0)

    assert Timeline.pixelPosToRangeValue(fakeTimeline(500, 99), position) == 0


def test_timelineClickInTheMiddleGivesTheMiddleFrame():
    from pyVexr_timelineGui import Timeline

    position = types.SimpleNamespace(x=lambda: 250)

    assert Timeline.pixelPosToRangeValue(fakeTimeline(500, 100), position) == 50


def test_timelineClickBeyondTheRightEdgeIsClamped():
    from pyVexr_timelineGui import Timeline

    position = types.SimpleNamespace(x=lambda: 900)

    assert Timeline.pixelPosToRangeValue(fakeTimeline(500, 100), position) == 100


def test_timelineClickBeforeTheFirstLayoutDoesNotDivideByZero():
    from pyVexr_timelineGui import Timeline

    position = types.SimpleNamespace(x=lambda: 10)

    assert Timeline.pixelPosToRangeValue(fakeTimeline(0, 100), position) == 100


def savedConfigWidget(monkeypatch, tmp_path, payload):
    monkeypatch.setattr(gui, "absPath", "{}/".format(tmp_path))
    if payload is not None:
        (tmp_path / "config.json").write_text(payload)
    return types.SimpleNamespace()


def test_incompleteConfigIsIgnoredInsteadOfBreakingStartup(monkeypatch, tmp_path):
    widget = savedConfigWidget(
        monkeypatch, tmp_path, json.dumps({"ocioVar": "/nowhere/config.ocio"})
    )

    assert gui.MyWidget.readSavedConfig(widget) is None


def test_corruptedConfigIsIgnored(monkeypatch, tmp_path):
    widget = savedConfigWidget(monkeypatch, tmp_path, "{not json")

    assert gui.MyWidget.readSavedConfig(widget) is None


def test_configPointingAtAMissingOcioFileIsIgnored(monkeypatch, tmp_path):
    payload = json.dumps({
        "ocioVar": "/gone/config.ocio", "ocioIn": "Linear", "ocioOut": "sRGB",
        "ocioDisplay": "sRGB,Standard", "ocioLook": "None",
    })
    widget = savedConfigWidget(monkeypatch, tmp_path, payload)

    assert gui.MyWidget.readSavedConfig(widget) is None


def test_completeConfigIsLoaded(monkeypatch, tmp_path, ocioConfigPath):
    payload = json.dumps({
        "ocioVar": ocioConfigPath, "ocioIn": "Linear", "ocioOut": "sRGB",
        "ocioDisplay": "sRGB,Standard", "ocioLook": "None",
    })
    widget = savedConfigWidget(monkeypatch, tmp_path, payload)

    config = gui.MyWidget.readSavedConfig(widget)

    assert config["ocioVar"] == ocioConfigPath
    assert config["ocioIn"] == "Linear"
