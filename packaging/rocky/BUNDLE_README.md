# PyVexr — bundle Rocky Linux

Ce dossier contient une version autonome de PyVexr : Python, PyQt5 (avec son
Qt), OpenCV, OpenColorIO, les bindings OpenEXR, les modules C++ de PyVexr, les
configs OCIO et les images sont deja dedans. Il n'y a rien a installer avec
`pip` ni avec `dnf`.

Teste sur Rocky Linux 8 et 9, x86_64.

## Lancer

```sh
./PyVexr
```

## Installer (optionnel)

```sh
./install.sh                       # ~/.local/share/pyvexr + lanceur + menu
./install.sh --prefix /opt/pyvexr  # ailleurs (droits d'ecriture requis)
./install.sh --uninstall
```

Le script ecrit un lanceur `~/.local/bin/pyvexr` et une entree de menu. Il ne
touche a aucun paquet systeme.

## Bon a savoir

- **Preferences OCIO** : le bouton *Save config* ecrit un `config.json` a cote
  de l'executable. Installez donc le bundle dans un dossier ou vous avez le
  droit d'ecrire (c'est le cas par defaut avec `install.sh`), sinon la
  sauvegarde des preferences echouera.
- **Deplacer le dossier** : deplacez-le entier. `imgs/`, `ocio/` et les
  bibliotheques doivent rester a cote de l'executable.
- **Lancer depuis le PATH** : passez par le lanceur cree par `install.sh` (ou
  un script `exec /chemin/reel/PyVexr "$@"`). Un lien symbolique ne marche pas :
  PyVexr deduit l'emplacement de ses ressources du chemin d'appel.

## Si l'application ne demarre pas

Lancez-la depuis un terminal pour voir le message d'erreur.

`qt.qpa.plugin: Could not load the Qt platform plugin "xcb"` signifie qu'il
manque une bibliotheque X11 tres bas niveau sur la machine. Pour savoir
laquelle :

```sh
QT_DEBUG_PLUGINS=1 ./PyVexr 2>&1 | grep -i "cannot load\|not found"
```

Puis, en general :

```sh
sudo dnf install libxkbcommon-x11 libSM libICE xcb-util-image \
     xcb-util-keysyms xcb-util-renderutil xcb-util-wm mesa-libGL
```

La pile OpenGL (`mesa-libGL` / driver proprietaire) n'est volontairement pas
embarquee : elle doit correspondre au materiel et au driver de la machine.

## Licence

MIT — voir `LICENSE`.
