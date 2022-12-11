# importing the cpp example
import exposureUp
import time
import math


def main():
    t0 = time.time()
    pythonTest = pow(5,3)
    t1 = time.time()
    tPython = t1 - t0

    print("Python test for {} took {}".format(pythonTest, tPython))

    t0 = time.time()
    cppTest = exposureUp.expoUp(5,3)
    t1 = time.time()
    tCpp = t1-t0

    print("C++ test for {} took {}".format(cppTest, tCpp))


    # Comparing cpp vs python code runtime
    compareRuntimes(tPython, tCpp)


def compareRuntimes(tPython, tCpp):
    if tPython < tCpp:
        print("Python code was faster")
    else:
        print("Cpp code was faster")



if __name__ == "__main__":
    main()
