"""
Logique pure de l'interface, testee sans ouvrir de fenetre.

Les methodes visees ne touchent pas a Qt : on les appelle sur un faux `self`
plutot que d'instancier MyWidget, ce qui garde ces tests instantanes.
"""

import types

import pytest
from PyQt5 import QtCore

import pyVexr_gui as gui
import pyVexr_main as main


def fakeWidget(seqDict, currentPos, timelineLength=None):
    """Un objet minimal exposant ce que lisent les methodes testees."""
    if timelineLength is None:
        timelineLength = sum(len(frames) for frames in seqDict.values())
    return types.SimpleNamespace(
        seqDict=seqDict,
        timeLineDict={index: {} for index in range(timelineLength)},
        frameNumber=types.SimpleNamespace(
            slider=types.SimpleNamespace(value=lambda: currentPos)
        ),
    )


def test_interpretRectangleReadsAQRectF():
    rectangle = QtCore.QRectF(12.0, -4.5, 100.0, 50.0)

    assert main.interpretRectangle(str(rectangle)) == (12.0, -4.5, 100.0, 50.0)


def test_interpretRectangleReadsAQRect():
    rectangle = QtCore.QRect(0, 0, 800, 600)

    assert main.interpretRectangle(str(rectangle)) == (0.0, 0.0, 800.0, 600.0)


def test_matchListLenPadsTheShorterList():
    result = gui.MyWidget.matchListLen(None, ["a", "b"], [1, 2, 3, 4, 5])

    assert len(result) == 5
    assert set(result) == {"a", "b"}


def test_matchListLenTrimsTheLongerList():
    result = gui.MyWidget.matchListLen(
        None, ["a", "b", "c", "d", "e"], [1, 2, 3]
    )

    assert len(result) == 3


def test_matchListLenKeepsEqualLengthsUntouched():
    result = gui.MyWidget.matchListLen(None, ["a", "b", "c"], [1, 2, 3])

    assert result == ["a", "b", "c"]


@pytest.mark.xfail(
    strict=True,
    reason="bug connu : matchListLen modifie la liste de versions stockee "
           "(corrige en phase 2)",
)
def test_matchListLenDoesNotMutateItsInput():
    versions = ["a", "b", "c", "d", "e"]

    gui.MyWidget.matchListLen(None, versions, [1, 2, 3])

    assert versions == ["a", "b", "c", "d", "e"]


def test_relativeFrameIndexOnASingleShot():
    widget = fakeWidget({"shotA": ["f0", "f1", "f2"]}, currentPos=2)

    assert gui.MyWidget.getRelativeFrameIndex(widget) == 2


def test_relativeFrameIndexInsideTheSecondShot():
    widget = fakeWidget(
        {"shotA": ["a0", "a1", "a2"], "shotB": ["b0", "b1", "b2"]},
        currentPos=4,
    )

    assert gui.MyWidget.getRelativeFrameIndex(widget) == 1


def test_relativeFrameIndexClampsBeyondTheTimeline():
    widget = fakeWidget({"shotA": ["f0", "f1", "f2"]}, currentPos=99)

    assert gui.MyWidget.getRelativeFrameIndex(widget) == 2


@pytest.mark.xfail(
    strict=True,
    reason="bug connu : sur la premiere image du second plan l'index renvoye "
           "sort de la liste du plan (corrige en phase 1)",
)
def test_relativeFrameIndexOnTheFirstFrameOfTheSecondShot():
    seqDict = {"shotA": ["a0", "a1", "a2"], "shotB": ["b0", "b1", "b2"]}
    widget = fakeWidget(seqDict, currentPos=3)

    index = gui.MyWidget.getRelativeFrameIndex(widget)

    assert index == 0
    assert seqDict["shotB"][index] == "b0"
