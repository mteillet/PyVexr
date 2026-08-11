"""
Detection des sequences : fileSearchPath / autoRangeFromPath / seqFromPath.
Ce sont les fonctions qui transforment ce que l'utilisateur ouvre en une
timeline, donc les premieres a proteger avant tout refactor.
"""

import pyVexr_main as main


def test_fileSearchPathSplitsNameFrameAndExtension():
    seqName, searchPath, extension = main.fileSearchPath("/a/b/shotA.0001.exr")
    assert seqName == "shotA"
    assert searchPath == "/a/b/shotA"
    assert extension == "exr"


def test_fileSearchPathKeepsDottedSequenceNames():
    seqName, searchPath, extension = main.fileSearchPath(
        "/a/b/seq001.shotA.0012.exr"
    )
    assert seqName == "seq001.shotA"
    assert searchPath == "/a/b/seq001.shotA"
    assert extension == "exr"


def test_fileSearchPathHandlesFileWithoutFrameNumber():
    seqName, searchPath, extension = main.fileSearchPath("/a/b/still.exr")
    assert seqName == "still"
    assert searchPath == "/a/b/still"
    assert extension == "exr"


def test_autoRangeFindsTheWholeSequenceFromASingleFrame(exrSequence):
    pathList = {"shotA": [exrSequence["frames"][2]]}
    seqDict = main.autoRangeFromPath(pathList, True)

    assert sorted(seqDict["shotA"]) == sorted(exrSequence["frames"])


def test_autoRangeDoesNotMixNeighbouringSequences(exrSequence):
    pathList = {"shotA": [exrSequence["frames"][0]]}
    seqDict = main.autoRangeFromPath(pathList, True)

    assert exrSequence["other"] not in seqDict["shotA"]


def test_autoRangeKeepsOnlyTheGivenFramesWhenAutoLoadIsOff(exrSequence):
    pathList = {"shotA": [exrSequence["frames"][0], exrSequence["frames"][1]]}
    seqDict = main.autoRangeFromPath(pathList, False)

    assert seqDict["shotA"] == exrSequence["frames"][:2]


def test_autoRangeReturnsSortedFrames(exrSequence):
    pathList = {"shotA": [exrSequence["frames"][0]]}
    seqDict = main.autoRangeFromPath(pathList, True)

    assert seqDict["shotA"] == sorted(seqDict["shotA"])


def test_seqFromPathGroupsFramesBySequence(exrSequence):
    seqDict = main.seqFromPath(
        [exrSequence["frames"][0], exrSequence["other"]], True
    )

    assert set(seqDict) == {"shotA", "shotB"}
    assert len(seqDict["shotA"]) == 5
    assert len(seqDict["shotB"]) == 1


def test_seqFromPathWithoutAutoLoadKeepsOnlyTheOpenedFrames(exrSequence):
    seqDict = main.seqFromPath(exrSequence["frames"][:2], False)

    assert seqDict["shotA"] == exrSequence["frames"][:2]
