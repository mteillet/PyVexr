# Build Rocky Linux — toutes dependances incluses

Cette chaine produit une archive `PyVexr-<version>-rocky<N>-x86_64.tar.gz` que
l'on decompresse et lance : pas de `pip install`, pas de `dnf install`, pas de
Python a installer sur la machine cible.

Ce qui est embarque dans le bundle :

| Composant | Origine | Version |
|---|---|---|
| CPython | Rocky (`python39`) | 3.9 |
| PyQt5 + Qt5 | wheel PyPI | 5.15.11 / Qt 5.15.19 |
| OpenCV (headless) | wheel PyPI | 4.10.0.84 |
| OpenColorIO | wheel PyPI | 2.3.2 |
| Bindings OpenEXR + Imath | wheel PyPI | 3.4.13 |
| numpy, imageio, pillow | wheels PyPI | voir `requirements.txt` |
| `exposureUp`, `loadExrChannel` | compiles pendant le build | — |
| Imath / OpenEXR C++ | compiles depuis les sources | 3.1.12 / 3.1.13 |
| configs OCIO, LUTs, images | depot | — |

Ne sont volontairement **pas** embarquees : la glibc et la pile OpenGL
(`libGL`, drivers), qui doivent venir de la machine cible. Toutes les autres
bibliotheques systeme utilisees par Qt (xcb, xkbcommon, SM/ICE, fontconfig…)
sont recopiees dans le bundle par `collect_missing_libs.py`.

## Construire

### Avec Docker / Podman (recommande)

```sh
packaging/rocky/build-docker.sh             # Rocky 8
packaging/rocky/build-docker.sh --rocky 9   # Rocky 9
```

L'archive est deposee dans `dist/`.

### Directement sur une machine Rocky

```sh
sudo bash packaging/rocky/build-bundle.sh --install-deps --smoke-test
```

Sans `--install-deps` le script n'installe rien et se contente de verifier ce
qui manque (utile si vous n'etes pas root : faites installer les paquets une
fois, puis lancez le script sans sudo).

### Avec GitHub Actions

Le workflow `.github/workflows/build-rocky.yml` construit les deux versions
(Rocky 8 et 9) et publie les archives en artifacts. Il se declenche a la main
(`workflow_dispatch`) ou sur push touchant le code ou le packaging.

## Quelle version choisir ?

Le bundle **Rocky 8** est construit avec la glibc 2.28 : il fonctionne sur
Rocky 8 **et** Rocky 9 (ainsi que RHEL/AlmaLinux/CentOS Stream equivalents).
Le bundle Rocky 9 est un build natif EL9, a utiliser si vous ne ciblez que
Rocky 9.

## Details d'implementation

- `build-bundle.sh` — toute la logique de build (paquets, Imath/OpenEXR,
  virtualenv, modules C++, PyInstaller, archive). Sert aussi bien dans le
  conteneur qu'en local ; les etapes deja faites sont sautees, on peut donc le
  relancer sans tout refaire.
- `pyvexr.spec` — spec PyInstaller. Le bundle est genere avec
  `contents_directory='.'` : l'executable et ses dependances sont au meme
  niveau, car `pyVexr_gui.py` et `pyVexr_main.py` cherchent `imgs/`, `ocio/` et
  `config.json` a cote de `sys.argv[0]`. `exposureUp` et `loadExrChannel` sont
  declares en `hiddenimports` puisqu'ils sont importes via un
  `sys.path.append()` dynamique.
- `collect_missing_libs.py` — passe `ldd` sur tout le bundle en simulant le
  `LD_LIBRARY_PATH` du bootloader PyInstaller, et recopie les bibliotheques
  manquantes (notamment celles du plugin Qt `xcb`, charge dynamiquement et donc
  invisible pour l'analyse de PyInstaller).
- `requirements.txt` — versions figees, toutes disponibles en wheel manylinux
  pour CPython 3.9.
- `install.sh` / `BUNDLE_README.md` — copies dans l'archive, pour l'utilisateur
  final.

## Mettre a jour une dependance

Modifier `requirements.txt` (ou `IMATH_VERSION` / `OPENEXR_VERSION` en tete de
`build-bundle.sh`), puis relancer un build. Verifier qu'une wheel manylinux
existe bien pour CPython 3.9 :

```sh
pip download --only-binary=:all: --python-version 3.9 \
    --platform manylinux_2_17_x86_64 --platform manylinux2014_x86_64 \
    --no-deps -d /tmp/whl "opencolorio==2.3.2"
```
