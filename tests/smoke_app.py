"""
Lance PyVexr sans affichage, charge une petite sequence EXR, se promene dans
la timeline puis quitte. Sert de test de fumee : c'est ce qui aurait attrape
le plantage PyQt5 flottant -> entier dans le painter de la timeline.

Appele en sous-processus par tests/test_smoke.py, ou a la main :

    QT_QPA_PLATFORM=offscreen python tests/smoke_app.py
"""

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

# pyVexr resout ses ressources a partir de sys.argv[0] : en sous-processus il
# faut donc lui presenter le chemin du script principal. Ce reglage disparait
# quand les chemins passeront par un APP_DIR base sur __file__.
sys.argv[0] = os.path.join(ROOT, "pyVexr_gui.py")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtCore, QtWidgets  # noqa: E402

from conftest import writeExr  # noqa: E402

import pyVexr_gui  # noqa: E402


def buildSequence(directory):
    frames = []
    for frameNumber in range(1, 6):
        frames.append(
            writeExr(
                os.path.join(
                    directory, "smoke.{}.exr".format(str(frameNumber).zfill(4))
                ),
                {"R": 0.25, "G": 0.5, "B": 0.75, "A": 1.0,
                 "diffuse.R": 0.1, "diffuse.G": 0.2, "diffuse.B": 0.3},
            )
        )
    return frames


def main():
    directory = tempfile.mkdtemp()
    frames = buildSequence(directory)

    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")

    # MyWidget et les fenetres secondaires lisent ces globals, qui ne sont
    # definis que lorsque pyVexr_gui est lance comme script principal.
    pyVexr_gui.app = app

    widget = pyVexr_gui.MyWidget()
    pyVexr_gui.widget = widget
    widget.resize(800, 600)
    widget.show()

    # Chargement d'une sequence, puis parcours de la timeline.
    widget.updateImgDict(frames)
    maximum = widget.frameNumber.slider.maximum()
    for position in range(0, maximum + 1):
        widget.frameNumber.slider.setValue(position)
        app.processEvents()

    # Reglages courants : exposition, saturation, changement de couche.
    widget.imgDict["exposure"] = 1.0
    widget.imgDict["saturation"] = 0.5
    widget.refreshImg()
    app.processEvents()

    widget.imgDict["channel"] = "diffuse"
    widget.refreshImg()
    app.processEvents()

    # Lecture : demarre la minuterie, la laisse tourner, puis l'arrete.
    widget.playBtn.setChecked(True)
    widget.playForward()
    QtCore.QTimer.singleShot(500, app.quit)
    app.exec_()
    playing = widget.playTimer.isActive()
    widget.playBtn.setChecked(False)
    widget.playForward()

    QtCore.QTimer.singleShot(200, app.quit)
    app.exec_()

    if playing is False:
        raise SystemExit("la minuterie de lecture ne tournait pas")
    if widget.playTimer.isActive():
        raise SystemExit("la minuterie de lecture ne s'est pas arretee")

    widget.close()
    print("smoke ok : {} images parcourues".format(maximum + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
