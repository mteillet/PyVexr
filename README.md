<br />
<div align="center">
	<h1 align="center">PyVexr</h1>
	<img src="/imgs/pyVexr_WhiteBG_githubReadme.jpeg" alt="PyVexr Logo" align="center">	
<br />
<br />
	Open Exr Viewer
</div>


# About The Project
PyVexr is intended to be a lightweight, simple GUI application to preview your EXR files easily using the OCIO you want.
Built using Python, C++, PyQt5, OpenCV2, OpenExr, and OCIO v2.


# Roadmap
- [x] Load multiple shots in the same timeline
	- [x] Scroll through multiple shots easily
	- [x] Playlist save and opening
		- [X] Add neighbouring shots to shots / playlists
	- [X] Multiple versions on each shot in order switch and compare them easily
- [x] Easily Pan, Zoom, Mirror the image
- [x] Visualize independently R/G/B/A channels 
	- [x] Luminance view
	- [x] Layer contact sheet
		- [x] Toggle Layer contact sheet mode for frame scrolling
- [x] Switch and visualize other channels in multilayered exrs
- [x] Tweak exposition and saturation on the fly
- [x] Direct .mp4 export from PyVexr, baking in your exposure / saturation tweaks, and your chosen OCIO
	- [x] Export single frame from PyVexr, with exposure, saturation, and OCIO baked
- [x] Easily accessible OCIOs 
	- [x] OCIO menu GUI 
	- [X] AgX support, with its looks
	- [X] ACES P0, and ACES P1 support (could be better, for now use ACES official configs)
	- [X] Filmic support, with its looks
	- [x] Config.json to remember your favourite OCIO settings
- [x] Buffer
	- [x] MultiThreading
	- [x] Buffer Menu
- [x] Full Python code available
	- [x] Compiled versions
		- [x] Linux (Tested on Ubuntu)
		- [x] Rocky Linux 8 / 9 self contained bundle (see `packaging/rocky`)
		- [x] Windows
- [x] Image support :
	- [x] Open EXR
		- [ ] Need optimization for multilayered / multipart EXRs
	- [x] Jpeg/Jpg
	- [x] Png
	- [x] Tiff (16 bits not tested yet)
	- [x] .mov
		- [ ] Need optimization
	- [x] .mp4
		- [ ] Need optimization
	- [ ] DPX 10 bits
	- [ ] DCP
- [x] C++ OpenExr backend
	- [ ] C++ Multilayer exr optimizations
- [ ] Switch between movie and images if they exist in the same folder with the same naming
- [ ] Picker to get values from specific pixels
- [ ] Convenient command line mode to start the pyVexr with specific shots and OCIO
- [ ] Context Menu on right click to open with PyVexr directly in the explorer


## Run from source
```sh
	python -m venv .venv && . .venv/bin/activate
	pip install -r requirements.txt
	python pyVexr_gui.py
```
Python 3.9 or newer. The dependencies are listed in `requirements.txt` (numpy, PyQt5,
opencv-python-headless, opencolorio, OpenEXR).

### C++ modules
`cppModules/` holds two optional pybind11 modules: `exposureUp` (exposure) and
`loadExrChannel` (multilayer EXR reading). They are **optional**: without them PyVexr falls
back to numpy and to the OpenEXR python bindings. To build them for your interpreter:
```sh
	pip install pybind11        # plus the OpenEXR headers, OpenEXR-devel or libopenexr-dev
	bash cppModules/build.sh
```
The compiled modules are no longer committed: they only work with the exact CPython version
they were built for.

### Tests
```sh
	pip install -r requirements-dev.txt
	pytest          # unit tests, image regression, headless smoke test
	ruff check .
```

## Rocky Linux (self contained build)
A build chain producing a fully self contained bundle for Rocky Linux 8 and 9 lives in
`packaging/rocky`. The resulting archive ships Python, PyQt5 and its Qt, OpenCV, OCIO, the
OpenEXR bindings, the compiled C++ modules, the OCIO configs and the images: nothing has to be
installed with `pip` or `dnf` on the target machine.

```sh
	# in a container (docker or podman)
	packaging/rocky/build-docker.sh             # Rocky 8, also runs on Rocky 9
	packaging/rocky/build-docker.sh --rocky 9

	# or directly on a Rocky machine
	sudo bash packaging/rocky/build-bundle.sh --install-deps --smoke-test
```

The archive lands in `dist/`. Unpack it and run `./PyVexr`, or `./install.sh` to get a launcher
and a menu entry. The GitHub Actions workflow `Build Rocky Linux bundle` builds both versions and
publishes them as artifacts. See `packaging/rocky/README.md` for details.

## Code audit
`AUDIT.md` lists what a full review of the code turned up, what was fixed, and what was
deliberately left alone.

## License
Distributed under the MIT License. See `LICENSE` for more information

## Contact
Teillet Martin - martin.teillet@hotmail.fr


### Thanks
Thanks to Dorian Douaud for making the PyVexr Logo<br />
Thanks to Elsksa and MrLixm for their help and advices concerning OCIO handling<br />
Thanks to Sacha Duru for his help regarding pyQt
