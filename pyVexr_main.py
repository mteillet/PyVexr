# PyVexr is a simple gui app designed to display exr to avoid having to open them in photoshop or other editing softwares
# Using python, pyQt5 and opencv 

#pyVexr_main.py

import cv2 as cv
import numpy as np
import PyOpenColorIO as OCIO
import OpenEXR as exr

def main():
    print("PyVexr pre alpha version")

def loadImg(ocioIn, ocioOut, ocioLook):
    print("PyVexr Loading Button")
    temporaryImg = "exrExamples/RenderPass_Beauty_1.0100.exr"
    exrTempTest(temporaryImg)
    convertedImg = convertExr(temporaryImg, ocioIn, ocioOut, ocioLook)
    return (convertedImg)

def exrTempTest(img):
    img = exr.InputFile(img)
    print(img.header())

        

def initOCIO():
    print("Init OCIO")
    ocioVar = "ocio/config.ocio"
    config = OCIO.Config.CreateFromFile(ocioVar)
    #print(config)

    # Getting displays list from ocio setup
    displays = config.getActiveDisplays()
    #print(displays)

    displayList = config.getDisplays()
    views= config.getViews(displayList[0])
    viewsList = []
    for view in views:
        viewsList.append(view)
    #print(viewsList)
    # Getting ocio colorspaces from config
    colorSpaces = config.getColorSpaces()
    # Building a dictionnary of the colorspaces we get from the ocio
    colorSpacesDict = {}
    for c in colorSpaces:
        # print(dir(c))
        colorSpacesDict[c.getName()] = c

    looks = config.getLooks()
    # Building dict of the looks
    looksDict = {}
    for look in looks:
        looksDict[look.getName()] = look


    return(colorSpacesDict,looksDict, viewsList)


# Converting the Exr file with opencv to a readable image file for QtPixmap
def convertExr(path, ocioIn, ocioOut, ocioLook):
    img = cv.imread(path, cv.IMREAD_ANYCOLOR | cv.IMREAD_ANYDEPTH)
    
    # For debugging purpose, if you need to display the image in open cv to compare
    '''
    img=img*65535
    img[img>65535]=65535
    img=np.uint16(img)
    cv.imshow("Display window", img)
    k = cv.waitKey(0)
    '''

    if(img.dtype == "float32"):
        # Making the actual OCIO Transform
        ocioTransform(img, ocioIn, ocioOut, ocioLook)
        img *= 255
        # Clamping the values to avoid artifacts if values go over 255
        img = clampImg(img)
        # Conversion to the QPixmap format
        img = img.astype(np.uint8)



    rgb_image = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    h,w,ch = rgb_image.shape
    bytes_per_line = ch * w
    convertedImg = rgb_image.data, w, h, bytes_per_line
    return(convertedImg)


def ocioTransform(img, ocioIn, ocioOut, ocioLook):
    print("Using PyOpenColorIO version 2")
    print("Attempting convesion from {0} to {1} using look {2}".format(ocioIn, ocioOut, ocioLook))

    ocioVar = "ocio/config.ocio"
    config = OCIO.Config.CreateFromFile(ocioVar)
    displays = config.getDisplays()
    views = config.getViews(displays[0])
    # views = [Standard,Filmic,Filmic Log, Raw, False Color]
    looks = config.getLooks()

    # Trying to set a display view transform
    transform = OCIO.DisplayViewTransform()
    transform.setSrc(ocioIn)
    # Defaulting to SRGB here as displays selection has not been set up in the gui
    transform.setDisplay(displays[0])
    transform.setView(ocioOut)

    viewer = OCIO.LegacyViewingPipeline()
    viewer.setDisplayViewTransform(transform)
    if ((ocioOut == "Filmic") | (ocioOut == "AgX")):
        if ocioLook != "None":
            viewer.setLooksOverrideEnabled(True)
            viewer.setLooksOverride(ocioLook)

    view = config.getDefaultView(displays[0])
    

    processor = viewer.getProcessor(config, config.getCurrentContext())
    #processor = config.getProcessor(transform)
    #processor = config.getProcessor(ocioIn, ocioOut)
    cpu = processor.getDefaultCPUProcessor()

    img = cpu.applyRGB(img)

    return(img)

def ocioLooksFromView(view):
    ocioVar = "ocio/config.ocio"
    config = OCIO.Config.CreateFromFile(ocioVar)
    displays = config.getDisplays()
    
    looksObj = config.getLooks()

    # Exception for other views, otherwise the filmic views will be in every views
    if ((view == "Filmic") | (view == "AgX")):
        looks = []
        for i in looksObj:
            looks.append(i.getName())
        if ((view == "Filmic") & ("Medium Contrast" in looks)):
            looks.pop(looks.index("Medium Contrast"))
            looks.insert(0, "Medium Contrast")
            # Removing the AgX Golden look
            looks.pop(looks.index("Golden"))
        if ((view == "AgX") & ("Punchy" in looks)):
            looks.pop(looks.index("Punchy"))
            looks.insert(0, "Punchy")
            # Removing Filmic Looks 
            #looks.pop(looks.index("Medium contrast"))
        looks.append("None")
    else:
        looks = ["None"]
    return(looks)



def clampImg(img):
    img[img>255] = 255
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

    processor = config.getProcessor("Linear", "sRGB")
    cpu = processor.getDefaultCPUProcessor()
    img = cpu.applyRGB(img)


    # Calling filmicBaseContrast
    #filmicBaseContrast(img)


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
