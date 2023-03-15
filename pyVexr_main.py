# PyVexr is a simple gui app designed to display exr to avoid having to open them in photoshop or other editing softwares
# Using python, pyQt5 and opencv 

#pyVexr_main.py

import os
import numpy as np
import PyOpenColorIO as OCIO
import imageio
import OpenEXR as EXR
import array
import time
import Imath
import math
import glob
import sys
# Setting absPath in order to avoid broken file links when using a compiled version on windows
absPath = os.path.dirname(sys.argv[0])
if absPath:
    absPath = "{}/".format(absPath)
# Adding the cppModules dir to the search path
sys.path.append('{}cppModules'.format(absPath)) 
import exposureUp
import loadExrChannel
# Enabling the EXR format in OpenCv for windows platform
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2 as cv


def bufferBackEnd(imgDict, frameList, current):
    """
    Checks if the buffer corresponding to the index is empty
    If it is empty, calculates the image and sends it back in order to assign it to the
    buffer
    """
    # Check buffer len is ok
    if len(imgDict["buffer"]) >> 0:
        # Check current buffer address is not already computed
        try:
            if (imgDict["buffer"][current] == None):
                #t0 = time.time()
                if (imgDict["ContactSheet"] == False):
                    convertedImg = convertExr(frameList[current], imgDict["ocio"]["ocioIn"], imgDict["ocio"]["ocioOut"], imgDict["ocio"]["ocioLook"], imgDict["exposure"], imgDict["saturation"], imgDict["channel"], imgDict["RGBA"], imgDict["ocioVar"], imgDict["ocio"]["ocioDisplay"], imgDict["ocioToggle"])
                else:
                    imgDict["path"] = [frameList[current]]
                    convertedImg = layerContactSheetBackend(imgDict["ContactSheetChannels"], imgDict)
                #t1 = time.time()
                #print("executed in {} seconds".format(t1 - t0))
                return(convertedImg, current)
            else:
                #print("buffer not empty")
                pass
            if (current < len(imgDict["buffer"])):
                current += 1
        except IndexError:
            #print("Fame Buffer index out of range")
            pass
    else:
        #print("No buffer needed for range")
        pass

    #return(test)


def seqFromPath(path):
    '''
    Looking for the list of paths
    for each path, compare if the string before the exr is the same or not
    if it is not the same, add to a new list in the dict
    and then scan folder to get the full range looking for files and add them into the dict
    '''
    pathList = {}
    movList = {}
    #print(path)
    for i in path:
        if (i.lower().endswith(".mov")) | (i.lower().endswith(".mp4")):
            frameCount, movStruct = detectFrameNumberMov(i)
            # Appending this to movList in case there are many movies
            movList[list(movStruct.keys())[0]] = movStruct[list(movStruct.keys())[0]]
        else:
            seqName, searchPath, extension = fileSearchPath(i)
            if seqName in pathList:
                #print("{} is in the dict".format(seqName))
                pathList[seqName].append(i)
            else:
                pathList[seqName] = [i]


    seqDict = autoRangeFromPath(pathList)
    # Adding the movies to the seqDict
    for mov in movList:
        seqDict[mov] = movList[mov]

    #print("seqDict is : {}".format(seqDict))

    return(seqDict)

def detectFrameNumberMov(filepath):
    '''
    In case file is a .mov, need to build and feed to the timelineGui.py 
    the number of frame to enable scrubbing in the timeline
    Also adds the frame number to the mov filename in order to allow frame
    display on the timelineGui
    '''
    # Getting the frame number from the mov file
    capture = cv.VideoCapture(filepath)
    frameCount = int(capture.get(cv.CAP_PROP_FRAME_COUNT))
    # Getting the name of the move file
    seqName =filepath.split("/")
    seqName = ((seqName[len(seqName)-1]).split("."))[:-1][0]
    movStruct = {}
    movStruct[seqName] = []
    current = 0
    for i in range(frameCount):
        framedPath = filepath.split(".")
        framedPath.insert(-1, str(current+1).zfill(4))
        framedPath = ".".join(framedPath)
        movStruct[seqName].append(framedPath)
        current += 1

    return(frameCount, movStruct)

def fileSearchPath(filepath):
    '''
    Taking a filepath as an arg
    Returning the filename - .exr and the frame number as seqName
    Returning the filepath - .exr and the frame number as search path
    '''
    filepath= (filepath.split("/"))
    filename = (filepath[-1]).split(".")
    extension = filename[len(filename)-1]
    if len(filename) > 3:
        seqName = (".".join(filename[:-2]))
    else:
        seqName = filename[0]
    searchPath = "{0}/{1}".format("/".join(filepath[:-1]), seqName)
    #print(searchPath)
    #print(seqName, searchPath, "is -> {}".format(extension))
 
    return(seqName, searchPath, extension)

def autoRangeFromPath(pathList):
    '''
    Auto - detecting the exrs having the same path but with different frame numbers from the ones that were opened / drag and dropped
    '''
    seqDict = {}
    for i in pathList:
        #print("Trying to auto-detect frames for the {} sequence".format(i))
        extension = pathList[i][0].split(".")
        extension = extension[len(extension) -1]
        #print("{} is extension {}".format(i, extension))
        seqName, searchPath , extension= fileSearchPath(pathList[i][0])
        fileList = glob.glob(str(searchPath)+".*."+ extension)
        # Returning the exr without frame number in case it hasn't been found with a frame number
        if len(fileList) == 0:
            fileList = glob.glob(str(searchPath)+"." + extension)
        fileList.sort()
        seqDict[i] = fileList

    return(seqDict)

        

def loadImg(ocioIn, ocioOut, ocioLook, fileList, exposure, saturation, channel, channelRGBA, ocioVar, ocioDisplay, ocioToggle, imgDict):
    '''
    Main function responsible for the loading of IMGs
    '''
    temporaryImg = fileList[0]
    if (imgDict["ContactSheet"] == False):
        convertedImg = convertExr(temporaryImg, ocioIn, ocioOut, ocioLook, exposure, saturation, channel, channelRGBA, ocioVar, ocioDisplay, ocioToggle)
    else:
        imgDict["path"] = [fileList[0]]
        convertedImg = layerContactSheetBackend(imgDict["ContactSheetChannels"], imgDict)

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


def saturationTweak(img, saturation, ocioVar):
    '''
    Check and setup of saturation luma values before actual saturation is applied
    '''
    if saturation != 1:
        # Getting the actual luma coef RGB from the ocio setup
        config = OCIO.Config.CreateFromFile(ocioVar)
        coefRGB = config.getDefaultLumaCoefs()
        #coefRGB = [0.2126, 0.7152, 0.0722]
        rgb = saturationKernel(img,saturation, coefRGB)
    else:
        rgb = img

    return(rgb)

def exrListChannels(path):
    '''
    Function responsible for returning the EXR Channels to the channel pannel
    '''
    if path[0].endswith(".exr") == True:
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
    else:
        channelList = ["RGBA"]
    # If RGBA is not in the channel list, then insert RGB, as it means the alpha channel was never found
    #if "RGBA" not in channelList:
    #    channelList.insert(0, "RGB")
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


    #print(channelsRaw)
    #print(foundChannelList)
    # check for exception containing too many channels
    if len(foundChannelList) >= 4:
        #print("over 3")
        foundChannelList = ["{}.{}".format(channel, casing[0]),"{}.{}".format(channel, casing[1]),"{}.{}".format(channel, casing[2])]


    if len(foundChannelList) == 3:
        #t0 = time.time()
        channelR,channelG,channelB = exr.channels([foundChannelList[0],foundChannelList[1],foundChannelList[2]], Imath.PixelType(Imath.PixelType.FLOAT)) 
        #t1 = time.time()
        #print("EXR loadChannels python function takes : {}".format(t1-t0))
        #t0 = time.time()
        #channelR,channelG,channelB = loadExrChannel.loadExrChan(path[0], [foundChannelList[0], foundChannelList[1],foundChannelList[2]])
        #t1 = time.time()
        #print("EXR loadChannels CPP function takes : {}".format(t1-t0))
        channelR = np.frombuffer(channelR, dtype = np.float32)
        channelR = np.reshape(channelR, isize)
        channelG = np.frombuffer(channelG, dtype = np.float32)
        channelG = np.reshape(channelG, isize)
        channelB = np.frombuffer(channelB, dtype = np.float32)
        channelB = np.reshape(channelB, isize) 
    elif len(foundChannelList) == 2:
        channelR, channelG = exr.channels([foundChannelList[0], foundChannelList[1]], Imath.PixelType(Imath.PixelType.FLOAT)) 
        channelR = np.frombuffer(channelR, dtype = np.float32)
        channelR = np.reshape(channelR, isize)
        channelG = np.frombuffer(channelG, dtype = np.float32)
        channelG = np.reshape(channelG, isize)       
        channelB = np.zeros((isize[1], isize[0], 1), dtype = np.float32)
        channelB = np.reshape(channelB, isize)
    elif len(foundChannelList) == 1:
        channelR = exr.channel("{}".format(foundChannelList[0]), Imath.PixelType(Imath.PixelType.FLOAT)) 
        channelR = np.frombuffer(channelR, dtype = np.float32)
        channelR = np.reshape(channelR, isize)
        channelG = channelR 
        channelB = channelR

    #t1 = time.time()
    #print(t1 - t0)

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

    ccList, viewList = ocio2Version(config)

    return(ccList,ccList,viewList)

def ocio2Version(config):
    '''
    Listing Colorspaces views and displays based on OCIO2 shared views setup
    '''
    # Getting colorspaces
    ccList = []
    colorspaces = config.getColorSpaceNames()
    for cc in colorspaces:
        ccList.append(cc)
    #print(ccList)

    # Getting linked displays and views
    viewList = []
    displays = config.getDisplays()
    for disp in displays:
        view = config.getViews(disp)
        for v in view:
            viewList.append("{},{}".format(disp, v))
    #print(viewList)

    return(ccList, viewList)

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
    if path[0].endswith(".exr"):
        channel = checkFirstExrChannel(path, channel, channelRGBA)

        if (channel in [None, "RGB", "RGBA"]) & (channelRGBA == "rgba"):
            # No channel merge will be needed
            img = cv.imread(path[0], cv.IMREAD_ANYCOLOR | cv.IMREAD_ANYDEPTH)
        else:
            splitImg = exrSwitchChannel(path, channel, channelRGBA)
            # Merging the splitted exr channel (in a different order a openCV expects BGR by default)
            img = cv.merge([splitImg[2], splitImg[1], splitImg[0]])
    else:
        if path[0].lower().endswith(".dpx"):
            print("DPX file found")
        elif (path[0].lower().endswith(".mov"))|(path[0].lower().endswith(".mp4")):
            #print(".mov file found")
            split = path[0].split(".")
            try:
                frameNumber = int(split[-2])
            except:
                frameNumber = 1
            del split[-2]
            split =".".join(split)
            if len(split) > 3 :
                capture = cv.VideoCapture(split)
            else:
                capture = cv.VideoCapture(path[0])
            capture.set(cv.CAP_PROP_POS_FRAMES, frameNumber)
            success, img = capture.read()
        else:
            img = cv.imread(path[0], cv.IMREAD_ANYCOLOR | cv.IMREAD_ANYDEPTH)
        if (ocioIn == "Linear"):
            ocioIn = "sRGB"
        # Convert img to float 32
        img = np.float32(img/255)

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
        img = saturationTweak(img, saturation, ocioVar)

    #ExposureChange
    if (exposure != 0):
        img = exposureUp.expoUp(img, exposure)

    if(img.dtype == "float32"):
        # Making the actual OCIO Transform
        if ocioToggle == True:
            ocioTransform2(img, ocioIn, ocioOut, ocioLook, ocioVar, ocioDisplay)
        else:
            img = ocioTransformDefault(img, ocioIn, ocioOut, ocioLook, ocioVar, ocioDisplay)
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

def ocioTransformDefault(img, ocioIn, ocioOut, ocioLook, ocioVar, ocioDisplay):
    '''
    Default Ocio transform -- standard
    '''
    img = np.power(img, 0.45)
    
    return(img)


def ocioTransform2(img, ocioIn, ocioOut, ocioLook, ocioVar, ocioDisplay):
    '''
    Custom Ocio transform following the ocio prefs set by user when ocio button is toggled
    '''
    # Need to shuffle the channel order in ocio in order to switch the R and B channels (thanks openCV)
    img = img[...,::-1]

    config = OCIO.Config.CreateFromFile(ocioVar)
    ocioVersion = "{}.{}".format(config.getMajorVersion(), config.getMinorVersion())
    disp, view = ocioDisplay.split(",")

    # Colorpsace conversion if the in and out colorspaces are different
    if ocioIn != ocioOut:
        #print("Conversion from {} to {}".format(ocioIn, ocioOut))
        transform = OCIO.ColorSpaceTransform()
        processor = config.getProcessor(ocioIn, ocioOut)
        cpu = processor.getDefaultCPUProcessor()
        cpu.applyRGB(img)

    # View Transform conversion for display
    transform = OCIO.DisplayViewTransform()
    transform.setSrc(ocioOut)
    transform.setView(view)
    transform.setDisplay(disp)

    viewer = OCIO.LegacyViewingPipeline()
    viewer.setDisplayViewTransform(transform)
    if ocioLook != "None":
        viewer.setLooksOverrideEnabled(True)
        viewer.setLooksOverride(ocioLook)
    processor = viewer.getProcessor(config, config.getCurrentContext())
    cpu = processor.getDefaultCPUProcessor()
    img = cpu.applyRGB(img)

    return(img)

def clampImg(img):
    '''
    Clamping 8 bit RGB values above 255 and below 0 to avoid errors
    '''
    img[img>255] = 255
    img[img<0] = 0
    return(img)

def ocio(img):
    print("OCIO -- {}".format("Version 2"))

    ocioVar = "{}ocio/config.ocio".format(absPath)
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

def createVideoWriter(imgDict, frameList, current, destination):

    frameArray = []
    current = 0
    for i in imgDict["buffer"]:

        imgResult = videoFirstFrameInit(imgDict, frameList, current)

        height, width, layers = (imgResult.shape)
        size = (width, height)

        frameArray.append(imgResult)
        print("# Pre-Computed {} out of {}...".format(current+1, len(imgDict["buffer"])))
        current += 1

    fourcc = cv.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv.VideoWriter(destination, fourcc, 24, size)

    for i in (frameArray):
        out.write((i))
        #out.write(cv.UMat([i]))

    out.release()

    print("# MP4 export done -> {}".format(destination))

def createImgWriter(imgDict, frameList, current, destination):
    '''
    Exporting an image from the buffer with baked in exposure, saturation, and ocio
    '''

    convertedImg = convertForVideo(frameList[current], imgDict["ocio"]["ocioIn"], imgDict["ocio"]["ocioOut"], imgDict["ocio"]["ocioLook"], imgDict["exposure"], imgDict["saturation"], imgDict["channel"], imgDict["RGBA"], imgDict["ocioVar"], imgDict["ocio"]["ocioDisplay"], imgDict["ocioToggle"])
    cv.imwrite(destination, convertedImg, [cv.IMWRITE_JPEG_QUALITY, 100])
    
    print("# JPEG export done -> {}".format(destination))

def videoFirstFrameInit(imgDict, frameList, current):
    convertedImg = convertForVideo(frameList[current], imgDict["ocio"]["ocioIn"], imgDict["ocio"]["ocioOut"], imgDict["ocio"]["ocioLook"], imgDict["exposure"], imgDict["saturation"], imgDict["channel"], imgDict["RGBA"], imgDict["ocioVar"], imgDict["ocio"]["ocioDisplay"], imgDict["ocioToggle"])

    return(convertedImg)

def convertForVideo(path, ocioIn, ocioOut, ocioLook, exposure, saturation, channel, channelRGBA, ocioVar, ocioDisplay, ocioToggle):
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
        img = saturationTweak(img, saturation, ocioVar)

    #ExposureChange
    if (exposure != 0):
        img = img * pow(2,float(exposure))


    if(img.dtype == "float32"):
        # Making the actual OCIO Transform
        if ocioToggle == True:
            ocioTransform2(img, ocioIn, ocioOut, ocioLook, ocioVar, ocioDisplay)
        else:
            ocioTransformDefault(img, ocioIn, ocioOut, ocioLook, ocioVar, ocioDisplay)
        #ocioTransform(img, ocioIn, ocioOut, ocioLook)
        img *= 255
        # Clamping the values to avoid artifacts if values go over 255
        img = clampImg(img)
        # Conversion to the QPixmap format
        img = img.astype(np.uint8)

    #rgb_image = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    #h,w,ch = rgb_image.shape
    #bytes_per_line = ch * w
    #convertedImg = rgb_image.data, w, h, bytes_per_line
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

def layerContactSheetBackend(chanList, imgDict):
    #print(chanList)
    #print(imgDict)

    # Getting casing and size of EXR
    exr = EXR.InputFile(imgDict["path"][0])
    header = exr.header()
    channelsRaw = header["channels"]
    dw = header["dataWindow"]


    # Getting size for the numpy reshape
    isize = (dw.max.y - dw.min.y + 1, dw.max.x - dw.min.x + 1)


    foundChannelList = []
    allChannelList = []
    for i in channelsRaw:
        allChannelList.append(i)
    
    # Check if the channel is lower or uppercased channel.R or channel.r
    casing = ["R","G","B","A"]
    if("{}.r".format(chanList[0]) in list(channelsRaw.keys())):
        casing = ["r","g","b","a"]

    redChannels = []
    blueChannels = []
    greenChannels = []

    #print(casing)
    counter = 0
    for channel in chanList:
        foundChannelList = [allChannelList[counter], allChannelList[counter+1], allChannelList[counter+2]]

        #print("test for channel : {}".format(channel))
        # Reorder channels in case the RGB exist but are not in the right order
        if ("{}.{}".format(channel, casing[0]) in allChannelList) & ("{}.{}".format(channel, casing[1]) in allChannelList) & ("{}.{}".format(channel, casing[2]) in allChannelList ) & (foundChannelList != ["{}.{}".format(channel, casing[0]),"{}.{}".format(channel, casing[1]),"{}.{}".format(channel, casing[2])]):
            #print("reorder chans")
            foundChannelList = ["{}.{}".format(channel, casing[0]),"{}.{}".format(channel, casing[1]),"{}.{}".format(channel, casing[2])]

        #print(foundChannelList)




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

        redChannels.append(channelR)
        greenChannels.append(channelG)
        blueChannels.append(channelB)

        blackChan = np.zeros((isize[1], isize[0], 1), dtype = np.float32)
        blackChan = np.reshape(blackChan, isize)

        blackImg = cv.merge([blackChan, blackChan, blackChan])

        #print("Found channels - {}".format(channel))
        print("Computed channel : {}".format(channel))

        counter += 3


    # Check the number of channels returned after the loop
    #print(len(redChannels))
    #print(len(greenChannels))
    #print(len(blueChannels))

    # Merge the different channel returned as images
    imgList = []
    current = 0
    for image in redChannels:
        currentchannel = cv.merge([blueChannels[current], greenChannels[current], redChannels[current]])
        # Adding text overlay on the image
        cv.putText(currentchannel, chanList[current], (0,25), cv.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv.LINE_AA)
        imgList.append(currentchannel)
        current += 1

    numImgs = (len(imgList))
    #print(numImgs)

    if numImgs > 1:
        #print("num imgs is lower than 2")
        # Defining number of columns
        end = math.floor(numImgs / 2)
        start = 0
        diff = end - start

        # Defining number of row
        iterations = math.ceil(numImgs/end)
        #print(end)
        #print(iterations)
        
        imgLine = []
        for i in range(iterations):
            if (end-1 < numImgs):
                #print("starting with image {} up to {}".format(start, end-1))
                #print("multi image")
                imgLine.append(cv.hconcat(imgList[start:end]))
            else:
                # Need to check if there are more than 1 additionnal pictures to put in last line
                # Need to place black images after the last one in the last line
                #print("single image {}".format(numImgs - 1))
                lastLine = []
                #print("{} : {}".format(start, numImgs - 1))
                current = start
                for i in range( (numImgs-1) - start + 1 ):
                    lastLine.append(imgList[current])
                    current += 1

                for i in range( diff - len(lastLine) ):
                    lastLine.append(blackImg)

                #print(len(lastLine))

                imgLine.append(cv.hconcat(lastLine))

            start = end 

            if ((end+diff) << numImgs):
                end += diff
            else:
                end = numImgs - 1

        #print(len(imgLine))

        #print(imgLine)
        for i in imgLine:
            #img = cv.vconcat([imgLine[0],imgLine[1], imgLine[2]])
            img = cv.vconcat(imgLine)
        # Debuggin showing only last line
        #img = imgLine[len(imgLine)-1]

    # SaturationChange
    if (imgDict["saturation"] != 1):
        img = saturationTweak(img, imgDict["saturation"])

    #ExposureChange
    if (imgDict["exposure"] != 0):
        img = img * pow(2,float(imgDict["exposure"]))



    if(img.dtype == "float32"):
        # Making the actual OCIO Transform
        if imgDict["ocioToggle"] == True:
            ocioTransform2(img, imgDict["ocio"]["ocioIn"], imgDict["ocio"]["ocioOut"], imgDict["ocio"]["ocioLook"], imgDict["ocioVar"], imgDict["ocio"]["ocioDisplay"])
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



        


if __name__ == "__main__":
    main()
