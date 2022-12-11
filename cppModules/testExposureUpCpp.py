import OpenEXR as EXR
import cv2 as cv
import numpy as np
import Imath
import time
import exposureUp


def main():
    openEXR()

def openEXR():
    exr = EXR.InputFile("/home/martin/Documents/BOURDONNEMENT_EXRs/seq001_sh010/set/SEQ001_shotShape10_LPE.0101.exr")
    header = exr.header()

    width = header["dataWindow"].max.x - header["dataWindow"].min.x + 1
    height = header["dataWindow"].max.y - header["dataWindow"].min.y + 1
    isize = (height, width)

    channelsRaw = header["channels"].keys()
    channelList = []
    for chan in channelsRaw:
        channelList.append(chan)

    # Read Image data
    r,g,b = exr.channels([channelList[0],channelList[1],channelList[2]], Imath.PixelType(Imath.PixelType.FLOAT))


    # Convert data to numpy array
    chanR= np.frombuffer(r, dtype = np.float32)
    chanG= np.frombuffer(g, dtype = np.float32)
    chanB= np.frombuffer(b, dtype = np.float32)
    r = np.reshape(chanR, isize)
    g = np.reshape(chanG, isize)
    b = np.reshape(chanB, isize)

    # Merging the channels
    img = cv.merge([r,g,b])
    #print(type(img))


    expoFactor = 5

    # Python
    t0 = time.time()
    pyImg = img * np.power(2, expoFactor)
    t1 = time.time()
    print(t1-t0)


    # CPP test
    t0 = time.time()
    cppImg = exposureUp.expoUp(img, expoFactor)
    t1 = time.time()
    print(t1-t0)


    #img=img*65535
    #img[img>65535]=65535
    #img=np.uint16(img)
    cv.imshow("Display window", cppImg)
    k = cv.waitKey(0)

if __name__ == "__main__":
    main()
