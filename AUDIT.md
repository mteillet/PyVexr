# Audit de PyVexr

Relecture complète de `pyVexr_gui.py`, `pyVexr_main.py`, `pyVexr_timelineGui.py`,
`cppModules/` et de l'organisation du dépôt. Chaque constat indique où il se
trouve, ce qu'il provoque concrètement, et son statut sur cette branche.

Les correctifs sont répartis en commits relisibles séparément :

| Commit | Contenu |
|---|---|
| `Add a test harness before refactoring` | tests, ruff, CI — **avant** toute modification |
| `Fix the crashes found by the audit` | exceptions certaines |
| `Fix the silent bugs found by the audit` | résultats faux sans erreur |
| `Make the buffer and playback thread safe and bounded` | threads, cache, mémoire |
| `Cache the OCIO processors and stop leaking EXR handles` | performance |
| `Resolve resources from the module, not from argv` | chemins et préférences |
| `Split the GUI and clear the dead code` | structure et lisibilité |
| `Clean up the repository` | hygiène du dépôt |

Vérification : 80 tests (unitaires, non-régression image, test de fumée lançant
réellement l'application sans affichage), `ruff check` propre, et le bundle
Rocky reconstruit par la CI.

---

## 1. Plantages certains

| # | Où | Effet | Statut |
|---|---|---|---|
| 1.1 | `pyVexr_gui.py` `customExpoMenu` | `self.expopop` au lieu de `self.expoPop` : le menu *Custom Exposure* lève `AttributeError`, la fenêtre ne s'ouvre jamais | corrigé |
| 1.2 | `pyVexr_main.py` contact sheet | `saturationTweak` appelé avec 2 arguments sur 3 : toute saturation ≠ 1 en mode contact sheet est un `TypeError` | corrigé |
| 1.3 | `pyVexr_main.py` contact sheet | une seule couche laisse `img` non liée → `UnboundLocalError` | corrigé |
| 1.4 | `pyVexr_main.py` `exrSwitchChannel` | canal alpha demandé sur un EXR sans alpha : `channelR/G/B` jamais assignées → `UnboundLocalError` | corrigé (image noire) |
| 1.5 | `pyVexr_gui.py` `getRelativeFrameIndex` | comparait une longueur de plan à une position globale : sur la première image du second plan, l'index renvoyé sort de la liste du plan → `IndexError` | corrigé |
| 1.6 | `pyVexr_gui.py` `queueResult` | résultat de worker écrit sans contrôle de bornes après un reset de buffer | corrigé |
| 1.7 | `pyVexr_gui.py` `exportPlaylist` | `os.getlogin()` lève sans terminal de contrôle : export impossible depuis un lanceur de bureau | corrigé (`getpass`) |
| 1.8 | `pyVexr_gui.py` × 5 dialogues | annuler une boîte de fichier continuait comme si un chemin avait été donné : fichiers nommés `.pyVexr`, `.mp4`, `.jpg`, ouverture d'un chemin vide | corrigé |
| 1.9 | `pyVexr_gui.py` `checkIfJsonExists` | `config.json` incomplet, corrompu, ou pointant vers un OCIO disparu : l'application ne démarre plus du tout, sans recours | corrigé (repli sur les valeurs par défaut) |
| 1.10 | `pyVexr_timelineGui.py` `pixelPosToRangeValue` | clic sur la timeline décalé d'une image, `-1` au bord gauche, division par zéro avant le premier layout | corrigé |
| 1.11 | `pyVexr_main.py` fin de fichier | `if __name__ == "__main__": main()` avec `main` non défini | corrigé |

## 2. Bugs silencieux — résultat faux, aucune erreur

### 2.1 Les exports MP4 et JPEG sortaient sans transformation d'affichage

`convertForVideo` ignorait le retour de `ocioTransformDefault`, alors que
`convertExr` l'affecte. Avec le bouton OCIO désactivé, tout ce qui était
exporté était donc du linéaire brut multiplié par 255, nettement plus sombre
que ce que montrait le viewer. **Corrigé.**

### 2.2 La transformation OCIO d'affichage était décalée de deux flottants

`ocioTransform2` passait la vue inversée `img[...,::-1]` à `applyRGB`. OCIO lit
son entrée comme un tampon RGB compact et **ignore les strides** : le pointeur
reçu était celui du troisième flottant de l'image, donc tout était traité
décalé, et la fin dépassait l'allocation de deux flottants.

Mesuré sur le config livré, image non uniforme 4×4 :

| Vue | Pixels faux | Écart max |
|---|---|---|
| Standard | 1/16 (le premier) | 55 niveaux |
| Filmic | 1/16 | 8 niveaux |
| AgX | 16/16 | 82 niveaux |
| False Color | 16/16 | 255 niveaux |

Les vues qui mélangent les canaux (LUT 3D) étaient donc **entièrement**
fausses. La transformation passe maintenant par une copie RGB contiguë, et
`tests/test_ocio_transform.py` compare le résultat à une transformation
calculée directement avec PyOpenColorIO, pour quatre vues. **Corrigé** — les
deux empreintes correspondantes de `tests/convert_reference.json` ont été
régénérées, c'est le seul changement d'image volontaire.

À noter : la fonction retournait aussi `None` (`img = cpu.applyRGB(img)`, qui
renvoie `None`), sans conséquence car les trois appelants ignoraient le retour.

### 2.3 Dépassement mémoire dans `loadExrChannel.cpp`

Les `Slice` étaient déclarées avec le type de pixel du fichier alors que les
tableaux de destination étaient toujours des `Array2D<half>` : sur un EXR
FLOAT — exactement ce que demande le code Python — OpenEXR écrivait 4 octets
par échantillon dans une allocation de 2, sur toute l'image. Le module lit
maintenant dans des tampons `float`, valide les trois noms de canaux (seul le
premier l'était) et la taille du vecteur. **Corrigé.**

### 2.4 Onze décalages binaires écrits à la place de comparaisons

`if (current+count >> self.frameNumber.slider.maximum())` est un décalage à
droite, nul pour toute valeur réaliste : la garde de bouclage du buffer était
du code mort, la fin de la plage n'était donc jamais mise en cache et
l'`IndexError` qui en résultait était avalée par un `except IndexError: pass`.
Même chose avec `<<` dans le contact sheet, où le remplissage noir de la
dernière ligne ne s'exécutait jamais. **Corrigé** (et le `except` supprimé).

### 2.5 Le cache n'était jamais invalidé par un changement de plans

`bufferState["frame"] = self.seqDict.keys()` stocke une **vue** du
dictionnaire : l'état mémorisé et l'état courant pointaient sur le même objet
et comparaient donc toujours égal. Ajouter ou retirer un plan laissait des
images périmées dans le cache. Les douze affectations dupliquées sont
maintenant un seul `snapshotBufferState()`. **Corrigé.**

### 2.6 Les listes de versions étaient détruites à l'usage

`matchListLen` faisait ses `insert`/`del` **sur la liste stockée** dans
`imgDict["version"]` : basculer vers une version plus courte puis revenir
détruisait définitivement la liste d'images. Et `buildVersioningDict`
réinitialisait tout le dictionnaire à chaque ajout de plan, effaçant les
versions enregistrées par l'utilisateur. **Corrigés.**

### 2.7 Fenêtres qui appliquent des réglages toutes seules

- La fenêtre OCIO connectait ses combos **avant** de les remplir : `addItem`
  déclenchait `currentIndexChanged` et écrasait les réglages du viewer avec le
  premier élément de chaque liste. « Cancel » ne restaurait rien. Corrigé
  (`blockSignals`, sélection des valeurs réelles, restauration à l'annulation).
- La fenêtre Contact Sheet appelait `self.toggleBtn.click()` à la
  construction : ouvrir la fenêtre basculait le mode et vidait le cache avant
  tout choix de couche. Corrigé.

### 2.8 Lecture d'images

| Où | Problème | Statut |
|---|---|---|
| chemin `.mov` / `.mp4` | `del split[-2]` exécuté même quand le numéro d'image ne parsait pas (`movie.mov` devenait `"mov"`) | corrigé |
| chemin `.mov` / `.mp4` | numérotation 1-based envoyée à `CAP_PROP_POS_FRAMES` qui est 0-based : décalage d'une image | corrigé |
| chemin `.mov` / `.mp4` | `success` jamais vérifié (→ `TypeError` plus loin), `capture` jamais libérée | corrigé |
| `convertExr` | `/255` en dur : les PNG/TIFF 16 bits sortaient 257× trop clairs, saturés en blanc | corrigé (échelle selon le dtype) |
| `checkFirstExrChannel` | testait `"rgba"` en minuscules alors que l'interface stocke `"RGBA"` : pas de repli sur la première couche | corrigé |
| `layerNameOf` | un canal sans point (`Zback`) devenait `""`, qui correspondait ensuite à *tous* les canaux | corrigé |
| `exrListChannels` | un EXR R/G/B sans alpha ne proposait aucune couche | corrigé (`RGB` ou `RGBA`) |

### 2.9 Timeline

`rect` périmé refilé au `fillRect` partagé (le repère de lecture était repeint
en gris), polices construites à chaque graduation et jamais appliquées, et un
libellé d'image non numérique (cas des films) interrompait le dessin de la
règle en plein milieu. **Corrigés.**

---

## 3. Threads, cache et mémoire

| # | Constat | Statut |
|---|---|---|
| 3.1 | Les workers recevaient `**self.imgDict`, une copie **superficielle** : `buffer`, `ocio` et `path` étaient les objets mêmes que le thread GUI modifie pendant la lecture | instantané immuable |
| 3.2 | `threadpool.clear()` ne supprime que ce qui n'a pas démarré : les résultats calculés pour un plan précédent atterrissaient dans le nouveau buffer, hors bornes ou — pire — dans les bornes et affichés | compteur de génération |
| 3.3 | Plusieurs workers pouvaient voir le même emplacement vide et décoder le même EXR simultanément | décision côté GUI avant démarrage |
| 3.4 | `setMaxThreadCount(self.maxThreads - 4)` donne **0** sur une machine 4 cœurs : Qt met alors tous les workers en file pour toujours, plus rien n'est mis en cache, sans message | `max(1, …)` partout, minimum 1 dans le réglage |
| 3.5 | Cache sans limite ni éviction : une timeline 4K de 200 images ≈ 4,7 Go résidents, libérables seulement par le menu *Reset Buffer* | budget mémoire (4 Go par défaut) + éviction des images les plus éloignées de la tête de lecture |
| 3.6 | Lecture : un `QRunnable` dormant par image de la timeline, `connect` après `start` (premier signal perdable), `clear()` incapable d'arrêter celui qui dort (une image de trop après pause), et dérive du 24 i/s | un seul `QTimer` |
| 3.7 | Aucun `closeEvent` : quitter pendant la mise en cache laisse des workers manipuler des objets Python pendant la finalisation de l'interpréteur | `clear()` + `waitForDone()` |
| 3.8 | `cachePos` : liste sans dédoublonnage, un repaint complet par image terminée ; la timeline ralentissait au fil de la session | `set` + repaints groupés (50 ms) |
| 3.9 | `QueueThread` / `BufferThread` jamais instanciées, et exécutant leur travail dans le thread appelant | supprimées |
| 3.10 | Les modules C++ ne relâchaient pas le GIL : le « multithreading » annoncé sérialisait sur la partie coûteuse | `gil_scoped_release` |

---

## 4. Performance du pipeline image

Mesuré sur un EXR 512×512, config livré, sRGB/Standard : **30 ms → 26 ms par
image**.

- Le config OCIO et les deux processeurs CPU sont construits une fois par jeu
  de réglages au lieu d'une fois par image dans chaque thread. Le gain est plus
  modeste que ce que laissait craindre la lecture du code, parce qu'OCIO 2.3
  possède déjà un cache interne de processeurs — mais le fichier n'est plus
  relu à chaque image.
- `saturationTweak` et `getLooks` passent par ce même config au lieu de
  reparser l'ensemble pour lire quelques coefficients.
- Tous les `EXR.InputFile` sont fermés (`try/finally`). Aucun ne l'était :
  sous le buffer multithread, les descripteurs s'accumulaient vers `EMFILE`.
- `loadExrChan` est enfin branché sur le chemin multicouche, avec repli
  Python : son unique appel était une ligne commentée alors que l'import, lui,
  était obligatoire.
- `np.fromstring` (déprécié, et bloquant pour numpy 2) → `np.frombuffer`.

Répartition des 26 ms restants : 12 ms de décodage EXR, 10 ms d'application
OCIO. Ce sont des coûts réels, pas du gaspillage.

**Non retenu** : supprimer l'aller-retour BGR→RGB (`cv.merge` inversé puis
`cvtColor` final). Le gain mesuré est de l'ordre de 0,3 ms alors que la
convention d'ordre des canaux traverse tout le fichier, y compris le chemin
`cv.imread` qui produit du BGR nativement.

---

## 5. Chemins et préférences

`pyVexr_gui.py` et `pyVexr_main.py` calculaient chacun leur racine à partir de
`sys.argv[0]`, avec **deux formules différentes** (`absPath` et `realPath`) qui
divergent dès que le répertoire courant n'est pas celui du script : les
préférences OCIO étaient écrites via l'une et relues via l'autre, donc
« Save Config » semblait fonctionner mais n'avait aucun effet au démarrage
suivant. Un lancement par lien symbolique ou depuis un autre dossier cassait
aussi le splash, l'icône et le config OCIO, et le découpage manuel sur `"/"`
ne tenait pas sous Windows.

Tout passe désormais par `pyVexr_paths.py` (`APP_DIR` basé sur `__file__`, ou
sur l'exécutable quand l'application est gelée). `config.json` est écrit dans
le dossier de configuration de la plateforme (`XDG_CONFIG_HOME/PyVexr`,
`APPDATA`, `Application Support`) et toujours relu à côté de l'application s'il
y a été laissé par une version précédente — ce qui règle au passage la
sauvegarde des préférences sur une installation en lecture seule, limitation
documentée du bundle Rocky.

---

## 6. Structure et lisibilité

- `pyVexr_gui.py` (2500 lignes) est découpé : `pyVexr_buffer.py` (worker),
  `pyVexr_popups.py` (les six fenêtres secondaires), `pyVexr_paths.py`.
- Les fenêtres secondaires lisaient le global `widget` ; elles reçoivent
  maintenant la fenêtre principale en argument. Le test de fumée les ouvre
  toutes les six.
- `interpretRectangle` analysait le `repr()` d'un `QRectF` — un texte qui n'est
  pas une API, qui change selon les versions de sip, et recalculé à chaque
  mouvement de souris. Il utilise les accesseurs.
- `listChannels` vide correctement son layout : seuls les boutons étaient
  retirés et `removeWidget()` sur un espaceur est sans effet, donc un
  `addStretch` fuyait à chaque changement de plan.
- Supprimés : `updateSaturation` défini deux fois, la fonction morte `ocio()`,
  douze variables inutilisées, les imports morts, les blocs
  `try: X except: X` qui rappellent la même fonction en avalant tout.
- Codes de touches bruts → constantes `QtCore.Qt.Key_*`, et
  `keyPressEvent` appelle `super()` (les touches non gérées n'étaient pas
  transmises).
- Opérateurs `&`/`|` utilisés comme booléens, `== True`, `== None` : convertis.

**Restant, non traité** : le global `widget` que lit encore `graphicsView`, et
`MyWidget` qui reste une grosse classe. Les enlever demande de repenser le
passage de la fenêtre principale aux gestionnaires d'événements ; ça se fait
séparément, avec le filet de tests désormais en place.

---

## 7. Hygiène du dépôt

| Constat | Statut |
|---|---|
| Deux `.so` compilés pour CPython 3.8 uniquement, commités et recompilés dans plusieurs commits, avec un import **obligatoire** côté Python : le dépôt ne démarrait pas sur un autre Python | retirés de git, imports optionnels avec repli, `*.so` ignoré |
| `cppModules/.testExposureUpCpp.py.swp` (fichier d'échange vim) commité | supprimé |
| `cppModules/tasks.py` : ne compile qu'un module sur deux, mauvais flags (`c++11`, bibliothèques manquantes), exige `invoke` (listé nulle part) et lance la compilation **à l'import** | remplacé par `cppModules/build.sh`, également utilisé par le build Rocky |
| Scripts de test ad hoc pointant vers `/home/martin/Documents/...` | supprimés, remplacés par `tests/` |
| Aucun test, aucun déclencheur CI sur les pull requests | 80 tests + workflow `Tests` (pytest + ruff) sur PR |
| Pas de `requirements.txt` ni de configuration d'outils à la racine | `requirements.txt`, `requirements-dev.txt`, `pyproject.toml` (ruff, pytest) |
| `.gitignore` de quatre lignes, `config.json` écrit dans l'arbre source | étendu ; le fichier est écrit dans le dossier utilisateur |
| README : `LICENSE.txt` inexistant, « Python 3.7 + », renvoi vers `tasks.py`, aucune instruction pour lancer depuis les sources | corrigé |

**Non retenu** : sortir les 35 Mo de LUTs vers Git LFS. Elles sont déjà dans
l'historique, les retirer casserait les clones existants pour un gain limité.

---

## 8. Ce qui n'a pas été touché, et pourquoi

- **Migration vers l'API moderne d'OpenEXR** (`OpenEXR.File`, qui rend les
  parties multiples et donne directement des tableaux numpy) et vers
  `DisplayViewTransform` en remplacement de `LegacyViewingPipeline` : ces deux
  changements modifient le rendu colorimétrique, ils se décident et se valident
  à l'œil, séparément.
- **`InputFile` ne voit que la partie 0** d'un EXR : les fichiers réellement
  *multi-part* (par opposition à multicouche) n'exposent que les canaux de la
  première partie. C'est la même migration que ci-dessus.
- **Apparence et ergonomie** : inchangées, sauf là où un réglage s'appliquait
  tout seul (§2.7) et où la police des noms de plans et des graduations est
  maintenant réellement appliquée (§2.9).
