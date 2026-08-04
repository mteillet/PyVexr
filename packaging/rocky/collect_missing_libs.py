#!/usr/bin/env python3
"""
Complete un bundle PyInstaller avec les bibliotheques systeme qu'il n'embarque
pas, pour que le resultat tourne sur une Rocky "minimale".

PyInstaller collecte les dependances qu'il trouve en analysant les binaires,
mais tout ce qui est charge dynamiquement (plugins Qt, dlopen) peut lui
echapper : sur une machine sans environnement graphique complet, PyVexr
s'arrete alors sur "could not load the Qt platform plugin xcb".

Ce script fait la fermeture transitive : pour chaque ELF du bundle, il demande
a ldd ou chaque dependance est resolue (en simulant le LD_LIBRARY_PATH que le
bootloader PyInstaller mettra en place), et recopie dans le bundle celles qui
viennent encore du systeme.

Ne sont volontairement PAS embarquees :
  - la glibc et le loader : ils doivent correspondre au systeme cible,
  - la pile OpenGL / DRM / drivers Nvidia : elle doit correspondre au materiel,
  - libxcb.so.1 et libxcb-dri* : ABI qui bouge souvent, et toujours presents
    des qu'il y a une pile graphique.
Cette liste est alignee sur celle de PyInstaller (PyInstaller/depend/dylib.py),
pour ne pas reintroduire ce qu'il exclut sciemment.

Usage : collect_missing_libs.py <dossier_du_bundle>
"""

import os
import re
import shutil
import subprocess
import sys

DENYLIST = [
    # glibc et loader
    r"ld-linux.*\.so(\..*)?",
    r"ld64\.so(\..*)?",
    r"lib(c|dl|m|pthread|rt|util|nsl|resolv|crypt|anl|cidn|thread_db|BrokenLocale)\.so(\..*)?",
    r"libnss_.*\.so(\..*)?",
    # pile graphique (doit venir de la machine cible)
    r"libE?(Open)?GLX?(ESv1_CM|ESv2)?(dispatch)?\.so(\..*)?",
    r"libglapi\.so(\..*)?",
    r"libdrm.*\.so(\..*)?",
    r"libgbm\.so(\..*)?",
    r"lib(EGL|GLX)_nvidia\.so(\..*)?",
    r"libnvidia-.*\.so(\..*)?",
    r"libcuda(debugger)?\.so(\..*)?",
    # ABI instable, fourni avec la pile graphique
    r"libxcb\.so(\..*)?",
    r"libxcb-dri.*\.so(\..*)?",
]
DENY_RE = re.compile("^(" + "|".join(DENYLIST) + ")$")

RESOLVED_RE = re.compile(r"^\s*(\S+)\s+=>\s+(/\S+)\s+\(0x[0-9a-f]+\)\s*$")
NOT_FOUND_RE = re.compile(r"^\s*(\S+)\s+=>\s+not found\s*$")


def is_elf(path):
    try:
        with open(path, "rb") as handle:
            return handle.read(4) == b"\x7fELF"
    except OSError:
        return False


def elf_files(bundle):
    for dirpath, _dirnames, filenames in os.walk(bundle):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            if ".so" in filename or os.access(path, os.X_OK):
                if is_elf(path):
                    yield path


def library_dirs(bundle):
    """Dossiers du bundle contenant des .so, comme vus a l'execution."""
    dirs = {bundle}
    for dirpath, _dirnames, filenames in os.walk(bundle):
        if any(".so" in name for name in filenames):
            dirs.add(dirpath)
    return sorted(dirs)


def dependencies(path, ld_library_path):
    """Retourne (dependances resolues {soname: chemin}, sonames introuvables)."""
    env = dict(os.environ, LD_LIBRARY_PATH=ld_library_path)
    try:
        result = subprocess.run(
            ["ldd", path], capture_output=True, text=True, env=env, check=False
        )
    except OSError:
        return {}, set()

    resolved = {}
    not_found = set()
    for line in result.stdout.splitlines():
        match = RESOLVED_RE.match(line)
        if match:
            resolved[match.group(1)] = match.group(2)
            continue
        match = NOT_FOUND_RE.match(line)
        if match:
            not_found.add(match.group(1))
    return resolved, not_found


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    bundle = os.path.abspath(argv[1])
    if not os.path.isdir(bundle):
        print("bundle introuvable : {}".format(bundle), file=sys.stderr)
        return 1

    copied = []
    left_to_system = set()
    unresolved = set()

    for _round in range(12):
        ld_library_path = os.pathsep.join(library_dirs(bundle))
        candidates = {}
        for path in elf_files(bundle):
            resolved, not_found = dependencies(path, ld_library_path)
            for soname, source in resolved.items():
                if os.path.realpath(source).startswith(bundle + os.sep):
                    continue  # deja dans le bundle
                candidates.setdefault(soname, source)
            unresolved |= {name for name in not_found if not DENY_RE.match(name)}

        progressed = False
        for soname, source in sorted(candidates.items()):
            if DENY_RE.match(soname):
                left_to_system.add(soname)
                continue
            destination = os.path.join(bundle, soname)
            if os.path.exists(destination):
                continue
            shutil.copy2(os.path.realpath(source), destination)
            os.chmod(destination, 0o755)
            copied.append(soname)
            progressed = True

        if not progressed:
            break

    for soname in copied:
        print("ajoutee au bundle  : {}".format(soname))
    for soname in sorted(left_to_system):
        print("laissee au systeme : {}".format(soname))
    if unresolved:
        print(
            "ATTENTION, dependances introuvables sur la machine de build : {}".format(
                ", ".join(sorted(unresolved))
            ),
            file=sys.stderr,
        )
    print("{} bibliotheque(s) systeme ajoutee(s) au bundle".format(len(copied)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
