#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <iostream>
#include <vector>
#include <math.h>
#include <stdio.h>
#include <ImathExport.h>
#include <ImathBox.h>
#include <OpenEXR/ImfRgba.h>
#include <OpenEXR/ImfMultiPartInputFile.h>
#include <OpenEXR/ImfInputPart.h>
#include <OpenEXR/ImfFrameBuffer.h>
#include <OpenEXR/ImfInputFile.h>
#include <OpenEXR/ImfChannelList.h>
#include <OpenEXR/ImfHeader.h>
#include <OpenEXR/ImfArray.h>

using namespace Imf;
using namespace Imath;
namespace py = pybind11;

std::vector<py::array_t<float>> loadExrChan(const std::string& filename, const std::vector<std::string>& selectedChannels){
	// Open the .exr file 
	Imf::MultiPartInputFile exrFile(filename.c_str());
	std::vector<py::array_t<float>> result;
	Imf::FrameBuffer frameBuffer;

	int partId = 0;

	// Getting the exr part in which the channels are contained
	for (int i = 0; i < exrFile.parts(); i++) {
		if (exrFile.header(i).channels().findChannel(selectedChannels[0].c_str()) != nullptr){
			partId = i;
		}
	}

	// Setting up the image dimensions
	const Imath::Box2i display = exrFile.header(partId).displayWindow();
	const Imath::Box2i data = exrFile.header(partId).dataWindow();
	const Imath::V2i dim(data.max.y - data.min.x + 1, data.max.y - data.min.y + 1);
	// For now setting up a half buffer of image X axis, not sure it is actually what's needed
	half buffer[data.max.y - data.min.x + 1];
	
	// Setting up default as HALF 16-bits
	uint8_t strideMult = 4;
	uint8_t strideOffset = 0;
	uint8_t dataSize = 2;
	Imf::PixelType pixelType = Imf::HALF;

	half* bufferHalfCast = static_cast<half*>(buffer);
	float* bufferFloatCast= (float*)buffer;

	if (exrFile.header(partId).channels().findChannel(selectedChannels[0].c_str())->type== Imf::HALF) {
		strideMult = 3;
	}

	if (exrFile.header(partId).channels().findChannel(selectedChannels[0].c_str())->type== Imf::FLOAT) {
		dataSize = 4;
		pixelType = Imf::FLOAT;
	}

	// Check if data window is smaller than display windos
	// If so, fills the missing regions with black pixels
	if (data.max.x < display.max.x || data.max.y < display.max.y ||
	    data.min.x > display.min.x || data.min.y > display.min.y ) {
		memset(buffer, 0.0f, (data.max.x - data.min.x + 1) * (data.max.y - data.min.y + 1) * (selectedChannels.size() < 3 ? 3 : selectedChannels.size()) * dataSize);
	}

	for (auto& channelName : selectedChannels){
		if (channelName.compare("") == 0) continue;
		if (pixelType == Imf::HALF) {
			frameBuffer.insert(channelName.c_str(), Imf::Slice(pixelType, (char*) &bufferHalfCast[strideOffset], dataSize * (data.max.x - data.min.x + 1) * strideMult, 1, 1, 1.0));	
		}
		else if (pixelType == Imf::FLOAT) {
			frameBuffer.insert(channelName.c_str(), Imf::Slice(pixelType, (char*) &bufferFloatCast[strideOffset], dataSize * (data.max.x - data.min.x + 1) * strideMult, 1, 1,1.0));
		}
		++strideOffset;
	}

	Imf::InputPart inputPart(exrFile, partId);

	inputPart.setFrameBuffer(frameBuffer);
	inputPart.readPixels(data.min.y, data.max.y);

	// If only a single channel is in the vector selectedChannels, copy it to the 2 other ones
	if (selectedChannels.size() < 3) {
		if (pixelType == Imf::FLOAT){
			for (uint32_t y = 0; y < static_cast<uint32_t>(data.max.y - data.min.y + 1); y++) {
				for (uint32_t x = 0; x < static_cast<uint32_t>(data.max.x - data.min.x + 1); x += 3) {
					// red channel
					float rVal = bufferFloatCast[x + y * (data.max.x - data.min.x + 1) * 3];
					// copy red channel to green 
					bufferFloatCast[x + 1 + y * (data.max.x - data.min.x + 1) * 3] = rVal;
					// copy red channel to blue
					bufferFloatCast[x + 2 + y * (data.max.x - data.min.x + 1) * 3] = rVal;
				}
			}
		}
		else if(pixelType == Imf::HALF){
			for (uint32_t y = 0; y < static_cast<uint32_t>(data.max.y - data.min.y + 1); y++) {
				for (uint32_t x = 0; x < static_cast<uint32_t>(data.max.x - data.min.x + 1); x += 3) {
					float rVal = bufferHalfCast[x + y * (data.max.x - data.min.x + 1) * 3];
					bufferHalfCast[x + 1 + y * (data.max.x - data.min.x + 1) * 3] = rVal;
					bufferHalfCast[x + 2 + y * (data.max.x - data.min.x + 1) * 3] = rVal;
			
				}
			}
			return(bufferHalfCast);
		}
	}
	/*
	else if (selectedChannels.size() == 3) {
		if (pixelType == Imf::FLOAT){
		}
		else if (pixelType == Imf::HALF){
		}
	}
	*/
}

PYBIND11_MODULE(loadExrChannel, m) {
	m.doc() = "pybind11 plugin retrieving image data from a specific channel contained in an exr";
	m.def("loadExrChan", &loadExrChan, "A function retrieving image data from a specific channel in a multipart EXR");
}
