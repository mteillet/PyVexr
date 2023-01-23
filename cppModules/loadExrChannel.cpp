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

	for (int i = 0; i < exrFile.parts(); ++i) {
		Imf::InputPart inputPart(exrFile, i);
		Imf::Header header = inputPart.header();
		int width = header.dataWindow().max.x - header.dataWindow().min.x + 1 ;
		int height = header.dataWindow().max.y - header.dataWindow().min.y + 1;
		Imf::ChannelList channels = inputPart.header().channels();
		Imf::Array2D<Imf::Rgba> pixels(height, width);
		Imf::FrameBuffer frameBuffer;

		// Iterate over all selected channels
		for (const auto& channelName : selectedChannels) {
			// Check if the channel exists in the file
			if (Imf::Channel *channel = channels.findChannel(channelName.c_str())) {
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
			else {
				// Throw an error if the specified channel is not found in the file
				throw std::runtime_error("channel " + channelName + " not found in file");
			}
		}
	}
	return result;
}

PYBIND11_MODULE(loadExrChannel, m) {
	m.doc() = "pybind11 plugin retrieving image data from a specific channel contained in an exr";
	m.def("loadExrChan", &loadExrChan, "A function retrieving image data from a specific channel in a multipart EXR");
}
