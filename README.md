<br />
<div align="center">
	<h3 align="center">PyVexr</h3>
	
	<p align="center">
	Open Exr Viewer
	</p>
</div>

# OpenExrViewer
Simple Python ,PyQt5, OpenCV, OpenEXR, and OCIO version 2 application to display open Exr files
Its main goal is to have a simple application for viewing your OpenExr files, without having to open nuke, with an easy to use OCIO access, in order to preview your EXRs with AgX or Filmic (Legacy)

## Roadmap

- [x] Load multiple shots in the same timeline
	- [x] Scroll through multiple shots easily
- [x] Visualize independently R/G/B 
	- [x] Luminance view
	- [ ] Layer contact sheet
- [x] Easily Pan, Zoom, Mirror the image
- [x] Switch and visualize other channels in multilayered exrs
- [x] Tweak exposition and saturation on the fly
- [x] OCIIO v2 support
	- [ ] OCIIO menu GUI v2
- [x] Full Python code available
	- [ ] Compiled versions
- [ ] Picker to get values from specific pixels
- [ ] Direct .mp4 export from PyVexr, baking in your exposure / saturation tweaks, and your chosen OCIIO
- [ ] Buffer 
	- [] MultiThreading
- [ ] Load and save the PyVexr playlist directly in order to save viewing sessions containing multiple shots
- [ ] Option to add neighbouring shots even after the first ones have been loaded
- [ ] Multiple versions on each shot in order to compare them easily

