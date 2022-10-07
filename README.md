<br />
<div align="center">
	<h3 align="center">PyVexr</h3>
	
	Open Exr Viewer
</div>


# About The Project
PyVexr is intended to be a lightweight, simple GUI application to preview your EXR files easily using the OCIO you want.
Built using Python, PyQt5, OpenCV2, OpenExr, and OCIO v2.


# Roadmap
- [x] Load multiple shots in the same timeline
	- [x] Scroll through multiple shots easily
- [x] Easily Pan, Zoom, Mirror the image
- [x] Visualize independently R/G/B/A channels 
	- [x] Luminance view
	- [ ] Layer contact sheet
- [x] Switch and visualize other channels in multilayered exrs
- [x] Tweak exposition and saturation on the fly
- [x] Easily accessible OCIIO v2 menu
	- [ ] OCIIO menu GUI v2
- [x] Full Python code available
	- [ ] Compiled versions
- [ ] Config.json to remember your favourite OCIIO settings
- [ ] Picker to get values from specific pixels
- [ ] Direct .mp4 export from PyVexr, baking in your exposure / saturation tweaks, and your chosen OCIIO
- [ ] Buffer 
	- [ ] MultiThreading
- [ ] Load and save the PyVexr playlist directly in order to save viewing sessions containing multiple shots
- [ ] Option to add neighbouring shots even after the first ones have been loaded
- [ ] Multiple versions on each shot in order to compare them easily


### Prerequisites
If you want to build the python version in order to modify or plug it in and existing pipe, here's what you need:
```sh
	* Python 3.7 + 
	* PyQt5
	* OpenCV2
	* PyOpenColorIO
	* OpenEXR
```
An executable release for Windows and Linux will soon be released.

### License
Distributed under the MIT License. See `LICENSE.txt` for more information

## Contact
Teillet Martin - martin.teillet@hotmail.fr
