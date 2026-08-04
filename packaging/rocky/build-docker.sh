#!/usr/bin/env bash
#
# Construit le bundle Rocky Linux dans un conteneur et recupere l'archive.
#
#   packaging/rocky/build-docker.sh              # Rocky 8 (compatible 8 et 9)
#   packaging/rocky/build-docker.sh --rocky 9    # Rocky 9
#   packaging/rocky/build-docker.sh --out-dir /tmp/out
#
# Fonctionne avec docker ou podman. L'archive atterrit dans dist/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

ROCKY_VERSION=8
OUT_DIR="${REPO_ROOT}/dist"
ENGINE="${CONTAINER_ENGINE:-}"
BASE_IMAGE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --rocky)   ROCKY_VERSION="${2:?--rocky attend 8 ou 9}"; shift ;;
        --image)   BASE_IMAGE="${2:?--image attend une image}"; shift ;;
        --out-dir) OUT_DIR="${2:?--out-dir attend un chemin}"; shift ;;
        -h|--help) awk '/^#!/ {next} /^#/ {sub(/^# ?/, ""); print; next} {exit}' "${BASH_SOURCE[0]}"; exit 0 ;;
        *)         echo "option inconnue : $1" >&2; exit 1 ;;
    esac
    shift
done

if [ -z "${ENGINE}" ]; then
    for candidate in docker podman; do
        if command -v "${candidate}" >/dev/null 2>&1; then
            ENGINE="${candidate}"
            break
        fi
    done
fi
[ -n "${ENGINE}" ] || { echo "ni docker ni podman trouve" >&2; exit 1; }

BASE_IMAGE="${BASE_IMAGE:-quay.io/rockylinux/rockylinux:${ROCKY_VERSION}}"
TAG="pyvexr-rocky${ROCKY_VERSION}:builder"
VERSION="${PYVEXR_VERSION:-$(date +%Y%m%d)-g$(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || echo unknown)}"

echo "==> construction (${ENGINE}, ${BASE_IMAGE}, version ${VERSION})"
"${ENGINE}" build \
    -f "${SCRIPT_DIR}/Dockerfile" \
    --build-arg "BASE_IMAGE=${BASE_IMAGE}" \
    --build-arg "PYVEXR_VERSION=${VERSION}" \
    -t "${TAG}" \
    "${REPO_ROOT}"

mkdir -p "${OUT_DIR}"
CONTAINER_ID="$("${ENGINE}" create "${TAG}")"
trap '"${ENGINE}" rm -f "${CONTAINER_ID}" >/dev/null 2>&1 || true' EXIT
"${ENGINE}" cp "${CONTAINER_ID}:/src/dist/." "${OUT_DIR}/"

echo "==> archive(s) disponible(s) :"
ls -lh "${OUT_DIR}"/PyVexr-*-rocky*.tar.gz
