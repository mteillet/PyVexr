#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <iostream>
#include <vector>
#include <math.h>
#include <stdio.h>
#include <ImathExport.h>
#include <ImathBox.h>
#include <OpenEXR/ImfFrameBuffer.h>
#include <OpenEXR/ImfInputFile.h>
#include <OpenEXR/ImfChannelList.h>
#include <OpenEXR/ImfHeader.h>
#include <OpenEXR/ImfArray.h>

using namespace Imf;
using namespace Imath;
namespace py = pybind11;

std::vector<py::array_t<float>> loadExrChan(const std::string& filename, const std::vector<std::string>& selectedChannel){
	// Open the .exr file 
	Imf::InputFile exr_file(filename.c_str());

	// img height and width
	Header header = exr_file.header();
	int width = header.dataWindow().max.x - header.dataWindow().min.x + 1;
	int height = header.dataWindow().max.y - header.dataWindow().min.y + 1;

	// Data type
	ChannelList channels = header.channels();
	
	// Check if channel names are valid
	if (!channels.findChannel(selectedChannel[0].c_str())){
		throw std::invalid_argument("CPP: invalid channel name: " + selectedChannel[0]);			
	}

	Channel channel = channels[selectedChannel[0].c_str()];
	PixelType pixelType = channel.type;

	// Allocate a frame buffer to hold image data
	size_t sampleSize = sizeof(float);
	Array2D<half> channelDataR(height, width);
	Array2D<half> channelDataG(height, width);
	Array2D<half> channelDataB(height, width);
	// Try to replace the 3 arrays by this vector next : 
	std::vector<Array2D<half>*> channelData = {&channelDataR, &channelDataG, &channelDataB};

	if(pixelType == HALF){
		sampleSize = sizeof(half);
	}
	int pixel_base = exr_file.header().dataWindow().min.y* (exr_file.header().dataWindow().size().x+1) + exr_file.header().dataWindow().min.x;

	FrameBuffer frameBuffer;
	frameBuffer.insert(selectedChannel[0].c_str(), Slice(pixelType,
			       (char*)channelDataR[0] - pixel_base * sampleSize, 
			       sampleSize, 
			       sampleSize * width));
	frameBuffer.insert(selectedChannel[1].c_str(), Slice(pixelType,
			       (char*)channelDataG[0] - pixel_base * sampleSize, 
			       sampleSize, 
			       sampleSize * width));
	frameBuffer.insert(selectedChannel[2].c_str(), Slice(pixelType,
			       (char*)channelDataB[0] - pixel_base * sampleSize, 
			       sampleSize, 
			       sampleSize * width));

	exr_file.setFrameBuffer(frameBuffer);
	exr_file.readPixels(header.dataWindow().min.y, header.dataWindow().max.y);

	// Casting the half arrats back to float (not handled by pybind11 otherwise)
	Array2D<float> floatDataR(height, width);
	Array2D<float> floatDataG(height, width);
	Array2D<float> floatDataB(height, width);
	std::copy(channelDataR[0],channelDataR[0] + (height * width), floatDataR[0]);
	std::copy(channelDataG[0],channelDataG[0] + (height * width), floatDataG[0]);
	std::copy(channelDataB[0],channelDataB[0] + (height * width), floatDataB[0]);

	py::array_t<float> channelR = py::array_t<float>({channelDataR.height(), channelDataR.width()}, floatDataR[0]);
	py::array_t<float> channelG = py::array_t<float>({channelDataG.height(), channelDataG.width()}, floatDataG[0]);
	py::array_t<float> channelB = py::array_t<float>({channelDataB.height(), channelDataB.width()}, floatDataB[0]);
	// return the channel data as numpy array
	return std::vector<py::array_t<float>>{channelR, channelG, channelB};
}

PYBIND11_MODULE(loadExrChannel, m) {
	m.doc() = "pybind11 plugin retrieving image data from a specific channel contained in an exr";
	m.def("loadExrChan", &loadExrChan, "A function retrieving image data from a specific channel in a multipart EXR");
}
