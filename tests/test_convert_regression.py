"""
Non-regression de la conversion d'image.

convertExr est le coeur du viewer : c'est lui qui transforme un EXR en pixels
affichables. Ces tests figent le resultat (empreinte des pixels) pour un jeu de
parametres representatif, afin qu'un refactor ne change pas silencieusement
l'image affichee.

Si une difference est intentionnelle, il faut regenerer la reference :

    python tests/test_convert_regression.py --update

et justifier le changement dans AUDIT.md.
"""

import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conftest import ROOT, writeExr  # noqa: E402

import pyVexr_main as main  # noqa: E402

REFERENCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "convert_reference.json")
OCIO_CONFIG = os.path.join(ROOT, "ocio", "config.ocio")

# (nom du cas, canaux de l'EXR, parametres de convertExr)
CASES = [
    (
        "rgba_neutre",
        {"R": 0.25, "G": 0.5, "B": 0.75, "A": 1.0},
        dict(exposure=0, saturation=1, channel=None, channelRGBA="rgba",
             ocioToggle=False),
    ),
    (
        "rgba_exposition",
        {"R": 0.25, "G": 0.5, "B": 0.75, "A": 1.0},
        dict(exposure=1.5, saturation=1, channel=None, channelRGBA="rgba",
             ocioToggle=False),
    ),
    (
        "rgba_saturation",
        {"R": 0.25, "G": 0.5, "B": 0.75, "A": 1.0},
        dict(exposure=0, saturation=0.4, channel=None, channelRGBA="rgba",
             ocioToggle=False),
    ),
    (
        "rgba_luma",
        {"R": 0.25, "G": 0.5, "B": 0.75, "A": 1.0},
        dict(exposure=0, saturation=1, channel=None, channelRGBA="luma",
             ocioToggle=False),
    ),
    (
        "couche_diffuse",
        {"R": 0.25, "G": 0.5, "B": 0.75, "A": 1.0,
         "diffuse.R": 0.1, "diffuse.G": 0.2, "diffuse.B": 0.3},
        dict(exposure=0, saturation=1, channel="diffuse", channelRGBA="rgba",
             ocioToggle=False),
    ),
    (
        "ocio_srgb_standard",
        {"R": 0.25, "G": 0.5, "B": 0.75, "A": 1.0},
        dict(exposure=0, saturation=1, channel=None, channelRGBA="rgba",
             ocioToggle=True),
    ),
    (
        "ocio_filmic",
        {"R": 0.25, "G": 0.5, "B": 0.75, "A": 1.0},
        dict(exposure=0.5, saturation=1, channel=None, channelRGBA="rgba",
             ocioToggle=True, ocioOut="Filmic Log"),
    ),
]


def renderCase(directory, name, channels, params):
    path = writeExr(os.path.join(directory, "{}.exr".format(name)), channels)

    converted = main.convertExr(
        path,
        params.get("ocioIn", "Linear"),
        params.get("ocioOut", "sRGB"),
        params.get("ocioLook", "None"),
        params["exposure"],
        params["saturation"],
        params["channel"],
        params["channelRGBA"],
        OCIO_CONFIG,
        params.get("ocioDisplay", "sRGB,Standard"),
        params["ocioToggle"],
    )

    pixels, width, height, bytesPerLine = converted
    digest = hashlib.sha256(bytes(pixels)).hexdigest()
    return {
        "sha256": digest,
        "width": width,
        "height": height,
        "bytesPerLine": bytesPerLine,
    }


def loadReference():
    with open(REFERENCE_PATH, "r") as handle:
        return json.load(handle)


@pytest.mark.parametrize("name,channels,params", CASES,
                         ids=[case[0] for case in CASES])
def test_convertedImageDidNotChange(tmp_path, name, channels, params):
    reference = loadReference()
    assert name in reference, (
        "cas absent de la reference, relancer "
        "python tests/test_convert_regression.py --update"
    )

    assert renderCase(str(tmp_path), name, channels, params) == reference[name]


def updateReference():
    import tempfile

    directory = tempfile.mkdtemp()
    reference = {}
    for name, channels, params in CASES:
        reference[name] = renderCase(directory, name, channels, params)
    with open(REFERENCE_PATH, "w") as handle:
        json.dump(reference, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("reference ecrite dans {}".format(REFERENCE_PATH))


if __name__ == "__main__":
    if "--update" in sys.argv:
        updateReference()
    else:
        print(__doc__.strip())
