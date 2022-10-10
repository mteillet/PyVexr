# PyVexr is a simple gui app designed to display exr to avoid having to open them in photoshop or other editing softwares
# Using python, pyQt5 and opencv 

#pyVexr_main.py

import cv2 as cv
import numpy as np
import PyOpenColorIO as OCIO
import OpenEXR as EXR
import threading
import time
import Imath
import glob

class MyThread(threading.Thread):
    def run(self):
        print("{} started !".format(self.getName()))
        time.sleep(10)
        print("{} finished !".format(self.getName()))

def testThread(count):
    for i in range(count):
        myThread = MyThread(name = count, daemon = True)
        myThread.start()

def main():
    print("PyVexr pre alpha version")
    print(threading.currentThread().name)

def seqFromPath(path):
    '''
    Looking for the list of paths
    for each path, compare if the string before the exr is the same or not
    if it is not the same, add to a new list in the dict
    and then scan folder to get the full range looking for files and add them into the dict
    '''
    pathList = {}
    #print(path)
    for i in path:
        seqName, searchPath = fileSearchPath(i)
        if seqName in pathList:
            #print("{} is in the dict".format(seqName))
            pathList[seqName].append(i)
        else:
            pathList[seqName] = [i]

    seqDict = autoRangeFromPath(pathList)

    return(seqDict)

def fileSearchPath(filepath):
    '''
    Taking a filepath as an arg
    Returning the filename - .exr and the frame number as seqName
    Returning the filepath - .exr and the frame number as search path
    '''
    filepath= (filepath.split("/"))
    filename = (filepath[-1]).split(".")
    seqName = (".".join(filename[:-2]))
    searchPath = "{0}/{1}".format("/".join(filepath[:-1]), seqName)
 
    return(seqName, searchPath)

def autoRangeFromPath(pathList):
    '''
    Auto - detecting the exrs having the same path but with different frame numbers from the ones that were opened / drag and dropped
    '''
    seqDict = {}
    for i in pathList:
        #print("Trying to auto-detect frames for the {} sequence".format(i))
        seqName, searchPath = fileSearchPath(pathList[i][0])
        fileList = glob.glob(str(searchPath)+".*.exr")
        fileList.sort()
        seqDict[i] = fileList

    return(seqDict)

        

def loadImg(ocioIn, ocioOut, ocioLook, fileList, exposure, saturation, channel, channelRGBA, ocioVar, ocioDisplay, ocioToggle):
    '''
    Main function responsible for the loading of IMGs
    '''
    temporaryImg = fileList[0]
    
    convertedImg = convertExr(temporaryImg, ocioIn, ocioOut, ocioLook, exposure, saturation, channel, channelRGBA, ocioVar, ocioDisplay, ocioToggle)
    return (convertedImg)


def saturationKernel(img, saturation, coefRGB):
    '''
    Saturation calculations based on luma coefficients
    '''
    imgB, imgG, imgR = cv.split(img)
    luma = imgR * coefRGB[0] + imgG * coefRGB[1] + imgB * coefRGB[2]
    luma3d = np.repeat(luma[:,:, np.newaxis], 3, axis = 2)
    saturated = np.clip(((img - luma3d) * saturation + luma3d), 0, 255)
    

    return(saturated)


def saturationTweak(img, saturation):
    '''
    Check and setup of saturation luma values before actual saturation is applied
    '''
    if saturation != 1:
        # Settings for the luma calculations
        coefRGB = [0.2126, 0.7152, 0.0722]
        rgb = saturationKernel(img,saturation, coefRGB)
    else:
        rgb = img

    return(rgb)

def exrListChannels(path):
    '''
    Function responsible for returning the EXR Channels to the channel pannel
    '''
    exr = EXR.InputFile(path[0])
    # Getting the RAW list of channels
    header = exr.header()
    channelsRaw = (header["channels"])
    dw =  header["dataWindow"]
    # Printing the raw list of channels (listed in alphabetical order)
    channelList = []
    for channel in channelsRaw:

        if "." in channel:
            tempChannel = channel.split(".")
            tempChannel = ".".join(tempChannel[:-1])
        else:
            tempChannel = channel

        if (tempChannel not in channelList) & (channel not in ["R","G","B","A"]):
            channelList.append(tempChannel)
        elif (channel) == "A":
            channelList.insert(0,"RGBA")
    # If RGBA is not in the channel list, then insert RGB, as it means the alpha channel was never found
    if "RGBA" not in channelList:
        channelList.insert(0, "RGB")
    #print(channelList)
    return(channelList)

def exrSwitchChannel(path, channel, channelRGBA):
    '''
    def responsible for returning the R,G,B components of the image, in case 
    a different channel of pass is selected
    '''
    exr = EXR.InputFile(path[0])
    header = exr.header()
    channelsRaw = header["channels"]
    dw = header["dataWindow"]

    # Getting size for the numpy reshape
    isize = (dw.max.y - dw.min.y + 1, dw.max.x - dw.min.x + 1)

    # In case of a change in the timeline, need to check if the channel exists in the new exr
    # Otherwise, goes to None by default
    channelExists = False
    for i in channelsRaw:
        if channel == None: 
            pass
        elif i.startswith(channel) == True:
            channelExists = True

    if (channel != None) & (channelExists != True):
        print("{} not found, going back to RGB".format(channel))
        channel = None

    # Check if the channel is lower or uppercased channel.R or channel.r
    casing = ["R","G","B","A"]
    if("{}.r".format(channel) in list(channelsRaw.keys())):
        casing = ["r","g","b","a"]

    #print(casing[:3])
    foundChannelList = []

    emptyAlpha = False
    # Additionnal tests if R,G,B,A or all channels are selected
    if (channel == "RGBA") | (channel == None):
        if (channelRGBA == "rgba") | (channelRGBA == "luma"):
            foundChannelList = casing[:3]
        elif (channelRGBA == "red"):
            foundChannelList = casing[0]
        elif (channelRGBA == "green"):
            foundChannelList = casing[1]
        elif (channelRGBA == "blue"):
            foundChannelList = casing[2]
        elif (channelRGBA == "alpha"):
            defaultAlpha = "{}.{}".format(channel, casing[3])
            if defaultAlpha in channelsRaw:
                foundChannelList = [defaultAlpha]
            elif casing[3] in channelsRaw:
                foundChannelList = casing[3]
            else:
                emptyAlpha = True
    else:
        for i in channelsRaw:
            if i.startswith(channel) == True:
                foundChannelList.append(i)
            if (channelRGBA == "alpha"):
                defaultAlpha = "{}.{}".format(channel,casing[3])
                if defaultAlpha in channelsRaw:
                    foundChannelList = [defaultAlpha]
                elif casing[3] in channelsRaw:
                    foundChannelList = [casing[3]]
                else:
                    print("empty Alpha")
                    emptyAlpha = True

    # Reorder channels in case the RGB exist but are not in the right order
    if ("{}.{}".format(channel, casing[0]) in foundChannelList) & ("{}.{}".format(channel, casing[1]) in foundChannelList) & ("{}.{}".format(channel, casing[2]) in foundChannelList ) & (foundChannelList != ["{}.{}".format(channel, casing[0]),"{}.{}".format(channel, casing[1]),"{}.{}".format(channel, casing[2])]):
        #print("reorder chans")
        foundChannelList = ["{}.{}".format(channel, casing[0]),"{}.{}".format(channel, casing[1]),"{}.{}".format(channel, casing[2])]


    #print(channel)
    #print(channelsRaw)
    #print(foundChannelList)
    # check for exception containing too many channels
    if len(foundChannelList) >= 4:
        #print("over 3")
        foundChannelList = ["{}.{}".format(channel, casing[0]),"{}.{}".format(channel, casing[1]),"{}.{}".format(channel, casing[2])]

    if len(foundChannelList) == 3:
        channelR = exr.channel("{}".format(foundChannelList[0]), Imath.PixelType(Imath.PixelType.FLOAT)) 
        channelR = np.fromstring(channelR, dtype = np.float32)
        channelR = np.reshape(channelR, isize)
        channelG = exr.channel("{}".format(foundChannelList[1]), Imath.PixelType(Imath.PixelType.FLOAT))
        channelG = np.fromstring(channelG, dtype = np.float32)
        channelG = np.reshape(channelG, isize)
        channelB = exr.channel("{}".format(foundChannelList[2]), Imath.PixelType(Imath.PixelType.FLOAT))
        channelB = np.fromstring(channelB, dtype = np.float32)
        channelB = np.reshape(channelB, isize) 
    elif len(foundChannelList) == 2:
        channelR = exr.channel("{}".format(foundChannelList[0]), Imath.PixelType(Imath.PixelType.FLOAT)) 
        channelR = np.fromstring(channelR, dtype = np.float32)
        channelR = np.reshape(channelR, isize)
        channelG = exr.channel("{}".format(foundChannelList[1]), Imath.PixelType(Imath.PixelType.FLOAT))
        channelG = np.fromstring(channelG, dtype = np.float32)
        channelG = np.reshape(channelG, isize)       
        channelB = np.zeros((isize[1], isize[0], 1), dtype = np.float32)
        channelB = np.reshape(channelB, isize)
    elif len(foundChannelList) == 1:
        channelR = exr.channel("{}".format(foundChannelList[0]), Imath.PixelType(Imath.PixelType.FLOAT)) 
        channelR = np.fromstring(channelR, dtype = np.float32)
        channelR = np.reshape(channelR, isize)
        channelG = channelR 
        channelB = channelR

    if (channelRGBA == "rgba"):
        pass
    elif channelRGBA == "alpha":
        if emptyAlpha == True:
            print("empty")
            channelA = np.zeros((isize[1], isize[0], 1), dtype = np.float32)
            channelA = np.reshape(channelA, isize)
    elif channelRGBA == "red":
        channelB = channelR
        channelG = channelR
    elif channelRGBA == "green":
        channelR = channelG
        channelB = channelG
    elif channelRGBA == "blue":
        channelR = channelB
        channelG = channelB

    # Converting to luma if necessary
    if (channelRGBA == "luma"):
        channelR = (0.299 * channelR) + (0.587 * channelG) + (0.114 * channelB)
        channelG = channelR
        channelB = channelR

    # Channels will be merged by the openCV function later on
    img = channelR, channelG, channelB
    
    return(img)

def initOcio2(ocioVar):
    '''
    Def responsible for populating the ocio menus if no config file is found
    '''
    config = OCIO.Config.CreateFromFile(ocioVar)

    colorSpaces = config.getActiveViews().split(", ")

    color = config.getColorSpaces()

    inputInterp = []
    displays = []
    for i in color:
        if (i.getFamily().lower() in ["linear", "log", "Log"]):
            #print(i.getFamily(),i.getName())
            inputInterp.append(i.getName())
        if (i.getFamily().lower() in ["display", ""]):
            #print(i.getFamily(), i.getName())
            displays.append(i.getName())

    return(colorSpaces,inputInterp,displays)

def getLooks(ocioVar, colorSpace):
    '''
    Def updating looks in ocio menu based on what colorspace is chosen
    '''
    config = OCIO.Config.CreateFromFile(ocioVar)

    looks = config.getLooks()
    looksList = []
    looksList.append("None")

    for i in looks:
        #print("{} - {}".format(i.getProcessSpace(), i.getName()))
        if colorSpace in i.getProcessSpace():
            #print("MATCH !! - {}".format(i.getName()))
            looksList.append(i.getName())


    return(looksList)


def checkFirstExrChannel(path, channel, channelRGBA):
    '''
    Checks if the channel RGB exists in the exr, otherwise returns the first channel
    '''
    exr = EXR.InputFile(path[0])
    header = exr.header()
    channelsRaw = header["channels"]
    #print(channelsRaw)

    current = 0
    if channel in [None, "rgb", "rgba"]:
        if "R" not in channelsRaw:
            if ((list(channelsRaw.keys())[current]) == "Z"):
                current += 1
                tempChan = ((list(channelsRaw.keys())[current]).split("."))[:-1]
                channel = ".".join(tempChan)
            elif (len((list(channelsRaw.keys())[current]).split(".")) == 0) :
                print("Channel Length is not long enough to be read")
                print("Check checkFirstExrChannel in main to fix")
            elif (len((list(channelsRaw.keys())[current]).split(".")) >> 0) :
                tempChan = ((list(channelsRaw.keys())[current]).split("."))[:-1]
                channel = ".".join(tempChan)
    #print("channel will be {}".format(channel))

    return(channel)

# Converting the Exr file with opencv to a readable image file for QtPixmap
def convertExr(path, ocioIn, ocioOut, ocioLook, exposure, saturation, channel, channelRGBA, ocioVar, ocioDisplay, ocioToggle):
    '''
    Main core code
    '''
    path = [path]

    # Checking if a switch back to RGB / default channel will be needed
    channel = checkFirstExrChannel(path, channel, channelRGBA)

    if (channel in [None, "RGB", "RGBA"]) & (channelRGBA == "rgba"):
        # No channel merge will be needed
        img = cv.imread(path[0], cv.IMREAD_ANYCOLOR | cv.IMREAD_ANYDEPTH)
    else:
        splitImg = exrSwitchChannel(path, channel, channelRGBA)
        # Merging the splitted exr channel (in a different order a openCV expects BGR by default)
        img = cv.merge([splitImg[2], splitImg[1], splitImg[0]])

    # For debugging purpose, if you need to display the image in open cv to compare
    '''
    img=img*65535
    img[img>65535]=65535
    img=np.uint16(img)
    cv.imshow("Display window", img)
    k = cv.waitKey(0)
    '''

    # SaturationChange
    if (saturation != 1):
        img = saturationTweak(img, saturation)

    #ExposureChange
    if (exposure != 0):
        img = img * pow(2,float(exposure))


    if(img.dtype == "float32"):
        # Making the actual OCIO Transform
        if ocioToggle == True:
            ocioTransform2(img, ocioIn, ocioOut, ocioLook, ocioVar, ocioDisplay)
        #ocioTransform(img, ocioIn, ocioOut, ocioLook)
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

def ocioTransform2(img, ocioIn, ocioOut, ocioLook, ocioVar, ocioDisplay):
    config = OCIO.Config.CreateFromFile(ocioVar)
    #print(ocioIn)
    #print(ocioOut)
    #print(ocioLook)
    #print(ocioDisplay)

    transform = OCIO.DisplayViewTransform()
    transform.setSrc(ocioIn)
    transform.setDisplay("sRGB")
    transform.setView(ocioOut)

    viewer = OCIO.LegacyViewingPipeline()
    viewer.setDisplayViewTransform(transform)
    if ocioLook != "None":
        viewer.setLooksOverrideEnabled(True)
        viewer.setLooksOverride(ocioLook)


    view = config.getDefaultView(ocioDisplay)

    processor = viewer.getProcessor(config, config.getCurrentContext())

    cpu = processor.getDefaultCPUProcessor()

    #displays = transform.getDisplays()
    img = cpu.applyRGB(img)

    #print(dir(transform))
    #for i in displays:
    #    print(i)

    return(img)


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
