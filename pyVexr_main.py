# PyVexr is a simple gui app designed to display exr to avoid having to open them in photoshop or other editing softwares
# Using python, pyQt5 and opencv 

#pyVexr_main.py

import cv2 as cv
import numpy as np
import PyOpenColorIO as OCIO

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
        
        # NOT NEEDED ANYMORE, HANDLED BY THE OCIO
        # Linear to srgb conversion
        #img = linearToSrgb(img)

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
    print("OCIO -- {}".format("Version 2"))

    ocioVar = "ocio/config.ocio"
    config = OCIO.Config.CreateFromFile(ocioVar)
    #print(config)

    # Getting displays list from ocio setup
    displays = config.getActiveDisplays()
    #print(displays)

    # Getting views available for display
    views = config.getViews("sRGB")
    # PRINTING THE VIEWS AVAILABLE
    """
    for view in views:
        print("Available View : {}".format(view))
    """
    # Getting ocio colorspaces from config
    colorSpaces = config.getColorSpaces()
    # Building a dictionnary of the colorspaces we get from the ocio
    for c in colorSpaces:
        # print(dir(c))
        print(c.getName())

    # Getting looks of the view 
    looks = config.getLooks()
    for look in looks:
        #print(dir(look))
        print(look.getName())

    processor = config.getProcessor("Linear", "sRGB")
    cpu = processor.getDefaultCPUProcessor()
    img = cpu.applyRGB(img)


    # Calling filmicBaseContrast
    #filmicBaseContrast(img)

def filmicBaseContrast(img):
    print(" -- FILMIC BASE CONTRAST -- ")

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
