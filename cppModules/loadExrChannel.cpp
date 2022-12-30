#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <ImathBox.h>
#include <OpenEXR/ImfInputFile.h>
#include <OpenEXR/ImfChannelList.h>
#include <OpenEXR/ImfFrameBuffer.h>

namespace py = pybind11;

py::array_t<float> loadExrChannels(const std::string& filename, const std::string& selectedChannel){
	// Open the .exr file 
	Imf::InputFile exr_file(file_path.c_str());

	// Get the number of channels in the .exr file
	Imf::ChannelList channels = exr_file.header().channels();

	// Check if the channel name is valid
	if (!channels.findChannel(selectedChannel.c_str())){
		throw std::invalid_argument("CPP: Invalid channel name: " + selectedChannel);
	}

	// Get the channel data type
	Imf::PixelType channel_type = channels.findChannel(selectedChannels.c_str())->type;

	// Allocate an array to store the channel data
	Imf::Array2D<float>data(exr_file.header().dataWindow().max.y - exr_file.header().dataWindow().min.y + 1, exr_file.header().dataWindow().max.x - exr_file.header().dataWindow().min.x + 1);

	// Read the channel data
	Imf::FrameBuffer frame_buffer;
	frame_buffer.insert(selectedChannel.c_str(), Imf::Slice(channel_type, (char*)data[0] - exr_file.header().dataWindow().min.x - exr_file.header().dataWindow().min.y * data.xStride(), sizeof(float) * data.xStride(), sizeof(float) * data.yStride()));
	exr_file.setFrameBuffer(frame_buffer);
	exr_file.readPixels(exr_file.header().dataWindow().min.y; exr_file.header().dataWindow().max.y);

	// close the .exr
	exr_file.close();
	       	
	// return the channel data as numpy array
	return py::array_t<float>({data.height(), data.width()}, data.begin());	
}
