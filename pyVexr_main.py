# PyVexr is a simple gui app designed to display exr to avoid having to open them in photoshop or other editing softwares
# Using python, pyQt5, opencv and some C++

#pyVexr_main.py

import cv2 as cv
import numpy as np

def main():
    print("PyVexr")

def loadImg():
    print("PyVexr Loading Button")
    temporaryImg = "exrExamples/CamShape_holdoutMatte.0000.exr"
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
    if(img.dtype != "uint8"):
        img = cv.normalize(img, None, 0, 255, cv.NORM_MINMAX, cv.CV_8U)
    print(img.dtype)

    # Conversion to the QPixmap format
    rgb_image = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    h,w,ch = rgb_image.shape
    bytes_per_line = ch * w
    convertedImg = rgb_image.data, w, h, bytes_per_line
    return(convertedImg)


if __name__ == "__main__":
    main()
