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
	FrameBuffer frameBuffer;
	size_t sampleSize = sizeof(float);
	if (pixelType == HALF){
		Array2D<half> channelDataR(height, width);
	}
	else{
		Array2D<float> channelDataR(height, width);
	}
	Array2D<half> channelDataR(height, width);
	if(pixelType == HALF){
		sampleSize = sizeof(half);
	}
	int pixel_base = exr_file.header().dataWindow().min.y* (exr_file.header().dataWindow().size().x+1) + exr_file.header().dataWindow().min.x;

	frameBuffer.insert(selectedChannel[0].c_str(), Slice(pixelType,
			       (char*)channelDataR[0] - pixel_base * sampleSize, 
			       sampleSize, 
			       sampleSize * width));

	exr_file.setFrameBuffer(frameBuffer);
	exr_file.readPixels(header.dataWindow().min.y, header.dataWindow().max.y);

	Array2D<float> floatData(height, width);
	std::copy(channelDataR[0],channelDataR[0] + (height * width), floatData[0]);

	py::array_t<float> channelR = py::array_t<float>({channelDataR.height(), channelDataR.width()}, floatData[0]);
	// return the channel data as numpy array
	return std::vector<py::array_t<float>>{channelR, channelR, channelR};
}

PYBIND11_MODULE(loadExrChannel, m) {
	m.doc() = "pybind11 plugin retrieving image data from a specific channel contained in an exr";
	m.def("loadExrChan", &loadExrChan, "A function retrieving image data from a specific channel in a multipart EXR");
}
