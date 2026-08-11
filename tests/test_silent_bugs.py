"""
Regressions des bugs silencieux : sur le code d'origine ces tests passaient
sans erreur mais avec un resultat faux (cache jamais invalide, versions
effacees, images 16 bits surexposees, couche introuvable...).
"""

import types

import cv2 as cv
import numpy as np

import pyVexr_gui as gui
import pyVexr_main as main
from conftest import writeExr


def bufferStateWidget(seqDict):
    return types.SimpleNamespace(
        seqDict=seqDict,
        imgDict={
            "ocio": {"ocioIn": "Linear", "ocioOut": "sRGB",
                     "ocioLook": "None", "ocioDisplay": "sRGB,Standard"},
            "ocioToggle": False,
            "channel": None,
            "exposure": 0,
            "saturation": 1,
            "RGBA": "rgba",
            "ContactSheet": False,
            "ContactSheetChannels": [],
        },
    )


def test_bufferStateSeesANewShot():
    widget = bufferStateWidget({"shotA": ["a0"]})
    before = gui.MyWidget.snapshotBufferState(widget)

    widget.seqDict["shotB"] = ["b0"]
    after = gui.MyWidget.snapshotBufferState(widget)

    # Storing seqDict.keys() kept a live view, so the two snapshots always
    # compared equal and the cache was never invalidated.
    assert before != after


def test_bufferStateSeesAnExposureChange():
    widget = bufferStateWidget({"shotA": ["a0"]})
    before = gui.MyWidget.snapshotBufferState(widget)

    widget.imgDict["exposure"] = 2
    assert gui.MyWidget.snapshotBufferState(widget) != before


def test_bufferStateSeesANewContactSheetSelection():
    widget = bufferStateWidget({"shotA": ["a0"]})
    before = gui.MyWidget.snapshotBufferState(widget)

    widget.imgDict["ContactSheetChannels"].append("diffuse")
    assert gui.MyWidget.snapshotBufferState(widget) != before


def test_bufferStateIsStableWhenNothingChanges():
    widget = bufferStateWidget({"shotA": ["a0"]})

    assert gui.MyWidget.snapshotBufferState(widget) == \
        gui.MyWidget.snapshotBufferState(widget)


def test_addingAShotKeepsThePreviouslyRegisteredVersions():
    widget = types.SimpleNamespace(
        seqDict={"shotA": ["a0", "a1"]},
        imgDict={"version": {}},
    )
    gui.MyWidget.buildVersioningDict(widget)
    widget.imgDict["version"]["shotA"]["v_0001"] = ["other0", "other1"]

    # A second shot goes through buildVersioningDict again.
    widget.seqDict["shotB"] = ["b0"]
    gui.MyWidget.buildVersioningDict(widget)

    assert "v_0001" in widget.imgDict["version"]["shotA"]
    assert widget.imgDict["version"]["shotB"]["v_0000"] == ["b0"]


def test_switchingVersionDoesNotDestroyTheStoredList():
    versions = {"v_0000": ["a0", "a1", "a2"], "v_0001": ["b0", "b1", "b2", "b3", "b4"]}

    resized = gui.MyWidget.matchListLen(None, versions["v_0001"], ["x", "y", "z"])

    assert len(resized) == 3
    assert versions["v_0001"] == ["b0", "b1", "b2", "b3", "b4"]


def test_normaliseKeepsFloatsUntouched():
    values = np.array([[0.25, 0.5]], dtype=np.float32)

    assert np.allclose(main.normaliseToFloat(values), [[0.25, 0.5]])


def test_normaliseScalesEightBits():
    values = np.array([[0, 128, 255]], dtype=np.uint8)

    result = main.normaliseToFloat(values)

    assert result.dtype == np.float32
    assert np.allclose(result, [[0.0, 128 / 255, 1.0]])


def test_normaliseScalesSixteenBits():
    values = np.array([[0, 32768, 65535]], dtype=np.uint16)

    result = main.normaliseToFloat(values)

    # The hardcoded /255 made these 257 times too bright, clamping to white.
    assert np.allclose(result, [[0.0, 32768 / 65535, 1.0]])


def test_sixteenBitPngIsNotBlownOut(tmp_path, ocioConfigPath):
    path = str(tmp_path / "grey.png")
    image = np.full((4, 4, 3), 32768, dtype=np.uint16)
    assert cv.imwrite(path, image)

    pixels, width, height, bytesPerLine = main.convertExr(
        path, "sRGB", "sRGB", "None", 0, 1, None, "rgba",
        ocioConfigPath, "sRGB,Standard", False,
    )
    read = np.frombuffer(bytes(pixels), dtype=np.uint8).reshape(height, width, 3)

    assert read.max() < 255


def test_layerNameOfADottedChannel():
    assert main.layerNameOf("diffuse.R") == "diffuse"
    assert main.layerNameOf("light.key.R") == "light.key"


def test_layerNameOfAChannelWithoutADot():
    # Used to collapse to "", which then matched every channel of the file.
    assert main.layerNameOf("Zback") == "Zback"


def test_listChannelsKeepsChannelsWithoutADot(tmp_path):
    path = writeExr(
        tmp_path / "flat.exr",
        {"R": 0.1, "G": 0.2, "B": 0.3, "Zback": 1.0,
         "diffuse.R": 0.1, "diffuse.G": 0.2, "diffuse.B": 0.3},
    )

    channels = main.exrListChannels([path])

    assert "" not in channels
    assert "Zback" in channels


def test_uppercaseRgbaFallsBackToTheFirstLayer(tmp_path):
    path = writeExr(
        tmp_path / "nobeauty.exr",
        {"diffuse.R": 0.1, "diffuse.G": 0.2, "diffuse.B": 0.3},
    )

    # The interface stores "RGBA" in upper case, the test was lower case only.
    assert main.checkFirstExrChannel([path], "RGBA", "rgba") == "diffuse"


def test_frameNumberDetection():
    from pyVexr_timelineGui import isFrameNumber

    assert isFrameNumber("0012") is True
    assert isFrameNumber("movie") is False
    assert isFrameNumber(None) is False
