#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <iostream>
#include <math.h>
#include <stdio.h>

namespace py = pybind11;


// Multiplies every sample by 2^exponent, in place.
//
// The array type is explicit : c_style rejects a non contiguous input that
// would otherwise be walked as if it were packed, and asking for a mutable
// buffer makes the in place write legal. The previous version called
// request() (read only by default) and wrote through the returned pointer,
// which is undefined behaviour on a read only array such as anything coming
// from np.frombuffer.
py::array_t<float> expoUp(py::array_t<float, py::array::c_style> image, float exponent) {
	auto buf = image.request(true);
	float* data = static_cast<float*>(buf.ptr);
	const py::ssize_t size = buf.size;

	const float multFactor = std::pow(2.0f, exponent);

	{
		// Nothing here touches Python : letting the other buffer threads run
		// is free.
		py::gil_scoped_release release;
		for (py::ssize_t i = 0; i < size; i++){
			data[i] *= multFactor;
		}
	}

	return image;
}


PYBIND11_MODULE(exposureUp, m) {
	// Optional module docstring
	m.doc() = "pybind11 plugin recalculating value of pixel based on exponent";
	// Generates binding code exposing here the add() function to Python
	m.def("expoUp", &expoUp, "A function that recalcultes the value of the pixel based on an exposure function");
}
