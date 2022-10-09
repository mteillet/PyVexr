# PyVexr is a simple gui app designed to display exr to avoid having to open them in photoshop or other editing softwares
# Using python, pyQt5 and opencv 

#pyVexr_main.py

import cv2 as cv
import numpy as np
import PyOpenColorIO as OCIO
import OpenEXR as EXR
import Imath
import glob

def main():
    print("PyVexr pre alpha version")

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
    #print("PyVexr Loading Button")
    temporaryImg = fileList[0]
    #temporaryImg = "exrExamples/RenderPass_LPE_1.0100.exr"
    #temporaryImg = "exrExamples/RenderPass_UTILS_1.0100.exr"
    #temporaryImg = "exrExamples/RenderPass_Beauty_1.0100.exr"
    #temporaryImg = "~/Documents/Downloads/Jonathan_bertin_09.jpg"
    #channelList = exrListChannels(temporaryImg)
    convertedImg = convertExr(temporaryImg, ocioIn, ocioOut, ocioLook, exposure, saturation, channel, channelRGBA, ocioVar, ocioDisplay, ocioToggle)
    return (convertedImg)

def updateImg(path, channel, ocioIn, ocioOut, ocioLook, exposure, saturation, channelRGBA, ocioVar, ocioDisplay, ocioToggle):
    #Checking if a channel switch will be needed or not

    channel = checkFirstExrChannel(path, channel, channelRGBA)

    if (channel in [None, "RGB", "RGBA"]) & (channelRGBA == "rgba"):
        #print("No channel merge needed")
        img = cv.imread(path[0], cv.IMREAD_ANYCOLOR | cv.IMREAD_ANYDEPTH)
        #print("classic layer")
    else:
        splitImg = exrSwitchChannel(path, channel, channelRGBA)
        # Merging the splitted exr channel (in a different order a openCV expects BGR by default)
        img = cv.merge([splitImg[2], splitImg[1], splitImg[0]])
        #print("splittedLayer")

    # SaturationChange
    if (saturation != 1):
        img = saturationTweak(img, saturation)

    # ExposureChange
    if (exposure != 0):
        img = img * pow(2,float(exposure))

    if(img.dtype == "float32"):
        # Making the actual OCIO Transform
        if ocioToggle == True:
            ocioTransform2(img, ocioIn, ocioOut, ocioLook, ocioVar, ocioDisplay)
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

def rgbToHsv(rgb):
    maxv = np.amax(rgb, axis=2)
    maxc = np.argmax(rgb, axis=2)
    minv = np.amin(rgb, axis=2)
    minc = np.argmin(rgb, axis=2)

    hsv = np.zeros(rgb.shape, dtype='float32')

    hsv[maxc == minc, 0] = np.zeros(hsv[maxc == minc, 0].shape)
    hsv[maxc == 0, 0] = (((rgb[..., 1] - rgb[..., 2]) * 60.0 / (maxv - minv + np.spacing(1))) % 360.0)[maxc == 0]
    hsv[maxc == 1, 0] = (((rgb[..., 2] - rgb[..., 0]) * 60.0 / (maxv - minv + np.spacing(1))) + 120.0)[maxc == 1]
    hsv[maxc == 2, 0] = (((rgb[..., 0] - rgb[..., 1]) * 60.0 / (maxv - minv + np.spacing(1))) + 240.0)[maxc == 2]
    hsv[maxv == 0, 1] = np.zeros(hsv[maxv == 0, 1].shape)
    hsv[maxv != 0, 1] = (1 - minv / (maxv + np.spacing(1)))[maxv != 0]
    hsv[..., 2] = maxv

    return(hsv)

def hsvToRgb(hsv):
    hi = np.floor(hsv[..., 0] / 60.0) % 6
    hi = hi.astype('uint8')
    v = hsv[..., 2].astype('float32')
    f = (hsv[..., 0] / 60.0) - np.floor(hsv[..., 0] / 60.0)
    p = v * (1.0 - hsv[..., 1])
    q = v * (1.0 - (f * hsv[..., 1]))
    t = v * (1.0 - ((1.0 - f) * hsv[..., 1]))

    rgb = np.zeros(hsv.shape)
    rgb[hi == 0, :] = np.dstack((v, t, p))[hi == 0, :]
    rgb[hi == 1, :] = np.dstack((q, v, p))[hi == 1, :]
    rgb[hi == 2, :] = np.dstack((p, v, t))[hi == 2, :]
    rgb[hi == 3, :] = np.dstack((p, q, v))[hi == 3, :]
    rgb[hi == 4, :] = np.dstack((t, p, v))[hi == 4, :]
    rgb[hi == 5, :] = np.dstack((v, p, q))[hi == 5, :]

    return(rgb)

def saturationKernel(img, saturation, coefRGB):
    imgB, imgG, imgR = cv.split(img)
    luma = imgR * coefRGB[0] + imgG * coefRGB[1] + imgB * coefRGB[2]
    luma3d = np.repeat(luma[:,:, np.newaxis], 3, axis = 2)
    saturated = np.clip(((img - luma3d) * saturation + luma3d), 0, 255)
    

    return(saturated)


def saturationTweak(img, saturation):
    if saturation != 1:
        # Settings for the luma calculations
        coefRGB = [0.2126, 0.7152, 0.0722]
        rgb = saturationKernel(img,saturation, coefRGB)
    else:
        rgb = img

    return(rgb)

def exrListChannels(path):
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
    """
    def responsible for returning the R,G,B components of the image, in case 
    a different channel of pass is selected
    """
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


def initOCIO():
    print("Init OCIO version 2")
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

def checkFirstExrChannel(path, channel, channelRGBA):
    """
    Checks if the channel RGB exists in the exr, otherwise returns the first channel
    """
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
    path = [path]

    channel = checkFirstExrChannel(path, channel, channelRGBA)

    if (channel in [None, "RGB", "RGBA"]) & (channelRGBA == "rgba"):
        #print("No channel merge needed")
        img = cv.imread(path[0], cv.IMREAD_ANYCOLOR | cv.IMREAD_ANYDEPTH)
        #print("classic layer")
    else:
        splitImg = exrSwitchChannel(path, channel, channelRGBA)
        # Merging the splitted exr channel (in a different order a openCV expects BGR by default)
        img = cv.merge([splitImg[2], splitImg[1], splitImg[0]])
        #print("splittedLayer")

    #img = cv.merge(path)
    #img = cv.imread(path, cv.IMREAD_ANYCOLOR | cv.IMREAD_ANYDEPTH)
    
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

def ocioTransform(img, ocioIn, ocioOut, ocioLook):
    #print("Using PyOpenColorIO version 2")
    #print("Attempting convesion from {0} to {1} using look {2}".format(ocioIn, ocioOut, ocioLook))

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
            looks.insert(0, "None")
            looks.pop(looks.index("Punchy"))
            looks.insert(1, "Punchy")

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
