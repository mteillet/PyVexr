#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <ImfInputFile.h>
#include <ImfChannelList.h>
#include <ImfFrameBuffer.h>


using namespace Imf;
using namespace Imath;o

namespace py = pybind11;



py::array_t<float> loadExrChannels(const std::string &filename, const std::string &selectedChannel){
	// Getting the exr specified channel
	InputFile file(filename);

	// Img width / weight
	Box2i dw = file.header().dataWindow();
	int width = dw.max.x - dw.min.x + 1;
	int height = dw.max.y - dw.min.y + 1;

	// Get list of channels
	ChannelList channels = file.header().channels();

	// Create buffer to store img data
	FrameBuffer frameBuffer;

	// Loop through every channel and add the one equal to the channel string
	for (ChannelList::ConstIterator it = channels.begin(); it != channels.end(); ++it) {
		// Get channel Name and data type
		const Channel &channel = it.channel();
		const char *name = channel.name();
		PixelType type = channel.type;

		// Allocate storage for channel data
		size_t size = width * height * sizeof(float);
		float *data = new float[size];

		// Set the channel data in the frame buffer
		if (std::string(name) == selectedChannel) {
			frameBuffer.insert(name, Slice(type, (char *)data, sizeof(float), sizeof(float)*width));
		}
	       	
	}
}
