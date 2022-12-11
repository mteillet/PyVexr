#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <iostream>
#include <math.h>
#include <stdio.h>

namespace py = pybind11;


py::array_t<float_t> expoUp(const py::array_t<float_t>& image, float_t exponent) {
	//Get a pointer to the image data and dimensions of the array
	auto buf = image.request();
	float_t* data = (float_t*)buf.ptr;
	//int rows = buf.shape[0];
	//int cols = buf.shape[1];
	
	float multFactor = pow(2, exponent);

	//Print the first 10 elements of the image array to verify data
	for (int i = 0; i < buf.size; i++){
		data[i] *= multFactor;
	}
	
	return image;
}

/* 
 * In practice implementation and building of the following
 * implementation and binding code would be located in a
 * separate file
 */


PYBIND11_MODULE(exposureUp, m) {
	// Optional module docstring
	m.doc() = "pybind11 plugin recalculating value of pixel based on exponent";
	// Generates binding code exposing here the add() function to Python
	m.def("expoUp", &expoUp, "A function that recalcultes the value of the pixel based on an exposure function");
}
