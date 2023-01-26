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





	for (int i = 0; i < exrFile.parts(); ++i) {
		Imf::InputPart inputPart(exrFile, i);
		Imf::Header header = inputPart.header();
		int width = header.dataWindow().max.x - header.dataWindow().min.x + 1 ;
		int height = header.dataWindow().max.y - header.dataWindow().min.y + 1;
		Imf::ChannelList channels = inputPart.header().channels();
		Imf::Array2D<Imf::Rgba> pixels(height, width);

		// Iterate over all selected channels
		for (const auto& channelName : selectedChannels) {
			// Check if the channel exists in the file
			if (!channels.findChannel(channelName.c_str())){
				throw std::runtime_error("channel " + channelName + " not found in file");
			}
			else {
				// Get the channel type
				Imf::PixelType pixelType = channels.findChannel(channelName.c_str())->type;
				// Make the buffer an 16 bits Imf::HALF if pixelType = 1
				std::cout << channelName.c_str() << std::endl;
				// Setup frame buffer for the current channel
				//Imf::Rgba *pixel = &(*pixels.begin());
				frameBuffer.insert(channelName.c_str(), Imf::Slice(Imf::FLOAT, (char*)(&pixels[0][0]), sizeof(Imf::Rgba), sizeof(Imf::Rgba) * pixels.width()));
				inputPart.setFrameBuffer(frameBuffer);
				inputPart.readPixels(inputPart.header().dataWindow().min.y, inputPart.header().dataWindow().max.y);

				// Convert the Array2D to a numpy array
				py::array_t<float> channelData({pixels.height(), pixels.width()});
				auto channelDataBuffer = channelData.request();
				float *channelDataPtr = (float *)channelDataBuffer.ptr;
				for (int i = 0; i < pixels.height(); ++i) {
					for (int j = 0; j < pixels.width(); j++){
					channelDataPtr[i * pixels.width() + j] = pixels[i][j].r;
					}
				}
				result.push_back(channelData);
			} 
		}
	}
	return result;
}

PYBIND11_MODULE(loadExrChannel, m) {
	m.doc() = "pybind11 plugin retrieving image data from a specific channel contained in an exr";
	m.def("loadExrChan", &loadExrChan, "A function retrieving image data from a specific channel in a multipart EXR");
}
