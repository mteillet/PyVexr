# PyVexr is a simple gui app designed to display exr to avoid having to open them in photoshop or other editing softwares
# Using python, pyQt5 and opencv 

#pyVexr_main.py

import cv2 as cv
import numpy as np

def main():
    print("PyVexr pre alpha version")

def loadImg():
    print("PyVexr Loading Button")
    temporaryImg = "exrExamples/RenderPass_Beauty_1.0100.exr"
    convertedImg = convertExr(temporaryImg)
    return (convertedImg)

# Converting the Exr file with opencv to a readable image file for QtPixmap
def convertExr(path):
    img = cv.imread(path, cv.IMREAD_ANYCOLOR | cv.IMREAD_ANYDEPTH)
    
    # For debugging purpose, if you need to display the image in open cv to compare
    '''
    img=img*65535
    img[img>65535]=65535
    img=np.uint16(img)
    cv.imshow("Display window", img)
    k = cv.waitKey(0)
    '''

    # Conversion from float32 to uint8
    # Perform conversion only if the file is not 8 bit integers
    # FOR NOW, THE SECOND VALUE HAS BEEN MULTIPLIED BY 16 IN ORDER TO HAVE BETTER EXPOSURE
    # NEED A WAY TO CORRECTLY SET THE CONVERSION BETWEEN 32 HALF EXR AND UINT8
    if(img.dtype != "uint8"):
        #img = cv.normalize(img, None, 0, 255*16, cv.NORM_MINMAX, cv.CV_8U)
        img[img < 0] = 0

        #Testing the filmic ocio config -- NEED to be converted to a separate function called from a menu later on
        ocio(img)
        
        #img[img > 1] = 1
        # Linear to srgb conversion
        img = linearToSrgb(img)

        # Correct conversion, need to apply a display correction on the image
        # Compare the exr with natron and image is displayed in linear space instead of SRGB
        img *= 255

        # Clamping the max value to avoid inverted brighter pixels 
        img[img>255] = 255

        # Converting to 8 bits for PyQt QPixmap support
        img = img.astype(np.uint8)

    
    #print(img.dtype)

    # Conversion to the QPixmap format
    rgb_image = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    h,w,ch = rgb_image.shape
    bytes_per_line = ch * w
    convertedImg = rgb_image.data, w, h, bytes_per_line
    return(convertedImg)

def linearToSrgb(img):
    img = np.power(img, 0.45)
    return(img)

def ocio(img):
    print("OCIO transform")
    print("Available OCIO configs : \n- Filmic Base Contrast")

    # Calling filmicBaseContrast
    filmicBaseContrast(img)

def filmicBaseContrast(img):
    print(" -- FILMIC BASE CONTRAST -- ")

    # Opening the filmic file
    with open("/home/martin/Documents/PYTHON/PyVexr/ocio/filmic_blender/Filmic_to_0-70_1-03.spi1d", "r") as f:
        data = f.readlines()
    # Removing unecessary lines from the file
    data = (data[5:-1])

    filmicLut = []
    for line in data:
        filmicLut.append(float(line))

    #img = filmicLut[int(img)]
    print(type(img))
    return(img)



def interpretRectangle(str):
    temp = str.split("(")
    temp = temp[1][:-1]
    temp = temp.split(",")
    offsetX = float(temp[0])
    offsetY = float(temp[1])
    lenX = float(temp[2])
    lenY = float(temp[3])
    return(offsetX, offsetY, lenX, lenY)


if __name__ == "__main__":
    main()
