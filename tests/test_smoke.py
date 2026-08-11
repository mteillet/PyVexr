"""
Test de fumee : l'application se lance vraiment, charge une sequence et
parcourt la timeline. Tourne en sous-processus avec la plateforme Qt
"offscreen", donc sans serveur graphique.
"""

import os
import subprocess
import sys

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smoke_app.py")


def test_appStartsLoadsASequenceAndQuits():
    environment = dict(os.environ, QT_QPA_PLATFORM="offscreen")

    result = subprocess.run(
        [sys.executable, SCRIPT],
        capture_output=True,
        text=True,
        timeout=300,
        env=environment,
    )

    assert result.returncode == 0, (
        "l'application a quitte avec {}\n--- stdout ---\n{}\n--- stderr ---\n{}"
        .format(result.returncode, result.stdout, result.stderr)
    )
    assert "smoke ok" in result.stdout
