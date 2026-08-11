"""
Correction de la transformation OCIO d'affichage.

OCIO lit son entree comme un tampon RGB compact et ignore les strides : la vue
inversee img[...,::-1] que recevait applyRGB le faisait demarrer deux flottants
plus loin dans l'image. Pour les vues qui melangent les canaux (AgX, False
Color), tous les pixels etaient faux ; pour les autres, seul le premier l'etait,
et la derniere lecture depassait l'allocation.

Ces tests comparent la sortie de convertExr a une transformation calculee
independamment avec PyOpenColorIO : c'est un vrai oracle, pas une empreinte.
"""

import numpy as np
import PyOpenColorIO as OCIO
import pytest

import pyVexr_main as main
from conftest import writeExr


def referenceDisplay(rgb, ocioConfigPath, ocioIn, ocioOut, display, view):
    """Transformation d'affichage calculee directement avec OCIO."""
    config = OCIO.Config.CreateFromFile(ocioConfigPath)
    values = np.array(rgb, dtype=np.float32).reshape(1, 1, 3).copy()

    if ocioIn != ocioOut:
        config.getProcessor(ocioIn, ocioOut).getDefaultCPUProcessor().applyRGB(values)

    transform = OCIO.DisplayViewTransform()
    transform.setSrc(ocioOut)
    transform.setView(view)
    transform.setDisplay(display)
    pipeline = OCIO.LegacyViewingPipeline()
    pipeline.setDisplayViewTransform(transform)
    processor = pipeline.getProcessor(config, config.getCurrentContext())
    processor.getDefaultCPUProcessor().applyRGB(values)

    return np.clip(values[0, 0] * 255, 0, 255).astype(np.uint8)


def convertedPixels(path, ocioConfigPath, ocioOut="sRGB", display="sRGB,Standard"):
    pixels, width, height, bytesPerLine = main.convertExr(
        path, "Linear", ocioOut, "None", 0, 1, None, "rgba",
        ocioConfigPath, display, True,
    )
    return np.frombuffer(bytes(pixels), dtype=np.uint8).reshape(height, width, 3)


@pytest.mark.parametrize("view", ["Standard", "Filmic", "AgX", "False Color"])
def test_displayTransformMatchesOcio(tmp_path, ocioConfigPath, view):
    colour = (0.25, 0.5, 0.75)
    path = writeExr(
        tmp_path / "pixel.exr",
        {"R": colour[0], "G": colour[1], "B": colour[2], "A": 1.0},
    )

    image = convertedPixels(
        path, ocioConfigPath, display="sRGB,{}".format(view)
    )
    expected = referenceDisplay(
        colour, ocioConfigPath, "Linear", "sRGB", "sRGB", view
    )

    # Le premier pixel est celui que le decalage de deux flottants abimait.
    assert tuple(image[0, 0]) == tuple(expected)
    assert tuple(image[-1, -1]) == tuple(expected)


def test_everyPixelIsTransformedTheSameWayOnAFlatImage(tmp_path, ocioConfigPath):
    path = writeExr(
        tmp_path / "flat.exr", {"R": 0.3, "G": 0.6, "B": 0.9, "A": 1.0}
    )

    image = convertedPixels(path, ocioConfigPath, display="sRGB,AgX")

    assert len(np.unique(image.reshape(-1, 3), axis=0)) == 1


def test_transformReturnsTheImageInsteadOfNone(tmp_path, ocioConfigPath):
    image = np.zeros((2, 2, 3), dtype=np.float32)
    image[...] = [0.75, 0.5, 0.25]

    result = main.ocioTransform2(
        image, "Linear", "sRGB", "None", ocioConfigPath, "sRGB,Standard"
    )

    assert result is image
    assert not np.allclose(image, [0.75, 0.5, 0.25])
