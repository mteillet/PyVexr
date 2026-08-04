#!/usr/bin/env bash
#
# Construit un PyVexr autonome pour Rocky Linux (EL8 / EL9, x86_64).
#
# Le resultat est une archive dist/PyVexr-<version>-rocky<N>-x86_64.tar.gz qui
# contient TOUT ce qu'il faut pour lancer PyVexr : l'interpreteur Python, PyQt5
# et son Qt, OpenCV, OCIO, les bindings OpenEXR, les modules C++ compiles, les
# configs OCIO et les images. Aucune installation Python n'est requise sur la
# machine cible.
#
# Ce script tourne aussi bien dans le conteneur de packaging/rocky/Dockerfile
# que directement sur une machine Rocky :
#
#   sudo bash packaging/rocky/build-bundle.sh --install-deps
#
# Options :
#   --install-deps   installe les paquets systeme necessaires via dnf
#   --only-deps      s'arrete apres les dependances (utile pour le cache Docker)
#   --smoke-test     lance le bundle en mode offscreen pour verifier qu'il demarre
#   --system-openexr utilise l'OpenEXR/Imath du systeme au lieu de le compiler
#   --python BIN     interpreteur a utiliser (defaut : python3.9 si present)
#   --jobs N         parallelisme de compilation (defaut : nproc)
#   --work-dir DIR   dossier de travail (defaut : <repo>/build/rocky)
#   --out-dir DIR    dossier de sortie  (defaut : <repo>/dist)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

WORK_DIR="${WORK_DIR:-${REPO_ROOT}/build/rocky}"
OUT_DIR="${OUT_DIR:-${REPO_ROOT}/dist}"
PYTHON_BIN="${PYTHON_BIN:-}"
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 2)}"
IMATH_VERSION="${IMATH_VERSION:-3.1.12}"
OPENEXR_VERSION="${OPENEXR_VERSION:-3.1.13}"

INSTALL_DEPS=0
ONLY_DEPS=0
SMOKE_TEST=0
SYSTEM_OPENEXR=0

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m/!\\\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mERREUR\033[0m %s\n' "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
    case "$1" in
        --install-deps)   INSTALL_DEPS=1 ;;
        --only-deps)      ONLY_DEPS=1; INSTALL_DEPS=1 ;;
        --smoke-test)     SMOKE_TEST=1 ;;
        --system-openexr) SYSTEM_OPENEXR=1 ;;
        --python)         PYTHON_BIN="${2:?--python attend un chemin}"; shift ;;
        --jobs)           JOBS="${2:?--jobs attend un nombre}"; shift ;;
        --work-dir)       WORK_DIR="${2:?--work-dir attend un chemin}"; shift ;;
        --out-dir)        OUT_DIR="${2:?--out-dir attend un chemin}"; shift ;;
        -h|--help)        awk '/^#!/ {next} /^#/ {sub(/^# ?/, ""); print; next} {exit}' "${BASH_SOURCE[0]}"; exit 0 ;;
        *)                die "option inconnue : $1" ;;
    esac
    shift
done

DEPS_PREFIX="${WORK_DIR}/deps"
VENV_DIR="${WORK_DIR}/venv"
CPP_OUT="${WORK_DIR}/cppModules"
BUNDLE_DIR="${WORK_DIR}/dist/PyVexr"

# ---------------------------------------------------------------------------
# Distribution
# ---------------------------------------------------------------------------
EL_VERSION=""
if [ -r /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    EL_VERSION="${VERSION_ID%%.*}"
    log "distribution detectee : ${PRETTY_NAME:-inconnue}"
fi
case "${EL_VERSION}" in
    8|9|10) ;;
    *) warn "distribution non EL8/EL9 : le bundle sera peut-etre lie a une glibc trop recente"
       EL_VERSION="${EL_VERSION:-9}" ;;
esac

if [ "$(id -u)" -eq 0 ]; then
    SUDO=""
elif command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
else
    SUDO=""
fi

# ---------------------------------------------------------------------------
# 1. Paquets systeme
# ---------------------------------------------------------------------------
install_optional() {
    # Les noms de paquets varient un peu entre EL8 et EL9. On tente tout d'un
    # coup, et seulement si ca echoue on reprend un par un pour identifier le
    # paquet manquant sans faire echouer le build.
    if ${SUDO} dnf -y install "$@" >/dev/null 2>&1; then
        return 0
    fi
    local package
    for package in "$@"; do
        if ! ${SUDO} dnf -y install "${package}" >/dev/null 2>&1; then
            warn "paquet optionnel non installe : ${package}"
        fi
    done
}

install_system_deps() {
    log "installation des paquets systeme (dnf)"
    ${SUDO} dnf -y install dnf-plugins-core >/dev/null 2>&1 || true
    case "${EL_VERSION}" in
        8) ${SUDO} dnf config-manager --set-enabled powertools >/dev/null 2>&1 || true ;;
        *) ${SUDO} dnf config-manager --set-enabled crb        >/dev/null 2>&1 || true ;;
    esac

    ${SUDO} dnf -y install \
        gcc gcc-c++ make cmake git tar gzip xz which findutils file zlib-devel \
        || die "impossible d'installer les outils de compilation"

    if [ "${EL_VERSION}" = "8" ]; then
        ${SUDO} dnf -y install python39 python39-devel python39-pip \
            || die "impossible d'installer python39"
    else
        ${SUDO} dnf -y install python3 python3-devel python3-pip \
            || die "impossible d'installer python3"
    fi

    # Bibliotheques dont Qt a besoin. Elles sont recopiees dans le bundle par
    # collect_missing_libs.py pour que la machine cible n'ait rien a installer.
    install_optional \
        libX11 libXext libXrender libXi libXtst libXrandr libXcursor \
        libXinerama libXfixes libXdamage libXcomposite libXau libxcb \
        libxkbcommon libxkbcommon-x11 xcb-util xcb-util-image xcb-util-keysyms \
        xcb-util-renderutil xcb-util-wm libSM libICE fontconfig freetype \
        dbus-libs expat libpng libjpeg-turbo zlib nss nspr \
        mesa-libGL libglvnd-glx
}

# ---------------------------------------------------------------------------
# 2. Interpreteur Python
# ---------------------------------------------------------------------------
python_is_usable() {
    local candidate="$1"
    command -v "${candidate}" >/dev/null 2>&1 || return 1
    "${candidate}" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 8) else 1)' >/dev/null 2>&1
}

find_python() {
    if [ -n "${PYTHON_BIN}" ]; then
        python_is_usable "${PYTHON_BIN}" || die "python inutilisable : ${PYTHON_BIN}"
        return
    fi
    local candidate
    for candidate in python3.9 python3.11 python3.10 python3; do
        if python_is_usable "${candidate}"; then
            PYTHON_BIN="${candidate}"
            return
        fi
    done
    die "aucun Python >= 3.8 trouve (essayez --install-deps)"
}

check_python_headers() {
    local include_dir
    include_dir="$(${PYTHON_BIN} -c 'import sysconfig; print(sysconfig.get_paths()["include"])')"
    [ -f "${include_dir}/Python.h" ] \
        || die "Python.h introuvable dans ${include_dir} : installez le paquet -devel correspondant"
}

# ---------------------------------------------------------------------------
# 3. Imath + OpenEXR (C++), necessaires pour compiler loadExrChannel
# ---------------------------------------------------------------------------
fetch() {
    local url="$1" destination="$2" attempt
    for attempt in 1 2 3 4; do
        if curl -fsSL --retry 2 -o "${destination}" "${url}"; then
            return 0
        fi
        warn "telechargement echoue (essai ${attempt}) : ${url}"
        sleep $((attempt * 3))
    done
    die "impossible de telecharger ${url}"
}

build_openexr() {
    if [ "${SYSTEM_OPENEXR}" = "1" ]; then
        log "utilisation de l'OpenEXR du systeme (pkg-config)"
        pkg-config --exists OpenEXR \
            || die "OpenEXR introuvable via pkg-config : installez OpenEXR-devel ou retirez --system-openexr"
        OPENEXR_CFLAGS="$(pkg-config --cflags OpenEXR) -I$(pkg-config --variable=includedir OpenEXR)/OpenEXR"
        OPENEXR_LIBS="$(pkg-config --libs OpenEXR)"
        return
    fi

    OPENEXR_CFLAGS="-I${DEPS_PREFIX}/include -I${DEPS_PREFIX}/include/Imath -I${DEPS_PREFIX}/include/OpenEXR"
    OPENEXR_LIBS="-L${DEPS_PREFIX}/lib -lOpenEXR -lImath -lIex -lIlmThread -Wl,-rpath,${DEPS_PREFIX}/lib"

    if [ -f "${DEPS_PREFIX}/lib/libOpenEXR.so" ]; then
        log "Imath/OpenEXR deja compiles dans ${DEPS_PREFIX}"
        return
    fi

    local src="${WORK_DIR}/src"
    mkdir -p "${src}"

    log "compilation d'Imath ${IMATH_VERSION}"
    fetch "https://github.com/AcademySoftwareFoundation/Imath/archive/refs/tags/v${IMATH_VERSION}.tar.gz" \
          "${src}/imath.tar.gz"
    rm -rf "${src}/Imath-${IMATH_VERSION}"
    tar -xzf "${src}/imath.tar.gz" -C "${src}"
    cmake -S "${src}/Imath-${IMATH_VERSION}" -B "${src}/build-imath" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="${DEPS_PREFIX}" \
        -DCMAKE_INSTALL_LIBDIR=lib \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
        -DBUILD_TESTING=OFF \
        -DIMATH_INSTALL_PKG_CONFIG=ON
    cmake --build "${src}/build-imath" -j "${JOBS}"
    cmake --install "${src}/build-imath"

    log "compilation d'OpenEXR ${OPENEXR_VERSION}"
    fetch "https://github.com/AcademySoftwareFoundation/openexr/archive/refs/tags/v${OPENEXR_VERSION}.tar.gz" \
          "${src}/openexr.tar.gz"
    rm -rf "${src}/openexr-${OPENEXR_VERSION}"
    tar -xzf "${src}/openexr.tar.gz" -C "${src}"
    cmake -S "${src}/openexr-${OPENEXR_VERSION}" -B "${src}/build-openexr" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="${DEPS_PREFIX}" \
        -DCMAKE_INSTALL_LIBDIR=lib \
        -DCMAKE_PREFIX_PATH="${DEPS_PREFIX}" \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
        -DBUILD_TESTING=OFF \
        -DOPENEXR_BUILD_TOOLS=OFF \
        -DOPENEXR_INSTALL_TOOLS=OFF \
        -DOPENEXR_INSTALL_EXAMPLES=OFF \
        -DOPENEXR_BUILD_EXAMPLES=OFF
    cmake --build "${src}/build-openexr" -j "${JOBS}"
    cmake --install "${src}/build-openexr"
}

# ---------------------------------------------------------------------------
# 4. Environnement Python
# ---------------------------------------------------------------------------
make_venv() {
    if [ ! -x "${VENV_DIR}/bin/python" ]; then
        log "creation du virtualenv (${PYTHON_BIN})"
        "${PYTHON_BIN}" -m venv "${VENV_DIR}"
    fi
    VENV_PY="${VENV_DIR}/bin/python"
    log "installation des dependances Python"
    "${VENV_PY}" -m pip install --upgrade pip wheel >/dev/null
    "${VENV_PY}" -m pip install -r "${SCRIPT_DIR}/requirements.txt"
}

# ---------------------------------------------------------------------------
# 5. Modules C++ (pybind11)
# ---------------------------------------------------------------------------
build_cpp_modules() {
    log "compilation des modules C++ (pybind11)"
    mkdir -p "${CPP_OUT}"

    local ext_suffix pybind_includes
    ext_suffix="$("${VENV_PY}" -c 'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"))')"
    pybind_includes="$("${VENV_PY}" -m pybind11 --includes)"

    # shellcheck disable=SC2086
    c++ -O3 -Wall -shared -std=c++17 -fPIC ${pybind_includes} \
        "${REPO_ROOT}/cppModules/exposureUp.cpp" \
        -o "${CPP_OUT}/exposureUp${ext_suffix}"

    # shellcheck disable=SC2086
    c++ -O3 -Wall -shared -std=c++17 -fPIC ${pybind_includes} ${OPENEXR_CFLAGS} \
        "${REPO_ROOT}/cppModules/loadExrChannel.cpp" \
        -o "${CPP_OUT}/loadExrChannel${ext_suffix}" \
        ${OPENEXR_LIBS} -Wl,-rpath,'$ORIGIN'

    log "verification de l'import des modules C++"
    PYTHONPATH="${CPP_OUT}" "${VENV_PY}" -c \
        'import exposureUp, loadExrChannel; print("  exposureUp et loadExrChannel importes")'
}

# ---------------------------------------------------------------------------
# 6. Bundle PyInstaller
# ---------------------------------------------------------------------------
run_pyinstaller() {
    log "generation du bundle PyInstaller"
    rm -rf "${WORK_DIR}/dist" "${WORK_DIR}/pyi"
    PYVEXR_ROOT="${REPO_ROOT}" PYVEXR_CPP_MODULES="${CPP_OUT}" \
        "${VENV_DIR}/bin/pyinstaller" \
            --noconfirm \
            --clean \
            --distpath "${WORK_DIR}/dist" \
            --workpath "${WORK_DIR}/pyi" \
            "${SCRIPT_DIR}/pyvexr.spec"

    [ -x "${BUNDLE_DIR}/PyVexr" ] || die "l'executable ${BUNDLE_DIR}/PyVexr n'a pas ete genere"

    log "recuperation des bibliotheques systeme manquantes"
    "${VENV_PY}" "${SCRIPT_DIR}/collect_missing_libs.py" "${BUNDLE_DIR}"

    install -m 0644 "${REPO_ROOT}/LICENSE" "${BUNDLE_DIR}/LICENSE"
    install -m 0755 "${SCRIPT_DIR}/install.sh" "${BUNDLE_DIR}/install.sh"
    install -m 0644 "${SCRIPT_DIR}/BUNDLE_README.md" "${BUNDLE_DIR}/README.md"
}

# ---------------------------------------------------------------------------
# 7. Test de demarrage
# ---------------------------------------------------------------------------
smoke_test() {
    log "test de demarrage (Qt offscreen, 30 s)"
    local status=0
    ( cd "${WORK_DIR}" && QT_QPA_PLATFORM=offscreen timeout 30 "${BUNDLE_DIR}/PyVexr" ) || status=$?
    case "${status}" in
        0)   log "le bundle s'est lance et termine sans erreur" ;;
        124) log "le bundle tourne toujours apres 30 s : demarrage OK" ;;
        *)   die "le bundle a quitte avec le code ${status}" ;;
    esac
}

# ---------------------------------------------------------------------------
# 8. Archive
# ---------------------------------------------------------------------------
package() {
    mkdir -p "${OUT_DIR}"
    local version archive
    # Volontairement pas de git describe : les tags du depot portent des noms de
    # plateforme (v0.0.5-Alpha-Windows) qui n'ont aucun sens ici. Date + commit,
    # ou PYVEXR_VERSION si on veut nommer la release soi-meme.
    version="${PYVEXR_VERSION:-$(date +%Y%m%d)-g$(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || echo unknown)}"
    archive="${OUT_DIR}/PyVexr-${version}-rocky${EL_VERSION}-x86_64.tar.gz"
    log "creation de ${archive}"
    tar -czf "${archive}" -C "${WORK_DIR}/dist" PyVexr
    log "taille : $(du -h "${archive}" | cut -f1)"
    log "termine : ${archive}"
}

# ---------------------------------------------------------------------------
main() {
    mkdir -p "${WORK_DIR}"
    [ "${INSTALL_DEPS}" = "1" ] && install_system_deps
    find_python
    check_python_headers
    log "python utilise : ${PYTHON_BIN} ($(${PYTHON_BIN} -V 2>&1))"
    build_openexr
    make_venv
    if [ "${ONLY_DEPS}" = "1" ]; then
        log "dependances pretes (--only-deps)"
        return 0
    fi
    build_cpp_modules
    run_pyinstaller
    [ "${SMOKE_TEST}" = "1" ] && smoke_test
    package
}

main "$@"
