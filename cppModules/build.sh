#!/usr/bin/env bash
#
# Compile les deux modules C++ de PyVexr pour l'interpreteur courant.
#
#   bash cppModules/build.sh                 # avec le python3 du PATH
#   PYTHON=python3.9 bash cppModules/build.sh
#
# Prerequis : un compilateur C++17, pybind11 (pip install pybind11) et les
# en-tetes OpenEXR/Imath (dnf install OpenEXR-devel, apt install libopenexr-dev).
# Les modules sont optionnels : sans eux PyVexr fonctionne, avec un repli numpy
# pour l'exposition et le lecteur EXR en Python.
#
# packaging/rocky/build-bundle.sh appelle ce script en lui passant
# OPENEXR_CFLAGS et OPENEXR_LIBS pour l'OpenEXR qu'il vient de compiler.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
OUT_DIR="${OUT_DIR:-${SCRIPT_DIR}}"

if ! command -v "${PYTHON}" >/dev/null 2>&1; then
    echo "python introuvable : ${PYTHON}" >&2
    exit 1
fi

if [ -z "${OPENEXR_CFLAGS:-}" ] || [ -z "${OPENEXR_LIBS:-}" ]; then
    if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists OpenEXR; then
        OPENEXR_CFLAGS="$(pkg-config --cflags OpenEXR) -I$(pkg-config --variable=includedir OpenEXR)/OpenEXR"
        OPENEXR_LIBS="$(pkg-config --libs OpenEXR)"
    else
        echo "OpenEXR introuvable via pkg-config ; essai avec /usr/local" >&2
        OPENEXR_CFLAGS="-I/usr/local/include -I/usr/local/include/Imath -I/usr/local/include/OpenEXR"
        OPENEXR_LIBS="-L/usr/local/lib -lOpenEXR -lImath -lIex -lIlmThread"
    fi
fi

EXT_SUFFIX="$("${PYTHON}" -c 'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"))')"
PYBIND_INCLUDES="$("${PYTHON}" -m pybind11 --includes)"

mkdir -p "${OUT_DIR}"

echo "==> exposureUp"
# shellcheck disable=SC2086
c++ -O3 -Wall -shared -std=c++17 -fPIC ${PYBIND_INCLUDES} \
    "${SCRIPT_DIR}/exposureUp.cpp" \
    -o "${OUT_DIR}/exposureUp${EXT_SUFFIX}"

echo "==> loadExrChannel"
# shellcheck disable=SC2086
c++ -O3 -Wall -shared -std=c++17 -fPIC ${PYBIND_INCLUDES} ${OPENEXR_CFLAGS} \
    "${SCRIPT_DIR}/loadExrChannel.cpp" \
    -o "${OUT_DIR}/loadExrChannel${EXT_SUFFIX}" \
    ${OPENEXR_LIBS} -Wl,-rpath,'$ORIGIN'

echo "==> verification de l'import"
PYTHONPATH="${OUT_DIR}" "${PYTHON}" -c \
    'import exposureUp, loadExrChannel; print("  exposureUp et loadExrChannel importes")'
