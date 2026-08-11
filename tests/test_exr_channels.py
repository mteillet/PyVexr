"""
Lecture des canaux EXR : liste des couches proposees dans l'interface et
extraction des pixels d'une couche donnee.
"""

import numpy as np

import pyVexr_main as main


def test_listChannelsOnRgbaGivesTheBeautyLayer(rgbaExr):
    assert main.exrListChannels([rgbaExr]) == ["RGBA"]


def test_listChannelsOnMultiLayerListsEveryLayerOnce(multiLayerExr):
    channels = main.exrListChannels([multiLayerExr])

    assert channels[0] == "RGBA"
    assert set(channels) == {"RGBA", "Z", "diffuse", "specular"}


def test_listChannelsOnNonExrFallsBackToRgba(tmp_path):
    assert main.exrListChannels([str(tmp_path / "image.png")]) == ["RGBA"]


def test_listChannelsOnRgbWithoutAlphaStillOffersTheBeautyLayer(rgbExr):
    assert main.exrListChannels([rgbExr]) == ["RGB"]


def test_switchChannelReturnsTheRequestedLayer(multiLayerExr):
    red, green, blue = main.exrSwitchChannel([multiLayerExr], "diffuse", "rgba")

    assert red.shape == (12, 16)
    assert np.allclose(red, 0.1)
    assert np.allclose(green, 0.2)
    assert np.allclose(blue, 0.3)


def test_switchChannelReadsTheOtherLayerToo(multiLayerExr):
    red, green, blue = main.exrSwitchChannel([multiLayerExr], "specular", "rgba")

    assert np.allclose(red, 0.6)
    assert np.allclose(green, 0.7)
    assert np.allclose(blue, 0.8)


def test_switchChannelLumaCollapsesToASingleValue(multiLayerExr):
    red, green, blue = main.exrSwitchChannel([multiLayerExr], "diffuse", "luma")

    expected = 0.299 * 0.1 + 0.587 * 0.2 + 0.114 * 0.3
    assert np.allclose(red, expected)
    assert np.allclose(red, green)
    assert np.allclose(green, blue)


def test_checkFirstExrChannelKeepsRgbWhenThePassExists(rgbaExr):
    assert main.checkFirstExrChannel([rgbaExr], None, "rgba") is None


def test_checkFirstExrChannelFallsBackToTheFirstLayer(tmp_path):
    from conftest import writeExr

    path = writeExr(
        tmp_path / "nobeauty.exr",
        {"diffuse.R": 0.1, "diffuse.G": 0.2, "diffuse.B": 0.3},
    )

    assert main.checkFirstExrChannel([path], None, "rgba") == "diffuse"
