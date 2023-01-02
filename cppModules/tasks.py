# tasks.py
# Building of the cpp module
import invoke

# $ c++ -O3 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes) example.cpp -o example$(python3-config --extension-suffix)

filename = "loadExrChannel.cpp"
moduleName = "loadExrChannel"

invoke.run(
        "c++ -I/usr/local/include/OpenEXR/ -I/usr/local/include/Imath -O3 -Wall -shared -std=c++11 -fPIC "
        "`python3 -m pybind11 --includes ` {0} -o {1}"
        "`python3-config --extension-suffix`".format(filename, moduleName)
)
