<br />
<div align="center">
	<h1 align="center">PyVexr</h1>
	
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
- [x] Easily accessible OCIO v2 menu
	- [x] OCIO menu GUI v2
	- [x] Config.json to remember your favourite OCIO settings
- [x] Buffer
	- [x] MultiThreading
	- [ ] Add option to toggle on / off the buffer
- [x] Full Python code available
	- [ ] Compiled versions
- [ ] Option to add neighbouring shots even after the first ones have been loaded
- [ ] DPX (10 bit) read support
- [ ] Load and save the PyVexr playlist directly in order to save viewing sessions containing multiple shots
- [ ] Direct .mp4 export from PyVexr, baking in your exposure / saturation tweaks, and your chosen OCIO
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
Thanks to Elsksa for his help and advices concerning OCIO handling
Thanks to Sacha Duru for his help regarding pyQt
