"""
Fixtures partagees : de petits EXR generes a la volee.

Rien n'est ajoute au depot : les images sont ecrites dans le tmp_path de
pytest, ce qui garde les tests independants de toute donnee externe (les
anciens scripts de cppModules pointaient vers /home/martin/...).
"""

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import Imath  # noqa: E402
import OpenEXR  # noqa: E402

WIDTH = 16
HEIGHT = 12


def writeExr(path, channelValues, width=WIDTH, height=HEIGHT,
             pixelType=Imath.PixelType.FLOAT):
    """
    Ecrit un EXR contenant exactement les canaux demandes.
    channelValues : {"nom du canal": valeur constante}
    """
    header = OpenEXR.Header(width, height)
    channel = Imath.Channel(Imath.PixelType(pixelType))
    header["channels"] = {name: channel for name in channelValues}

    dtype = np.float32 if pixelType == Imath.PixelType.FLOAT else np.float16
    pixels = {
        name: np.full((height, width), value, dtype=dtype).tobytes()
        for name, value in channelValues.items()
    }

    out = OpenEXR.OutputFile(str(path), header)
    out.writePixels(pixels)
    out.close()
    return str(path)


@pytest.fixture
def rgbExr(tmp_path):
    """EXR simple R/G/B, sans alpha."""
    return writeExr(tmp_path / "rgb.exr", {"R": 0.25, "G": 0.5, "B": 0.75})


@pytest.fixture
def rgbaExr(tmp_path):
    """EXR R/G/B/A."""
    return writeExr(
        tmp_path / "rgba.exr", {"R": 0.25, "G": 0.5, "B": 0.75, "A": 1.0}
    )


@pytest.fixture
def multiLayerExr(tmp_path):
    """EXR multicouche : beauty + une passe diffuse + un Z."""
    return writeExr(
        tmp_path / "multi.exr",
        {
            "R": 0.25, "G": 0.5, "B": 0.75, "A": 1.0,
            "diffuse.R": 0.1, "diffuse.G": 0.2, "diffuse.B": 0.3,
            "specular.R": 0.6, "specular.G": 0.7, "specular.B": 0.8,
            "Z": 12.0,
        },
    )


@pytest.fixture
def halfExr(tmp_path):
    """EXR encode en half, pour verifier le chemin HALF de la lecture."""
    return writeExr(
        tmp_path / "half.exr",
        {"R": 0.25, "G": 0.5, "B": 0.75},
        pixelType=Imath.PixelType.HALF,
    )


@pytest.fixture
def exrSequence(tmp_path):
    """
    Une sequence de 5 images nommee shotA.####.exr, plus une image d'une
    autre sequence dans le meme dossier pour verifier le regroupement.
    """
    directory = tmp_path / "seq"
    directory.mkdir()
    frames = []
    for frameNumber in range(1, 6):
        frames.append(
            writeExr(
                directory / "shotA.{}.exr".format(str(frameNumber).zfill(4)),
                {"R": 0.25, "G": 0.5, "B": 0.75},
            )
        )
    other = writeExr(
        directory / "shotB.0001.exr", {"R": 0.1, "G": 0.1, "B": 0.1}
    )
    return {"directory": str(directory), "frames": frames, "other": other}


@pytest.fixture
def ocioConfigPath():
    """Le config OCIO livre avec le depot."""
    return os.path.join(ROOT, "ocio", "config.ocio")
