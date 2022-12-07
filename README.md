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
Built using Python, PyQt5, OpenCV2, OpenExr, and OCIO v2.


# Roadmap
- [x] Load multiple shots in the same timeline
	- [x] Scroll through multiple shots easily
	- [x] Playlist save and opening
		- [X] Add neighbouring shots to shots / playlists
- [x] Easily Pan, Zoom, Mirror the image
- [x] Visualize independently R/G/B/A channels 
	- [x] Luminance view
	- [x] Layer contact sheet
		- [x] Toggle Layer contact sheet mode for frame scrolling
- [x] Switch and visualize other channels in multilayered exrs
- [x] Tweak exposition and saturation on the fly
- [x] Direct .mp4 export from PyVexr, baking in your exposure / saturation tweaks, and your chosen OCIO
	- [ ] Export single frame from PyVexr, with exposure, saturation, and OCIO baked
- [x] Easily accessible OCIOs 
	- [x] OCIO menu GUI 
	- [X] AgX support, with its looks
	- [X] ACES P0, and ACES P1 support
	- [X] Filmic support, with its looks
	- [x] Config.json to remember your favourite OCIO settings
- [x] Buffer
	- [x] MultiThreading
	- [x] Buffer Menu
- [x] Full Python code available
	- [x] Compiled versions
		- [x] Linux (Tested on Ubuntu)
		- [x] Windows
- [ ] Image support :
	- [x] Open EXR
	- [x] Jpeg/Jpg
	- [x] Png
	- [x] Tiff (16 bits not tested yet)
	- [ ] DPX 10 bits
	- [ ] .mov
	- [ ] .mp4
- [ ] Switch between movie and images if they exist in the same folder with the same naming
- [ ] C++ OpenExr backend
- [ ] Infos menu
- [ ] Multiple versions on each shot in order to compare them easily
- [ ] Picker to get values from specific pixels


## Prerequisites
If you want to build the python version in order to modify or plug it in and existing pipe, here's what you need:
```sh
	* Python 3.7 + 
	* PyQt5
	* OpenCV2
	* PyOpenColorIO
	* OpenEXR
```
An executable release for Windows and Linux will soon be released.

## License
Distributed under the MIT License. See `LICENSE.txt` for more information

## Contact
Teillet Martin - martin.teillet@hotmail.fr


### Thanks
Thanks to Dorian Douaud for making the PyVexr Logo<br />
Thanks to Elsksa for his help and advices concerning OCIO handling<br />
Thanks to Sacha Duru for his help regarding pyQt
