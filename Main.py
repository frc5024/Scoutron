from __future__ import print_function

print("Starting up program...\n")

from glob import glob
import matplotlib.pyplot as plt
from skimage import *
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import math

'''''''''''''''''''''''''''''''''''''''''''''
'            GLOBAL    VARIABLES            '
'''''''''''''''''''''''''''''''''''''''''''''

# What type of authorization do we want? We want the scope of the spreadsheet we're using
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID of the spreadsheet
SPREADSHEET_ID = '1FLMm3aBwR1MjXJPwC50OiIlZYRXPjGwciewMAKkfxY8'


'''''''''''''''''''''''''''''''''''''''''''''
'            IMAGE    PROCESSING            '
'''''''''''''''''''''''''''''''''''''''''''''

# Code Snippet from Google themselves, thankyou Google
def GetSheetsAPI():
    creds = None
    try:
        # 'token.pickle' is our credentials, load it if it exists
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        # Get the service?
        service = build('sheets', 'v4', credentials=creds)
        # Get the sheets?
        sheet = service.spreadsheets()
        return sheet
    except:
        return None

def ReadRange(Sheet, Range):
    global SPREADSHEET_ID
    Result = Sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=Range).execute()
    return Result.get('values')

def WriteRange(Sheet, Range, Data):
    global SPREADSHEET_ID
    Body = {'values':Data}
    Result = Sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=Range,
        valueInputOption='RAW', body=Body).execute()

def GrabImageDimensions(Image):
    W = len(Image[0])
    H = len(Image)
    print("Image  Width: %i" % W )
    print("Image Height: %i" % H )
    print()
    return (W, H)

def ContoursToRects(Contours):
    Rectangles = []
    for Contour in Contours:
        MostLeft  = 9999
        MostRight = 0
        MostUp    = 9999
        MostDown  = 0        
        for Point in Contour:
            MostLeft  = min(MostLeft,  Point[1]) # \
            MostRight = max(MostRight, Point[1]) #  \ Idk why, but the X & Y values are flipped...
            MostUp    = min(MostUp,    Point[0]) #  / So we counter flip it once here and never again
            MostDown  = max(MostDown,  Point[0]) # /
        Rect = [MostLeft, MostUp, MostRight-MostLeft, MostDown-MostUp]
        Rectangles.append(Rect)
    # Log it
    print("Grabbed all rectangles...")
    for Rect in Rectangles :
        print(Rect)
    print()
    return Rectangles

def GrabTopRowRects(Rectangles, YLine):
    TopRowRects = []
    NumOfRectsToPop = 0
    # All top row rects should be first in the array
    # So go through the rects until one rect isnt in top row ( < YLine)
    for i, Rect in enumerate(Rectangles):
        if Rect[1] < YLine: TopRowRects.append(Rect)
        else:               break
    # Now we sort through the top row rects from min->max x coord
    # We can pop the corner rect later, it'll be easier that way
    Temp = [0, 0, 0, 0]
    for i in range(len(TopRowRects)):
        SmallestRectIndex = i
        for j in range(i, len(TopRowRects)):
            if TopRowRects[j] < TopRowRects[SmallestRectIndex]:
                SmallestRectIndex = j
        Temp = TopRowRects[i]
        TopRowRects[i] = TopRowRects[SmallestRectIndex]
        TopRowRects[SmallestRectIndex] = Temp
    # Pop the useless corner rects
    TopRowRects.pop(0)
    TopRowRects.pop(-1)
    # Log it
    print("Grabbed all Top Row Rectangles...")
    for Rect in TopRowRects:
        print(Rect)
    print()
    return TopRowRects

def GrabLeftColRects(Rectangles, XLine):
    # Sadly we don't know which rects are our allignement rects
    # So we go through every rect and add it if it's < XLine
    LeftColRects = []
    for i, Rect in enumerate(Rectangles):
        if Rect[0] < XLine:
            LeftColRects.append(Rect)
    # Although it's not sorted x-wise, being sorted y-wise means it's already sorted
    # Pop the useless corner rect
    LeftColRects.pop(0)
    # Log it
    print("Grabbed all Left Collumn Rectangles...")
    for Rect in LeftColRects:
        print(Rect)
    print()
    return LeftColRects

def GrabCornerRect(Rectangles, YLine, ImageWidth):
    # The corner rect is square unlike the allignment rects
    # It's width should be > then half the height
    Length_2 = Rectangles[0][3] / 2
    for Rect in Rectangles:
        if  Rect[2] > Length_2 \
        and Rect[0] < ImageWidth * 0.3:
            print("Corner Rect pulled...")
            print("Rect: "+str(Rect)+"\n")
            return Rect
    return -1

def GrabTopRightRect(Rectangles, YLine, ImageWidth):
    # The corner rect is square unlike the allignment rects
    # It's width should be > then half the height
    Length_2 = Rectangles[0][3] / 2
    for Rect in Rectangles:
        if  Rect[2] > Length_2 \
        and Rect[0] > ImageWidth * 0.7:
            print("Top Right Rect pulled...")
            print("Rect: "+str(Rect)+"\n")
            return Rect
    return -1

def GetAngleFromTwoRects(R1, R2):
    X1 = R1[0] + R1[2] / 2
    Y1 = R1[1] + R1[3] / 2
    X2 = R2[0] + R2[2] / 2
    Y2 = R2[1] + R2[3] / 2

    DeltaX = X2 - X1
    DeltaY = Y2 - Y1
    
    AngleRadians = math.atan2(DeltaY, DeltaX)

    return  AngleRadians * 180.0 / math.pi

def GrabAllignmentCoordsX(TopRowRects):
    XColCoords = []
    for Rect in TopRowRects:
        XColCoords.append(Rect[0] + Rect[2] / 2)
    print("X Collumn Coords: %s\n" % XColCoords)
    return XColCoords

def GrabAllignmentCoordsY(LeftColRects):
    YRowCoords = []
    for Rect in LeftColRects:
        YRowCoords.append(Rect[1] + Rect[3] / 2)
    print("Y Row     Coords: %s\n" % YRowCoords)
    return YRowCoords

def GrabBubbleRectsFromRects(Rectangles, XLine, YLine):
    BubbleRects = []
    for Rect in Rectangles:
        if Rect[0] > XLine:
            if Rect[1] > YLine:
                BubbleRects.append(Rect)
    print("Grabbed all the bubble rectangles...")
    for B in BubbleRects:
        print(B)
    print()
    return BubbleRects

def IsPointInRects(Point, Rects):
    for Rect in Rects:
        XDelta = Point[0] - Rect[0]
        YDelta = Point[1] - Rect[1]
        if XDelta < 0       \
        or YDelta < 0       \
        or XDelta > Rect[2] \
        or YDelta > Rect[3] :
            continue
        else: return True
    return False

def GetBubbles(XColCoords, YRowCoords, BubbleRects):
    Bubbles = []
    for Row in YRowCoords:
        BubbleRow = []
        for Col in XColCoords:
            Point = [Col, Row]
            IsFilled = IsPointInRects(Point, BubbleRects)
            BubbleRow.append(IsFilled)
        Bubbles.append(BubbleRow)

    # Log it
    print("Grabbed all bubble values...")
    for BubbleRow in Bubbles:
        print(BubbleRow)
    print()
    
    return Bubbles


'''''''''''''''''''''''''''''''''''''''''''''
'            IMAGE    DISPLAYING            '
'''''''''''''''''''''''''''''''''''''''''''''

def DisplayImage(plt, Image, Title):
    plt.imshow(Image)
    plt.set_title(Title)
    plt.axis('off')
    return

def DrawContours(plt, Contours):
    for Contour in Contours:
        plt.plot(Contour[:,1], Contour[:,0])

def DrawRectangles(plt, Rectangles):
    for Rect in Rectangles:
        X = [0, 0, 0, 0, 0]
        Y = [0, 0, 0, 0, 0]
        X[0] = Rect[0]
        X[1] = Rect[0]
        X[2] = Rect[0]+Rect[2]
        X[3] = Rect[0]+Rect[2]
        X[4] = Rect[0]
        Y[0] = Rect[1]
        Y[1] = Rect[1]+Rect[3]
        Y[2] = Rect[1]+Rect[3]
        Y[3] = Rect[1]
        Y[4] = Rect[1]
        plt.plot(X, Y)

def DrawXRectangles(plt, Rectangles):
    for Rect in Rectangles:
        X  = [Rect[0], Rect[0]+Rect[2]]
        Y1 = [Rect[1], Rect[1]+Rect[3]]
        Y2 = [Y1[1], Y1[0]]
        plt.plot(X, Y1)
        plt.plot(X, Y2)

def DrawVerticalLines(plt, Coords, y2):
    for x in Coords:
        plt.plot([x, x], [0, y2])

def DrawHorizontalLines(plt, Coords, x2):
    for y in Coords:
        plt.plot([0, x2], [y, y])

    
''''''''''''''''''''''''''''''''''''''''
'            MAIN    THREAD            '
'''''''''''''''''''''''''''''''''''''''

def main():

    print("Running program...\n")

    # Grap all JPGs in the Images folder
    Images = glob("Images/*.jpg")

    # Grab all PNGs in the Images folder, just in case
    Images += glob("Images/*.png")

    print("Found all jpg/png images in Images directory")
    for Image in Images:
        print(Image)
    print()

    # Declare all our window cols/rows
    fig, axes = plt.subplots(nrows=1, ncols=len(Images))
    ax = axes.ravel()
    
    BubbleSets = []

    for i, ImageName in enumerate(Images):
        
        # Read the image file as grayscale
        RawImage = io.imread(ImageName, True)

        # Make a rect for the entire image, for general awareness
        ImageWidth, ImageHeight = GrabImageDimensions(RawImage)

        # Gaussian blur the image, this greys out the text, circles, and lines
        BlurImage = filters.gaussian(RawImage, sigma=1.5)

        # Apply threshold to turn image from greyscale to black|white, this will full rid the text & circles
        ThreshImage = BlurImage < 0.3
        
        # Finds contours... Will turn our image into a list of shapes basically
        Contours = measure.find_contours(ThreshImage, 0.8)

        # Turns all the random shapes(contours) into simple rects
        Rectangles = ContoursToRects(Contours)
        
        # First rect might be the entire page, if so, pop it
        if Rectangles[0][2] > ImageWidth / 2 :
            print("Popped page rect...\n="+str(Rectangles[0])+"\n")
            Rectangles.pop(0)
        # To be safe, we won't do any more popping, as we will be saving indexes and stuff

        # Since rects are in top-down order, lets make a line to seperate our allignment rects
        YLine = Rectangles[0][1] + Rectangles[0][3]
        print("YLine: %i\n" % YLine)

        # First, we need the two corner rects to check our rotation
        # We also need the top-left corner rect for the X-Line
        CornerRect = GrabCornerRect(Rectangles, YLine, ImageWidth)
        TopRightRect = GrabTopRightRect(Rectangles, YLine, ImageWidth)

        # Get an angle of... if the page is tilted
        # But we might not have a top-right rect to allign with
        Angle = 0.0
        if TopRightRect is not -1 :
            Angle = GetAngleFromTwoRects(CornerRect, TopRightRect)

        print("Angle tilt of page calculated:", Angle, '\n')

        # Only rotate the image if the angle we're tilted is actualy significant
        if math.fabs(Angle) > 1.0 :

            print("Rotating the image.\n")
            
            # Rotate our image
            BlurImage = transform.rotate(BlurImage, -Angle, True)

            # Re do everything we did above
            ThreshImage = BlurImage < 0.3
            Contours = measure.find_contours(ThreshImage, 0.8)
            Rectangles = ContoursToRects(Contours)
            if Rectangles[0][2] > ImageWidth / 2 :
                print("Popped page rect...\n="+str(Rectangles[0])+"\n")
                Rectangles.pop(0)
            YLine = Rectangles[0][1] + Rectangles[0][3]
            print("YLine: %i\n" % YLine)
            CornerRect = GrabCornerRect(Rectangles, YLine, ImageWidth)

        # All the rects above our YLine are our allignment rects
        TopRowRects = GrabTopRowRects(Rectangles, YLine)
        
        CornerRect = GrabCornerRect(Rectangles, YLine, ImageWidth)

        # Same as YLine but x-wise, we use the CornerRect we grabbed to calculate this
        XLine = CornerRect[0] + CornerRect[2] / 2
        print("XLine: %i\n" % XLine)

        # All the rects to the left of the XLine are also our allignment rects
        LeftColRects = GrabLeftColRects(Rectangles, XLine)
     
        # Grab all the X&y-axis coordinates to allign with bubbles
        XColCoords = GrabAllignmentCoordsX(TopRowRects)
        YRowCoords = GrabAllignmentCoordsY(LeftColRects)
        
        # All the rects that are past the X&Y lines are our bubbles
        BubbleRects = GrabBubbleRectsFromRects(Rectangles, XLine, YLine)

        # Where magic happens. Check each intersection to see if there's a filled bubble there
        Bubbles = GetBubbles(XColCoords, YRowCoords, BubbleRects)

        # Display our results!
        DisplayImage       (ax[i], ThreshImage, ImageName)
        DrawHorizontalLines(ax[i], YRowCoords, ImageWidth)
        DrawVerticalLines  (ax[i], XColCoords, ImageHeight)
        DrawRectangles     (ax[i], TopRowRects)
        DrawRectangles     (ax[i], LeftColRects)
        DrawXRectangles    (ax[i], BubbleRects)

        # Append it
        BubbleSets.append(Bubbles)

    # -= End for Image in Images =-

    
    # !!! Bubbles are accessed [y][x], not [x][y] !!!

    ###################################
    # ...Convert Bubbles into Data... #
    ###################################

    Data = [
        ["Beenis", "lol", "xd"],
        ["Benis2", "big oof", "rip in chat"]
    ]

    print("Data collected...")
    for Row in Data:
        print(Row)
    print()

    # Get authorization and store an object to access the spreadsheet
    Sheet = GetSheetsAPI()

    # If we're offline (or something else fails)
    if Sheet is None:
        
        print("!!! Unable to reach the Google Spreadsheet. Outputing the data into a text file instead !!!\n")
        
        file = open("DataOutput.txt", 'a')
        
        for Row in Data:
            file.write(str(Row[0]))
            for i, Val in  enumerate(Row, 1) :
                file.write("\t"+str(Val))
            file.write("\n")
        file.close()

        print("Successfully appended extracted data to DataOutput.txt\n")
        
    else:
        
        Vals = ReadRange(Sheet, "Sheet1!A1:C4")

        print("Values pulled from Spreadsheet")
        for Row in Vals:
            print(Row)
        print()

        WriteRange(Sheet, "Sheet1!A6:D8", Data)
        print("Updated the Spreadsheet with Data\n")
    
    '''    IMAGE DISPLAYING    '''
   
    # Show it!
    plt.tight_layout(0.0)
    plt.show()

    input("Press Enter to Exit...")

    return
    
if __name__ == "__main__" : main()
