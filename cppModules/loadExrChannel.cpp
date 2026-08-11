#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <iostream>
#include <vector>
#include <string>
#include <stdexcept>
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

// Reads three channels of an EXR and returns them as float32 numpy arrays.
//
// The pixels are read straight into float buffers with a FLOAT slice, letting
// OpenEXR do the half to float conversion. The previous version declared the
// slices with the pixel type found in the file while the destination arrays
// were always Array2D<half>, so a FLOAT file made OpenEXR write four bytes per
// sample into a two byte per sample allocation, overflowing the heap by a
// factor of two across the whole image.
std::vector<py::array_t<float>> loadExrChan(const std::string& filename, const std::vector<std::string>& selectedChannel){
	if (selectedChannel.size() < 3){
		throw std::invalid_argument("CPP: three channel names are required");
	}

	int width = 0;
	int height = 0;
	std::vector<std::vector<float>> channelData(3);

	{
		// The decode is the expensive part and touches no Python object :
		// without releasing the GIL the buffer threads serialise right here.
		py::gil_scoped_release release;

		InputFile exrFile(filename.c_str());
		Header header = exrFile.header();
		Box2i dataWindow = header.dataWindow();

		width = dataWindow.max.x - dataWindow.min.x + 1;
		height = dataWindow.max.y - dataWindow.min.y + 1;

		// Every requested channel is checked, not just the first one : the
		// missing ones used to surface as an unhelpful exception thrown from
		// inside readPixels.
		const ChannelList& channels = header.channels();
		for (int i = 0; i < 3; ++i){
			if (!channels.findChannel(selectedChannel[i].c_str())){
				throw std::invalid_argument("CPP: invalid channel name: " + selectedChannel[i]);
			}
		}

		const size_t sampleSize = sizeof(float);
		const size_t pixelCount = static_cast<size_t>(width) * static_cast<size_t>(height);
		const long pixelBase = static_cast<long>(dataWindow.min.y) * (dataWindow.size().x + 1)
			+ static_cast<long>(dataWindow.min.x);

		FrameBuffer frameBuffer;
		for (int i = 0; i < 3; ++i){
			channelData[i].assign(pixelCount, 0.0f);
			char* base = reinterpret_cast<char*>(channelData[i].data()) - pixelBase * sampleSize;
			frameBuffer.insert(selectedChannel[i].c_str(),
					   Slice(Imf::FLOAT, base, sampleSize, sampleSize * width));
		}

		exrFile.setFrameBuffer(frameBuffer);
		exrFile.readPixels(dataWindow.min.y, dataWindow.max.y);
	}

	std::vector<py::array_t<float>> result;
	result.reserve(3);
	for (int i = 0; i < 3; ++i){
		result.push_back(py::array_t<float>(
			{static_cast<py::ssize_t>(height), static_cast<py::ssize_t>(width)},
			channelData[i].data()));
	}

	return result;
}

PYBIND11_MODULE(loadExrChannel, m) {
	m.doc() = "pybind11 plugin retrieving image data from a specific channel contained in an exr";
	m.def("loadExrChan", &loadExrChan, "A function retrieving image data from a specific channel in a multipart EXR");
}
