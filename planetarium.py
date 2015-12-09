from __future__ import division

"""
Emily Newman's TP F15

Using Pygame and PyEphem libraries
Uses the Yale Bright Star Catalog, as well as PyEphem's star catalog

YBS available at http://mirrors.dotsrc.org/exherbo/YBS.edb

Used http://mathworld.wolfram.com/Point-LineDistance2-Dimensional.html 
for distance of a point from a line
"""
import pygame
from framework import Framework 
import ephem
import ephem.stars
import ephem.cities
import datetime, time
import math
import copy
import os

"""
TODO MASTER LIST:
cities - done
constellations??
interface / main screen nav (dragging mouse to move) - done
undo/redo/delete bugs - mostly done?
general interface - ???
make info more visible - in progress
splash screen

"""



# read/writeFile from the class notes on Basic File I/O
# http://www.cs.cmu.edu/~112/notes/notes-strings.html#basicFileIO
def readFile(filename, mode="rt"):       # rt = "read text"
    with open(filename, mode) as fin:
        return fin.read()

def writeFile(filename, contents, mode="wt"):    # wt = "write text"
    with open(filename, mode) as fout:
        fout.write(contents)


def pointInBox(point, boxCoords): #from my hw8a.py
    (x, y) = point
    (boxLeft, boxTop, boxRight, boxBot) = boxCoords
    return boxLeft<=x<=boxRight and boxTop<=y<=boxBot 

def pointInCircle(point, circlePos, r):
    (x, y) = point
    (cx, cy) = circlePos
    return (x-cx)**2 + (y-cy)**2 <= r**2


class Star(object):
    def __init__(self, name, body):
        self.name = name
        self.body = body #type == ephem.Body
        self.screenPos = None
        self.showInfo = False
        self.r = 1

    def changeInfo(self):
        self.showInfo = not self.showInfo

    def calculate(self, ref, shift): #ref = city, shift = Planetarium.shift
        self.body.compute(ref)
        self.r = int(self.body.mag)
        if self.body.alt < 0: #below horizon
            return #do nothing, screenPos remains None
        phi = self.body.alt + math.pi/2
        theta = 2*math.pi - self.body.az
        #convert from spherical to cartesian xy coordinates
        #constant sphere radius
        x = math.sin(phi)*math.cos(theta)
        y = math.sin(phi)*math.sin(theta)
        #convert to draw-able coordinates
        #stores them based on "big" screen, not "current" screen
        self.screenPos = (shift * (x + 1), shift * (-y + 1))

    def displayPos(self, left, up):
        if self.screenPos == None: return None
        (x,y) = self.screenPos
        return (int(x - left), int(y - up))


class Line(object):
    def __init__(self, startStar, screenPos, endStar=None):
        self.screenPos = screenPos
        (left, up) = screenPos
        self.star1 = startStar
        (self.dispX1, self.dispY1) = self.star1.displayPos(left, up)
        (self.x1, self.y1) = self.star1.screenPos
        self.star2 = endStar
        (self.x2, self.y2) = self.star1.screenPos
        (self.dispX2, self.dispY2) = (self.dispX1, self.dispY1)
        self.color = (255, 255, 255) #white
        self.width = 2

    def __repr__(self):
        return self.star1.name+"|"+self.star2.name

    def onClick(self, x, y):
        #point distance from a line equation
        (x1, y1, x2, y2) = (self.dispX1, self.dispY1, self.dispX2, self.dispY2)
        d = abs((x2-x1)*(y1-y) - (x1-x)*(y2-y1))
        denom = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if denom != 0: d /= denom
       # print "successful click"
        return d <= 3*self.width

    def setEnd(self, star, ref):
        (left, up) = ref
        self.star2 = star
        (self.x2, self.y2) = self.star2.screenPos
        (self.dispX2, self.dispY2) = self.star2.displayPos(left, up)

    def updateEndPoint(self, x, y):
        #only used temporarily for aesthetic purposes
        self.dispX2 = x
        self.dispY2 = y

    def displayPoints(self, ref):
        (left, up) = ref
        if self.star2 == None:
            return (self.star1.displayPos(left,up), (self.dispX2, self.dispY2))
        else:
            return (self.star1.displayPos(left, up), 
                    self.star2.displayPos(left, up))

    def draw(self, screen, ref):
        (start, end) = self.displayPoints(ref)
        pygame.draw.line(screen, self.color, start, end, self.width)


class Button(object):
    def __init__(self, name, x, y, color, width=25, height=15):
    # x and y are upper left corner
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.BLACK = (0, 0, 0)
        self.color = color

    def onClick(self, x, y):
        return pointInBox((x,y), (self.x, self.y, 
                                self.x+self.width, self.y+self.height))
        

    def draw(self, screen, font):
        #todo use images instead of pygame drawing?
        pygame.draw.rect(screen, self.BLACK, pygame.Rect(self.x, self.y, 
                                            self.width, self.height), 1)
        screen.fill(self.color, pygame.Rect(self.x, self.y, 
                                            self.width, self.height))


class ZoomButton(Button):
    def __init__(self, name, x, y, color, width=25, height=15):
        super(ZoomButton, self).__init__(name, x, y, color, width, height)
        self.dir = 0
        self.char = ""
        if self.name == "zoomIn":
            self.dir=1
            self.char="+"
        elif self.name=="zoomOut":
            self.dir=-1
            self.char="-"
        self.zoom=30

    def onClick(self, x, y):
        if pointInBox((x,y), (self.x, self.y, self.x+self.width, 
                                            self.y+self.height)):
            return self.dir*self.zoom
        else:
            return 0 #no change to shift

    def draw(self, screen, font):
        super(ZoomButton, self).draw(screen, font)
        text=font.render(self.char, 1, self.BLACK)
        screen.blit(text, (self.x, self.y))


class ModeButton(Button):
    def __init__(self, name, x, y, color, width=25, height=15):
        super(ModeButton, self).__init__(name, x, y, color, width, height)

             
    def draw(self, screen, font): 
        word = self.name[0].upper() + self.name[1:]
        (self.width, self.height) = font.size(word)  
        super(ModeButton, self).draw(screen, font)
        (self.width, self.height) = font.size(word)
        text = font.render(word, 1, self.BLACK)
        screen.blit(text, (self.x, self.y))

    def onClick(self, x, y):
        if pointInBox((x,y), (self.x, self.y, self.x+self.width, 
                                            self.y+self.height)):
            return self.name
        return None


class TimeButton(Button):
    def __init__(self, name, x, y, color, width=25, height=15):
        super(TimeButton, self).__init__(name, x, y, color, width, height)
        #set max time val
        self.minTime = 0
        if self.name == "year":
            self.minTime = 100
            self.maxTime = 3000
            self.width += 5
        elif self.name == "month":
            self.minTime = 1
            self.maxTime = 12
        elif self.name == "day":
            self.minTime = 1
            self.maxTime = 31 #to be controlled in Planetarium
        elif self.name == "hour":
            self.maxTime = 23
        else: #minute
            self.maxTime = 59
        self.timeVal = 0
        self.YELLOW = (255, 255, 0)

    def up(self):
        if self.minTime <= self.timeVal+1 <= self.maxTime:
            self.timeVal += 1

    def down(self):
        if self.minTime <= self.timeVal-1 <= self.maxTime:
            self.timeVal -= 1

    def getTime(self):
        return self.timeVal

    def setTimeVal(self, val):
        self.timeVal = val

    def onClick(self, x, y):
        if pointInBox((x,y), (self.x, self.y, self.x+self.width, 
                                            self.y+self.height)):
            return self
    def draw(self, screen, font):
        super(TimeButton, self).draw(screen, font)
        text = font.render(str(self.timeVal), 1, self.BLACK)
        screen.blit(text, (self.x, self.y))


class NowButton(Button):
    def draw(self, screen, font):
        word = self.name[0].upper() + self.name[1:]
        super(NowButton, self).draw(screen, font)
        text = font.render(word, 1, self.BLACK)
        screen.blit(text, (self.x, self.y))

    def onClick(self, x, y):
        if pointInBox((x,y), (self.x, self.y, self.x+self.width, 
                                            self.y+self.height)):
            return datetime.datetime.now()


class ToggleButton(Button):
    def __init__(self, name, x, y, color, width=25, height=15):
        super(ToggleButton, self).__init__(name, x, y, color, width, height)
        self.toggle = False
        self.offColor = color #red
        self.onColor = (0, 204, 0) #green

    def onClick(self, x, y):
        if pointInBox((x,y), (self.x, self.y, self.x+self.width, 
                                            self.y+self.height)):
            self.toggle = not self.toggle
            return self.toggle
    def draw(self, screen, font):
        if self.toggle:
            word = "ON"
            self.color = self.onColor
        else:
            word = "OFF"
            self.color = self.offColor
        super(ToggleButton, self).draw(screen, font)
        text = font.render(word, 1, self.BLACK)
        screen.blit(text, (self.x, self.y))


class ListButton(Button):
    def __init__(self,  name, x, y, color, data, width=25, height=15):
        super(ListButton, self).__init__(name, x, y, color, width, height)
        self.data = data #stores strings
        self.selectedWord = self.data[0]
        self.index = 0



    def selectItem(self, item):
        self.selectedWord = item
        index = self.data.find(item)

    def down(self):
        self.index = (self.index+1)%len(self.data)
        self.selectedWord = self.data[self.index]
        return self.data[self.index]


    def up(self):
        if self.index - 1 < 0:
            self.index = len(self.data) - (self.index + 1)
        else:
            self.index -= 1
        self.selectedWord = self.data[self.index]
        return self.data[self.index]
            

    def getItem(self):
        return self.data[self.index]

    def onClick(self, x, y):
        if pointInBox((x,y), (self.x, self.y, self.x+self.width, 
                                            self.y+self.height)):
            return self

    def draw(self, screen, font):
        (self.width, self.height) = font.size("OOOOOOOOOOOOOO")
        super(ListButton, self).draw(screen, font)
        text = font.render(self.selectedWord, 1, self.BLACK)
        screen.blit(text, (self.x, self.y))


class DrawButton(Button):
    def __init__(self, name, x, y, color, width=25, height=15):
        super(DrawButton, self).__init__(name, x, y, color, width, height)
        self.icon = pygame.image.load(os.path.join('icons', name+'.png'))

    def drawSelected(self, screen):
        pygame.draw.rect(screen, self.color, 
                        pygame.Rect(self.x, self.y, self.width, self.height))

    def draw(self, screen, font):
        screen.blit(self.icon, (self.x, self.y))

    def onClick(self, x, y):
        if pointInBox((x,y), (self.x, self.y, self.x+self.width, 
                                            self.y+self.height)):
           # print "clicked line"
            return self


class Planetarium(Framework):
    def __init__(self, width=600, height=400, fps=50, title="PyPlanetarium"):
        super(Planetarium, self).__init__(width, height, fps, title)
        self.title = "PyPlanetarium"
        self.bgColor = self.BLACK
        self.shift = 1400 #changes with zooming
        #full screen width and height is self.shift*2 at any time
        self.margin = 10
        self.minZoom = 10
        self.maxZoom = 10000
        self.shiftChange = 10

        (self.MIN_ALT, self.MAX_ALT) = (0, math.pi/2)
        (self.MIN_AZ, self.MAX_AZ) = (0, 2*math.pi) #radians
        # upper left corner of screen in terms of sky
        # starts w/ center of screen being (0,0) of sky
        self.screenPos = (self.shift-self.width//2, self.shift-self.height//2)
        self.date = datetime.datetime.now() #always Datetime form
        self.starList = [ ]
        self.cities = [city for city in ephem.cities._city_data]
        self.cities.sort()
        self.initPittsburgh()
        self.city = self.pgh
        self.cityName = "Pittsburgh"
        self.initStars()
        #read in more stars!
        yaleCatalog = self.readInDB("ybs.edb")
        self.starList += yaleCatalog #using Yale's Bright Star catalog
        self.LIGHT_BLUE = (114, 164, 255) 
        self.RED = (208, 9, 9)
        self.GREEN2 = (0, 204, 0)
        self.PINK = (255, 102, 255)
        self.YELLOW = (255, 255, 0)

        self.initButtons()
        self.initOptionsMode()

        self.inRealTime = False
        self.mode = "main"
        #draw mode initializing
        self.initDrawMode()
        self.updateOptionButtons()

        self.justClicked = False
        (self.mouseStartX, self.mouseStartY) = (None, None)



################################# INIT FUNCTIONS ##############################

        

    def initButtons(self):
        self.buttons = [ 
        ZoomButton("zoomIn", 0, 0, self.LIGHT_BLUE),
        ZoomButton("zoomOut", 25, 0, self.LIGHT_BLUE),
        ModeButton("draw", self.width-self.font.size("draw")[0], 0, 
                                        self.LIGHT_BLUE),
        ModeButton("options",self.width-self.font.size("draw")[0] 
                -self.font.size("options")[0]-10, 0, self.LIGHT_BLUE)
                ]

    def initOptionsMode(self):
        #splitting the screen into 9ths width wise, 8ths height wise
        self.optionsButtons = [ 
        TimeButton("year", self.width*3//9, self.height*3//8, self.WHITE),
        TimeButton("month", self.width*4//9, self.height*3//8, self.WHITE),
        TimeButton("day", self.width*5//9, self.height*3//8, self.WHITE),
        TimeButton("hour", self.width*6//9, self.height*3//8, self.WHITE),
        TimeButton("minute", self.width*7//9, self.height*3//8, self.WHITE),
        NowButton("now", self.width*8//9, self.height*3//8, self.PINK),
        ListButton("city", self.width//2-self.font.size("OOOOOOOOOOOOOO")[0]//2,
                                self.height*4//8, self.LIGHT_BLUE, self.cities),
        ToggleButton("realtime", self.width//2-self.font.size("OFF")[0]//2, 
                                self.height*5//8, self.RED),
        ModeButton("return", self.width//2-self.font.size("Return")[0]//2, 
                                self.height*6//8, self.GREEN2),
        ModeButton("quit", self.width//2-self.font.size("Quit")[0]//2,
                                self.height*7//8, self.RED )
        ]
        self.selectedButton = None


    def initDrawMode(self):
        size = 50
        self.drawModeButtons = [ 
                                DrawButton("erase", 0, self.height//8, 
                                                    self.YELLOW, size, size),
                                DrawButton("undo", 0, self.height*2//8,
                                                    self.YELLOW, size, size),
                                DrawButton("redo", 0, self.height*3//8, 
                                                    self.YELLOW, size, size),
                                DrawButton("clear", 0, self.height*4//8, 
                                                    self.YELLOW, size, size),
                                DrawButton("save", 0, self.height*5//8, 
                                                    self.YELLOW, size, size),
                                DrawButton("loadfile", 0, self.height*6//8, 
                                                    self.YELLOW, size, size),
                                DrawButton("savefile", 0, self.height*7//8, 
                                                    self.YELLOW, size, size)
                                ]
        self.onLine = False
        self.lines = [ ]
        self.undidLines = [ ]
        self.undidActions = [ ] 
        self.erasedLines = [ ] 
        self.lastAction = "draw"
        self.selectedDrawButton = None
        self.drawMode = "draw"
        self.actions = [ ]
        self.iconSize = 50

    def initStars(self): #FLAG
        for star in ephem.stars.db.split("\n"):
            starName = star.split(",")[0]
            if starName == "": continue #not a star
            self.starList.append(Star(starName, ephem.star(starName)))


    def initPittsburgh(self):
        self.pgh = ephem.Observer()
        self.pgh.lat = "40:26:26.3"
        self.pgh.long = "-79:59:45.20" 
        self.pgh.date = ephem.Date(self.date)
        self.cities.insert(0, "Pittsburgh")

    def readInDB(self, path):
        #returns list of Star objects from all stars in DB
        db = readFile(path)
        starList = [ ] 
        for line in db.splitlines():
            if line.startswith("#") or line == "": continue
            line = line.strip()
            body = ephem.readdb(line)
            starList.append(Star(body.name, body))
        return starList



################################## STAR FUNCTIONS #############################


    def calculateStars(self):
        for star in self.starList:
            star.calculate(self.city, self.shift)


    def updateScreenPos(self, shiftChange, x=0, y=0):
        (oldX, oldY) = self.screenPos
        # print "old " + str(self.screenPos)
        if shiftChange == 0:
            self.screenPos = (x+oldX, y+oldY)
        else:
            oldShift = self.shift
            self.shift += shiftChange
            self.screenPos=(oldX*self.shift/oldShift, oldY*self.shift/oldShift)
        # print "new " + str(self.screenPos)




########################### MOUSE PRESSED FUNCTIONS ###########################

    def mousePressed(self, x, y):
        #Options screen:
        if self.mode == "options":
            self.optionsMousePressed(x, y)

        #In main screen:
        #check all buttons
        elif self.mode == "draw":
            check = self.checkDrawButtons(x, y)
            if check == 1: return 
            #check the nav buttons
            self.checkNavButtons(x, y)
            self.checkStarsDrawMode(x, y)
            self.checkLines(x, y)

        elif self.mode == "main":
            #check all buttons
            self.checkNavButtons(x, y)
            #check all stars
            self.checkStars(x, y)
        # print self.screenPos
        # print x, y


    def mouseScrollUp(self, x, y):
        print "scrolling up"

        self.updateScreenPos(min(self.shiftChange, self.maxZoom-self.shift))
        print self.shift

    def mouseScrollDown(self, x, y):
        print "scrolling down"
        self.updateScreenPos((min(-self.shiftChange, self.shift-self.minZoom)))
        print self.shift


############### draw mode functions ##################
    def unpackFile(self):
        directory = os.getcwd()
        lines = [ ]
        actions = [ ] 
        if "savedata.txt" not in os.listdir(directory):
            return 1
            #TODO:popup saying "not available, chk filename savedata.txt"
        info = readFile(os.path.join(os.getcwd(), "savedata.txt")).splitlines()
        date = None
        screenPos = None
        shift = None
        for index in xrange(len(info)):
            action = info[index]
            if action == "": continue
            if index == 0: #should be datetime
                date = datetime.datetime.strptime(action, "%Y %m %d %H %M")
                continue
            elif index == 1: #screenPos and shift
                action = action.split(".")
                screenPos = (int(action[0]), int(action[1]))
                shift = int(action[2])
                city = action[3]
                if city == "Pittsburgh": city = self.pgh
                else: city = ephem.city(city)
                continue
            action = action.split(".")
            # if len(action) < 2: continue
            typeof = action[0]
            line = action[1]
            line = line.split("|")
            # if len(line) < 2: continue
            star1Name = line[0]
            star2Name = line[1]
            star1 = None
            star2 = None
            for star in self.starList:
                if star.name == star1Name:
                    star1 = star
                elif star.name == star2Name:
                    star2 = star
            star1.calculate(city, shift)
            star2.calculate(city, shift)
            newLine = Line(star1, screenPos, star2)
            lines += [ newLine ]
            actions += [ (typeof, newLine) ]
        self.date = date
        self.screenPos = screenPos
        self.shift = shift
        self.lines = copy.copy(lines)
        self.actions = copy.copy(actions)


    def checkDrawButtons(self, x, y):
        for button in self.drawModeButtons:
            #undo, redo, erase, clear, save
            if button.onClick(x, y) == None: continue
            self.selectedDrawButton = button
            if button.name == "erase":
                if self.drawMode == "draw":
                    self.drawMode = "erase"
                else:
                    self.drawMode = "draw"
                    self.selectedDrawButton = None
                return 1
            elif button.name == "undo":
                if self.actions != [ ]:
                    toUndo = self.actions.pop()
                    self.undidActions.append(toUndo)
                    (action, line) = toUndo
                    if action == "erase":
                        self.lines.append(line)
                    elif action == "draw":
                        self.lines.remove(line)
                return 1
            elif button.name == "redo":
                if self.undidActions != [ ]:
                    toRedo = self.undidActions.pop()
                    self.actions.append(toRedo)
                    (action, line) = toRedo
                    if action == "erase":
                        self.lines.remove(line)
                    elif action == "draw":
                        self.lines.append(line)
                return 1
            elif button.name == "clear":
                self.lines = [ ] 
                self.actions = [ ] 
            elif button.name == "save":
                pygame.image.save(self.screen, "screenshot.jpg")
                return 1
            elif button.name == "savefile":
                (left, up) = self.screenPos
                data = (self.date.strftime("%Y %m %d %H %M")+"\n"+str(left)+"."+
                        str(up)+"."+str(self.shift)+"." + self.cityName + "\n")
                for action in self.actions:
                    (typeof, line) = action
                    data += typeof + "."+ str(line)+"\n"
                writeFile("savedata.txt", data)
            elif button.name == "loadfile":
                try:
                    lines = self.unpackFile()
                    if lines == 1: 
                        print ("File not found! Make sure it is named "+ 
                                                        "savedata.txt")
                    #TODO: file not loaded popup?
                    #TODO: popup saying loaded correctly?
                except:
                    print "Not a valid file!"
                




    def printAllLines(self):
        print self.lastAction
        print "erased " + str(self.erasedLines)
        print "undo " + str(self.undidLines)
        print "current " + str(self.lines)

    def checkLines(self, x, y):
        if self.drawMode == "erase":
            erasedLine = None
            for line in self.lines:
                if line.onClick(x, y):
                    erasedLine = line
                    self.lastAction = "erase"
            if erasedLine != None: 
                self.actions.append(("erase", erasedLine))
                self.erasedLines.append(erasedLine)
                self.lines.remove(erasedLine)
                erasedLine = None


############### options mode functions ########################

    def optionsMousePressed(self, x, y):
        (left, up) = self.screenPos
        for button in self.optionsButtons:
            if super(type(button), button).onClick(x,y):
                val = button.onClick(x, y)
                if button.name == "realtime":
                    self.inRealTime = val
                   # print self.inRealTime
                elif isinstance(button, NowButton):
                    self.date = val
                    self.updateOptionButtons()
                elif isinstance(button, ModeButton):
                    if val == "return":
                        self.mode = "main"
                    else:
                        self.mode = val
                   # print self.mode
                else: 
                    self.selectedButton = val
                   # print self.selectedButton
                

    def updateDate(self):
        yr = self.date.year
        mon = self.date.month
        day = self.date.day
        hr = self.date.hour
        mi = self.date.minute
        for button in self.optionsButtons:
            if button.name == "year":
                yr = button.getTime()
            elif button.name == "month":
                mon = button.getTime()
            elif button.name == "day":
                day = button.getTime()
            elif button.name == "hour":
                hr = button.getTime()
            elif button.name == "minute":
                mi = button.getTime()
        self.date = self.date.replace(yr, mon, day, hr, mi)


    def checkStars(self, x, y):
        (left, up) = self.screenPos
        for star in self.starList:
            if star.displayPos(left,up) == None: continue #not on screen
            (cx, cy) = star.displayPos(left,up)
            (width, height) = self.font.size(star.name)
            if (pointInCircle((x,y), (cx, cy), star.r)
                or pointInBox((x,y), (cx, cy, cx+width, cy+height))):
                star.changeInfo()
                return #ensures only one star info shown


    def checkStarsDrawMode(self, x, y):
        (left, up) = self.screenPos
        if self.drawMode == "draw":
            for star in self.starList:
                if star.displayPos(left,up) == None: continue #not on screen
                (cx, cy) = star.displayPos(left,up)
                (width, height) = self.font.size(star.name)
                if (pointInCircle((x,y), (cx, cy), star.r)
                            or pointInBox((x,y), (cx, cy, cx+width, cy+height))):
                        self.selectedDrawButton = None
                        if self.onLine == False:
                            self.lines.append(Line(star, self.screenPos))
                            ## print "appended line"
                            ## print len(self.lines)
                            self.onLine = True
                            return
                        else: #is on a line
                            # print "setting end"
                            self.lines[-1].setEnd(star, self.screenPos)
                            self.actions.append(("draw", self.lines[-1]))
                            self.onLine = False
                            return
            if self.onLine and self.selectedDrawButton==None: 
               # print "removing line"
                if self.lines != [ ]: self.lines.pop()
                self.onLine = False
                return


    def checkNavButtons(self, x, y):
        (left, up) = self.screenPos
        for button in self.buttons:
            if isinstance(button, ZoomButton):
                val = button.onClick(x,y)
                if self.shift+val < 0 or self.shift+val > 10000: continue
                elif val != 0: 
                    self.updateScreenPos(val)
                    return
            elif isinstance(button, ModeButton):
                name = button.onClick(x, y)
                if name != None and self.mode != name: 
                    self.mode = name
                elif name != None and self.mode == name: 
                    self.mode = "main"
                   # print self.mode
                    button.color = self.LIGHT_BLUE


    def resetTimeButtonColors(self):
        for button in self.optionsButtons:
            if isinstance(button, TimeButton) or isinstance(button, ListButton):
                button.color = self.WHITE

        if self.selectedButton != None:
            self.selectedButton.color = self.YELLOW

    def mouseReleased(self, x, y):
        self.justClicked = False

    def mouseMotion(self, x, y):
        if self.onLine:
            #shows line drawing in real time
            if self.lines != [ ]:
                self.lines[-1].updateEndPoint(x, y)

    def mouseDrag(self, x, y):
        if self.mode == "main" or self.mode == "draw":
            if self.justClicked == False:
                self.justClicked = True
                (self.mouseStartX, self.mouseStartY) = (x, y)
            else:
                (posX, posY) = self.screenPos
                (dx, dy) = (self.mouseStartX-x, self.mouseStartY-y)
                if self.legalScreenPos(posX+dx*1//4, posY+dy*1//4):
                    self.screenPos = (posX+dx*1//4, posY+dy*1//4) 
                    #to make the drag slower

    def legalScreenPos(self, x, y):
        return (0-self.margin <= x <= self.shift*2-self.width+2*self.margin
                and 0-self.margin <= y <= self.shift*2-self.height+2*self.margin)

    def keyPressed(self, keyCode, modifier):
        if self.mode == "options" and self.selectedButton != None:
            val = None
            if keyCode == pygame.K_UP:
                val = self.selectedButton.up()
               # print self.date
            elif keyCode == pygame.K_DOWN:
                val = self.selectedButton.down()
            if val != None: 
                if val == "Pittsburgh": self.city = self.pgh
                else: 
                    self.city = ephem.city(val)
                    self.cityName = val

    def keyReleased(self, keyCode, modifier):
        pass


    def timerFired(self, dt):
        if self.mode == "quit":
            pygame.quit()

        if self.inRealTime == True:
            self.date = datetime.datetime.now()

        if self.mode == "options":
            if self.inRealTime == True:
                self.updateOptionButtons()
            else: #is not in real time
                while self.isKeyPressed("K_UP"):
                    if self.selectedButton != None:
                        self.selectedButton.up()
                while self.isKeyPressed("K_DOWN"):
                    if self.selectedButton != None:
                        self.selectedButton.down()
                if self.selectedButton != None:
                    self.updateDate() 

        self.updateCity()
        self.calculateStars()

    def updateCity(self):
        self.city.date = ephem.Date(self.date)
        # self.city.epoch = self.city.date

    def updateOptionButtons(self):
        for button in self.optionsButtons:
            if button.name == "year":
                button.setTimeVal(self.date.year)
            elif button.name == "month":
                button.setTimeVal(self.date.month)
            elif button.name == "day":
                button.setTimeVal(self.date.day)
            elif button.name == "hour":
                button.setTimeVal(self.date.hour)
            elif button.name == "minute":
                button.setTimeVal(self.date.minute)

######################## REDRAW FUNCTIONS ######################################


    def redrawAll(self, screen):
        if self.mode == "options":
            self.drawOptions(screen)
        else:
            self.drawStars(screen)
            self.drawButtons(screen)
            if self.mode == "draw":
                self.drawLines(screen)
                self.drawDrawButtons(screen)
        self.screen = screen

    def drawOptions(self, screen):
        word = "OPTIONS"
        (fx, fy) = self.font.size("OPTIONS")
        x = self.width//2-fx//2
        y = self.height*1//8
        self.drawText(screen, word, x, y, self.font, self.WHITE)

        word = "Date:"
        x = self.width*2//9
        y = self.height*3//8
        self.drawText(screen, word, x, y, self.font, self.WHITE)

        word = "City:"
        x = self.width*2//9
        y = self.height*4//8
        self.drawText(screen, word, x, y, self.font, self.WHITE)

        word = "Stars move in real time:"
        x = self.width*1//9
        y = self.height*5//8
        self.drawText(screen, word, x, y, self.font, self.WHITE)

        self.resetTimeButtonColors()
        for button in self.optionsButtons:
            button.draw(screen, self.font)

    def drawText(self, screen, word, x, y, font, color):
        text = font.render(word, 1, color)
        screen.blit(text, (x, y))

    def drawLines(self, screen):
        for line in self.lines:
            line.draw(screen, self.screenPos)


    def drawButtons(self, screen):
        for button in self.buttons:
            if isinstance(button, ModeButton):
                if button.name == self.mode:
                    button.color = self.GREEN
                button.draw(screen, self.font)
            else:
                button.draw(screen, self.bigFont)

    def drawStars(self, screen):
        for star in self.starList:
            star.calculate(self.city, self.shift)
            (left, up) = self.screenPos
            pos = star.displayPos(left, up)
            if pos != None:
                if pointInBox(pos, (0,0,self.width,self.height)):
                    if star.r < 0: continue
                    pygame.draw.circle(screen, self.WHITE, pos, star.r)
                    label = self.font.render(star.name, 1, self.GREEN)
                    screen.blit(label, pos)
                    if star.showInfo:
                        self.drawStarInfo(star, screen, pos)
        #                 infostar = star
        #                 infopos = pos
        # if infostar != None: self.drawStarInfo(infostar, screen, pos)


    def drawStarInfo(self, star, screen, pos):
        (x, y) = pos
        starObj = star.body 
        # RA will be the longest line
        (width, height)=self.font.size("Right Ascension: " + str(starObj.a_ra))
        fontHeight = height
        height *= 4 #four lines
        pygame.draw.rect(screen, self.BLACK, 
                            pygame.Rect(x, y+fontHeight, width, height))

        # Magnitude
        mag = self.font.render("Magnitude: " + str(starObj.mag), 1, self.WHITE)
        screen.blit(mag, (x, y+self.fontSize+2))
        # RA
        ra=self.font.render("Right Ascension: "+str(starObj.a_ra),1,self.WHITE)
        screen.blit(ra, (x, y+2*self.fontSize+2))
        # Dec
        dec = self.font.render("Declination: "+str(starObj.dec), 1, self.WHITE)
        screen.blit(dec, (x, y+3*self.fontSize+2))
        # Constellation - ephem.constellation(obj)[1] returns the name of
        # the constellation the star is within
        const = self.font.render("Constellation: " +
                        ephem.constellation(starObj)[1], 1, self.WHITE)
        screen.blit(const, (x, y+4*self.fontSize+2))

    # def resetDrawButtonColors(self):
    #     for button in self.drawModeButtons:
    #         if self.drawMode == "erase" and button.name == "erase":
    #             button.color = self.YELLOW
    #         else:
    #             button.color = self.GREEN2
    #     if self.selectedDrawButton != None:
    #         self.selectedDrawButton.color = self.YELLOW

    def drawDrawButtons(self, screen):
        # self.resetDrawButtonColors()
        for button in self.drawModeButtons:
            if self.drawMode == "erase" and button.name == "erase":
                button.drawSelected(screen)
            button.draw(screen, self.font)


    def isKeyPressed(self, key):
        # return whether a specific key is being held 
        return self._keys.get(key, False)



Planetarium().run()