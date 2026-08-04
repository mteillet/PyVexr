#!/usr/bin/env bash
#
# Installe le bundle PyVexr sur la machine courante.
#
#   ./install.sh                      # installe dans ~/.local/share/pyvexr
#   ./install.sh --prefix /opt/pyvexr # installe ailleurs (droits requis)
#   ./install.sh --uninstall          # retire l'installation utilisateur
#
# Rien n'est ajoute au systeme : le bundle est autonome, on cree seulement un
# lanceur dans ~/.local/bin et une entree de menu.

set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${HOME}/.local/share/pyvexr"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
UNINSTALL=0

while [ $# -gt 0 ]; do
    case "$1" in
        --prefix)    PREFIX="${2:?--prefix attend un chemin}"; shift ;;
        --uninstall) UNINSTALL=1 ;;
        -h|--help)   awk '/^#!/ {next} /^#/ {sub(/^# ?/, ""); print; next} {exit}' "${BASH_SOURCE[0]}"; exit 0 ;;
        *)           echo "option inconnue : $1" >&2; exit 1 ;;
    esac
    shift
done

if [ "${UNINSTALL}" = "1" ]; then
    rm -f "${BIN_DIR}/pyvexr" "${DESKTOP_DIR}/pyvexr.desktop"
    rm -rf "${PREFIX}"
    echo "PyVexr desinstalle (${PREFIX})"
    exit 0
fi

mkdir -p "${PREFIX}" "${BIN_DIR}" "${DESKTOP_DIR}"

if [ "$(cd "${PREFIX}" && pwd)" != "${SELF_DIR}" ]; then
    echo "copie du bundle vers ${PREFIX}"
    cp -a "${SELF_DIR}/." "${PREFIX}/"
fi

# Un vrai script et pas un lien symbolique : PyVexr deduit l'emplacement de
# imgs/ et ocio/ de dirname(sys.argv[0]), il doit donc etre lance par son
# chemin reel.
cat > "${BIN_DIR}/pyvexr" <<EOF
#!/bin/sh
exec "${PREFIX}/PyVexr" "\$@"
EOF
chmod 0755 "${BIN_DIR}/pyvexr"

cat > "${DESKTOP_DIR}/pyvexr.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=PyVexr
GenericName=EXR Viewer
Comment=Open EXR viewer with OCIO support
Exec=${PREFIX}/PyVexr %F
Icon=${PREFIX}/imgs/pyVexr_Icon_512.jpeg
Terminal=false
Categories=Graphics;Viewer;
MimeType=image/x-exr;image/png;image/jpeg;image/tiff;
EOF

command -v update-desktop-database >/dev/null 2>&1 \
    && update-desktop-database "${DESKTOP_DIR}" >/dev/null 2>&1 || true

echo "PyVexr installe dans ${PREFIX}"
echo "lancement : ${BIN_DIR}/pyvexr  (ajoutez ${BIN_DIR} au PATH si besoin)"
