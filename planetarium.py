from __future__ import division

"""
Emily Newman's TP F15

Compatible with Python 2.7

Using Pygame and PyEphem libraries
Uses the Yale Bright Star Catalog, as well as PyEphem's star catalog

YBS available at http://mirrors.dotsrc.org/exherbo/YBS.edb

Used http://mathworld.wolfram.com/Point-LineDistance2-Dimensional.html 
for distance of a point from a line

Icon images obtained from Google Images.

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

-implement quiz
-all the extra stuff (video, readme, etc)

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

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Star) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def changeInfo(self):
        self.showInfo = not self.showInfo

    def calculate(self, ref, shift): #ref = city, shift = Planetarium.shift
        self.body.compute(ref)
        self.r = int(self.body.mag)
        if self.body.alt < 0: #below horizon
            self.screenPos = None
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

    def __hash__(self):
        if self.star2 != None:
            return hash(self.star1.name) + hash(self.star2.name)
        else:
            return hash(self.star1.name) + hash("None")

    def __repr__(self):
        if self.star2 != None:
            return self.star1.name+"|"+self.star2.name
        else:
            return self.star1.name+"|"+"None"

    def __eq__(self, other):
        return (isinstance(other, Line) and (other.star1 == self.star1 
                and other.star2 == self.star2) or (other.star1 == self.star2
                and other.star2 == self.star1))

    def onClick(self, x, y):
        #point distance from a line equation
        (x1, y1, x2, y2) = (self.dispX1, self.dispY1, self.dispX2, self.dispY2)
        d = abs((x2-x1)*(y1-y) - (x1-x)*(y2-y1))
        denom = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if denom != 0: d /= denom
        return d <= 3*self.width

    def setEnd(self, star, ref):
        (left, up) = ref
        self.star2 = star
        (self.x2, self.y2) = self.star2.screenPos
        (self.dispX2, self.dispY2) = self.star2.displayPos(left, up)

    def updateLine(self, ref):
        (left, up) = ref
        (self.dispX1, self.dispY1) = self.star1.displayPos(left, up)
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

class Hint(object):
    def __init__(self, x, y, text, width, height):
        self.x = x
        self.y = y
        self.text = text
        self.show = False
        self.textcolor = (0, 0, 0) #black
        self.bgcolor = (242, 189, 46) #yellowish
        self.width = width
        self.height = height
        self.text2 = "Click here to go back."

    def display(self, value=True):
        self.show = value

    def onClick(self, x, y):
        if (pointInBox((x,y), (self.x, self.y, self.x+self.width, 
                                            self.y+self.height))):
            self.show = False
            return True
        return False

    def draw(self, screen, font):
        if self.show:
            pygame.draw.rect(screen, self.bgcolor, 
                pygame.Rect(self.x, self.y, self.width, self.height))
            text = font.render(self.text, 1, self.textcolor)
            screen.blit(text, (self.x+self.width//2-font.size(self.text)[0]//2, 
                            self.y+self.height//3-font.size(self.text)[1]//2))
            text2 = font.render(self.text2, 1, self.textcolor)
            screen.blit(text2, (self.x+self.width//2-font.size(self.text2)[0]//2, 
                        self.y+self.height*2//3-font.size(self.text2)[1]//2))

    def setText(self, text):
        self.text = text

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

class HintButton(Button):
    def __init__(self, name, x, y, color, width=50, height=50):
        super(HintButton, self).__init__(name, x, y, color, width, height)
        self.icon = pygame.image.load(os.path.join('icons', self.name+'.png'))

    def draw(self, screen, font):
        screen.blit(self.icon, (self.x, self.y))
        
class ModeButton(Button):
    def __init__(self, name, x, y, color, width=25, height=15):
        super(ModeButton, self).__init__(name, x, y, color, width, height)

    def draw(self, screen, font): 
        word = self.name[0].upper() + self.name[1:]
        if (self.width, self.height) == (25, 15): #defaults
            (self.width, self.height) = font.size(word)
        super(ModeButton, self).draw(screen, font)
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
            self.width += 15
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
        self.WHITE = (255, 255, 255)

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
        name = self.name[0].upper() + self.name[1:]
        text = font.render(name, 1, self.WHITE)
        screen.blit(text, (self.x+self.width//2-font.size(name)[0]//2, 
                            self.y-font.size(name)[1]-5))

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
        self.width += 5

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
            return self


class Planetarium(Framework):
    def __init__(self, width=1000, height=666, fps=50, title="PyPlanetarium"):
        super(Planetarium, self).__init__(width, height, fps, title)
        self.initBasics() 

        self.initColors()
        self.initButtons()
        self.initOptionsMode()

        self.inRealTime = False
        self.mode = "splash"
        #draw mode initializing
        self.initDrawMode()
        self.updateOptionButtons()

        self.justClicked = False
        (self.mouseStartX, self.mouseStartY) = (None, None)

        self.infostar = None
        self.infopos = None
        self.lastMode = None
        self.initSplash()
        self.initHelp()
        self.initQuiz()


################################# INIT FUNCTIONS ##############################

    def initBasics(self):
        self.title = "PyPlanetarium"
        self.bgColor = self.BLACK
        self.shift = 1400 #changes with zooming
        #full screen width and height is self.shift*2 at any time
        self.margin = 10
        self.minZoom = 500
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

    def initColors(self):
        self.LIGHT_BLUE = (114, 164, 255) 
        self.RED = (208, 9, 9)
        self.GREEN2 = (0, 204, 0)
        self.PINK = (255, 102, 255)
        self.YELLOW = (255, 255, 0)

    def initQuiz(self):
        self.hint = Hint(self.width//2-175, self.height//2-65, "", 370, 120)
        self.correctMsg = "Correct!"
        size = 50
        self.quizButtons = [
        HintButton("hint", self.width-size, self.height-size, self.YELLOW,
                                                                    size, size)
        ]
        self.constindex = 0
        self.quizzes = ["bigdipper", "littledipper"]
        self.const = self.quizzes[0]

    def initSplash(self):
        self.splashScreen = pygame.image.load(os.path.join("screens",
                                                        "splash.png"))
        self.splashButtons = [
        ModeButton("GO", self.width//2, self.height*7//8, self.GREEN2, 
                    self.bigFont.size("GO")[0],  self.bigFont.size("GO")[1])
        ]
        self.inFastTime = True

    def initButtons(self):
        self.buttons = [ 
        ModeButton("draw", self.width-self.font.size("draw")[0], 0, 
                                        self.LIGHT_BLUE),
        ModeButton("options",self.width-self.font.size("draw")[0] 
                -self.font.size("options")[0]-10, 0, self.LIGHT_BLUE)
                ]

    def initHelp(self):
        self.helpScreen = pygame.image.load(os.path.join("screens", "help.png"))
        self.helpButtons = [
        ModeButton("return", self.width//2-self.font.size("return")[0]//2, 
                            self.height*7//8, self.LIGHT_BLUE)
        ]

    def initOptionsMode(self):
        #splitting the screen into 9ths width wise, 8ths height wise
        self.optionsButtons = [ 
        TimeButton("year", self.width*5//18, self.height*3//8, self.WHITE),
        TimeButton("month", self.width*4//9, self.height*3//8, self.WHITE),
        TimeButton("day", self.width*5//9, self.height*3//8, self.WHITE),
        TimeButton("hour", self.width*6//9, self.height*3//8, self.WHITE),
        TimeButton("minute", self.width*7//9, self.height*3//8, self.WHITE),
        NowButton("now", self.width*8//9, self.height*3//8, self.PINK, 33),
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
            ModeButton("quiz", 0, 0, self.PINK),
            ModeButton("help", self.width-self.font.size("Options")[0]-
                            self.font.size("Draw")[0]-60, 0, self.LIGHT_BLUE),
            DrawButton("erase", 0, self.height//8, self.YELLOW, size, size),
            DrawButton("undo", 0, self.height*2//8, self.YELLOW, size, size),
            DrawButton("redo", 0, self.height*3//8, self.YELLOW, size, size),
            DrawButton("clear", 0, self.height*4//8, self.YELLOW, size, size),
            DrawButton("save", 0, self.height*5//8, self.YELLOW, size, size),
            DrawButton("loadfile", 0, self.height*6//8,self.YELLOW, size, size),
            DrawButton("savefile", 0, self.height*7//8, self.YELLOW, size, size)
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


########################## LOAD FROM FILE FUNCTIONS ###########################


    def readInDB(self, path):
        #returns list of Star objects from all stars in DB
        db = readFile(path)
        starList = [ ] 
        for line in db.splitlines():
            if line.startswith("#") or line == "": continue
            line = line.strip()
            body = ephem.readdb(line)
            if body.name == "Benetnasch": continue #duplicate of Alkaid
            starList.append(Star(body.name, body))
        return starList

    def unpackFile(self, source="savedata.txt", folder=""):
        directory = os.getcwd()
        if folder == "": pass
        else:
            directory = os.path.join(directory, folder)
        lines = [ ]
        actions = [ ] 
        if source not in os.listdir(directory):
            return 1
            #TODO:popup saying "not available, chk filename savedata.txt"
        info = readFile(os.path.join(directory, source)).splitlines()
        date = None
        screenPos = None
        shift = None
        for index in xrange(len(info)):
            action = info[index]
            if action == "": continue
            if index == 0: #datetime
                date = datetime.datetime.strptime(action, "%Y %m %d %H %M")
                continue
            elif index == 1: #screenPos and shift
                action = action.split(".")
                screenPos = (int(action[0]), int(action[1]))
                shift = int(action[2])
                city = action[3]
                if city == "Pittsburgh": city = self.pgh
                else: city = ephem.city(city)
                city.date = date
                continue
            action = action.split(".")
            typeof = action[0]
            line = action[1]
            line = line.split("|")
            (star1Name, star2Name) = (line[0], line[1])
            (star1, star2) = (None, None)
            for star in self.starList:
                if star.name == star1Name:
                    star1 = star
                elif star.name == star2Name:
                    star2 = star
            star1.calculate(city, shift)
            star2.calculate(city, shift)
            newLine = Line(star1, screenPos)
            newLine.setEnd(star2, screenPos)
            lines += [ newLine ]
            actions += [ (typeof, lines[-1]) ]
        self.date = date
        self.screenPos = screenPos
        self.shift = shift
        self.lines = copy.copy(lines)
        self.actions = copy.copy(actions)

    def loadConstellation(self, const):
        self.const = const
        folder = "const" #where all constellations are
        self.unpackFile(const+".txt", folder)
        self.constLines = copy.copy(self.lines)
        #create set of stars in constellation
        self.constStars = set()
        for line in self.constLines:
            self.constStars.add(line.star1)
            self.constStars.add(line.star2)
        self.lines = [ ]
        self.actions = [ ]


################################ UPDATE FUNCTIONS #############################


    def calculateStars(self):
        for star in self.starList:
            star.calculate(self.city, self.shift)

    def updateScreenPos(self, shiftChange, x=0, y=0):
        (oldX, oldY) = self.screenPos
        if shiftChange == 0:
            self.screenPos = (x+oldX, y+oldY)
        else:
            oldShift = self.shift
            self.shift += shiftChange
            self.screenPos=(oldX*self.shift/oldShift, oldY*self.shift/oldShift)

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

    def resetTimeButtonColors(self):
        for button in self.optionsButtons:
            if isinstance(button, TimeButton) or isinstance(button, ListButton):
                button.color = self.WHITE
        if self.selectedButton != None:
            self.selectedButton.color = self.YELLOW

    def resetDrawMode(self):
        self.date = datetime.datetime.now()
        self.city = self.pgh
        self.screenPos = (self.shift-self.width//2, self.shift-self.height//2)


############################### quiz functions ##############################


    def checkAnswer(self):
        lines = set(self.lines) #gets rid of duplicates
        constLines = set(self.constLines)
        stars = set()
        for line in self.lines:
            stars.add(line.star1)
            stars.add(line.star2)
        diff = len(self.constStars) - len(stars)
        linediff = len(constLines) - len(lines)
        if diff > 0 or (diff==0 and stars!=self.constStars): 
            #not enough stars! find missing star
            missingStars = self.constStars - stars
            #get stars in constellation but not in drawing
            hintStar = missingStars.pop()
            hinttext = "Hint: You are missing " + str(hintStar)
        elif diff < 0: #too many stars! find the extra star
            extraStars = stars - self.constStars
            #get stars in drawing that arent in constellation
            hintStar = extraStars.pop()
            hinttext = "Hint: "+str(hintStar)+" does not belong!"
        elif linediff < 0 or (linediff==0 and lines!=constLines):
            #too many lines/lines where they shouldn't belong
            wrongLines = lines - constLines
            #get the lines in drawing not in constellations
            hintLine = wrongLines.pop()
            hinttext = ("Hint: " +hintLine.star1.name+" and "+
                    hintLine.star2.name+" shouldn't be connected!")
        elif linediff > 0:
            #not enough lines! find the missing line
            missingLines = constLines - lines
            hintLine = missingLines.pop()
            star1, star2 = hintLine.star1, hintLine.star2
            hinttext = ("Hint: " +str(star1)+" and "+str(star2)+" should be" 
                                                        +" connected!")
        else:
            hinttext = self.correctMsg
        return hinttext


########################### CHECK FUNCTIONS ##############################


    def checkDrawButtons(self, x, y):
        for button in self.drawModeButtons:
            #undo, redo, erase, clear, save
            if button.onClick(x, y) == None: continue
            self.selectedDrawButton = button
            if isinstance(button, ModeButton):
                self.lastMode = self.mode
                if self.mode == "draw" and button.name == "quiz":
                    self.loadConstellation(self.quizzes[0])
                    self.mode = button.name
                elif self.mode == "quiz" and button.name == "quiz":
                    self.mode = "draw"
                else:
                    self.mode = button.name
            elif button.name == "erase":
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
                data = (self.date.strftime("%Y %m %d %H %M")+"\n"+str(int(left))
                        +"."+str(int(up))+"."+str(self.shift)+"." + 
                        self.cityName + "\n")
                for action in self.actions:
                    (typeof, line) = action
                    data += typeof + "."+ str(line)+"\n"
                writeFile("savedata.txt", data)
                print "File saved successfully to savedata.txt!" #TODO popup?
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

    def checkLines(self, x, y):
        if self.drawMode == "erase":
            erasedLine = None
            for line in self.lines: #FLAG error here
                if line.onClick(x, y):
                    erasedLine = line
                    self.lastAction = "erase"
            if erasedLine != None: 
                self.actions.append(("erase", erasedLine))
                self.erasedLines.append(erasedLine)
                self.lines.remove(erasedLine)
                erasedLine = None

    def checkStarsDrawMode(self, x, y):
        (left, up) = self.screenPos
        if self.drawMode == "draw":
            for star in self.starList:
                if star.displayPos(left,up) == None: continue #not on screen
                (cx, cy) = star.displayPos(left,up)
                (width, height) = self.smallFont.size(star.name)
                if pointInCircle((x,y), (cx, cy), star.r):
                    self.selectedDrawButton = None
                    if self.onLine == False:
                        self.lines.append(Line(star, self.screenPos))
                        self.onLine = True
                    else: #is on a line
                        if star != self.lines[-1].star1 and self.lines!=[]:
                            self.lines[-1].setEnd(star, self.screenPos)
                            self.actions.append(("draw", self.lines[-1]))
                        elif self.lines!=[]:
                            self.lines.pop(-1)
                        self.onLine = False
                    return 1
            check = self.checkStarLabelsDrawMode(x, y)  
            if check == 1: return 1
            if self.onLine and self.selectedDrawButton==None: 
                if self.lines != [ ]: self.lines.pop()
                self.onLine = False
                return 1   

    def checkStarLabelsDrawMode(self, x, y):
        (left, up) = self.screenPos
        if self.drawMode == "draw":
            for star in self.starList:
                if star.displayPos(left,up) == None: continue #not on screen
                (cx, cy) = star.displayPos(left,up)
                (width, height) = self.smallFont.size(star.name)
                if pointInBox((x,y),(cx, cy, cx+width, cy+height)):
                    self.selectedDrawButton = None
                    if self.onLine == False:
                        self.lines.append(Line(star, self.screenPos))
                        self.onLine = True
                        return 1
                    else: #is on a line
                        if star != self.lines[-1].star1:
                            self.lines[-1].setEnd(star, self.screenPos)
                            self.actions.append(("draw", self.lines[-1]))
                        else:
                            self.lines.pop(-1)
                        self.onLine = False
                        return 1

    def optionsMousePressed(self, x, y):
        (left, up) = self.screenPos
        for button in self.optionsButtons:
            if super(type(button), button).onClick(x,y):
                val = button.onClick(x, y)
                if button.name == "realtime":
                    self.inRealTime = val
                elif isinstance(button, NowButton):
                    self.date = val
                    self.updateOptionButtons()
                elif isinstance(button, ModeButton):
                    if val == "return":
                        self.mode = self.lastMode
                    else:
                        self.mode = val
                else: 
                    self.selectedButton = val

    def checkStars(self, x, y):
        (left, up) = self.screenPos
        for star in self.starList:
            if star.displayPos(left,up) == None: continue #not on screen
            (cx, cy) = star.displayPos(left,up)
            (width, height) = self.smallFont.size(star.name)
            if (pointInCircle((x,y), (cx, cy), star.r)
                        or pointInBox((x,y), (cx, cy, cx+width, cy+height))):
                self.infostar = star
                return #ensures only one star info shown
        self.infostar = None

    def checkNavButtons(self, x, y):
        (left, up) = self.screenPos
        for button in self.buttons:
            name = button.onClick(x, y)
            if name != None and self.mode != name: 
                self.lastMode = self.mode
                self.mode = name
                if self.mode == "draw": 
                    self.inRealTime = False
                    self.infostar = None
                elif self.mode == "options":
                    self.updateOptionButtons()
                return
            elif name != None and self.mode == name: 
                self.mode = "main"
                button.color = self.LIGHT_BLUE
                return

    def legalScreenPos(self, x, y):
        return (0-self.margin <= x <= self.shift*2-self.width+2*self.margin
                and 0-self.margin <= y <= self.shift*2-self.height+2*self.margin)

    def checkSplashButtons(self, x, y):
        for button in self.splashButtons:
            if super(type(button), button).onClick(x, y):
                if isinstance(button, ModeButton) and button.name == "GO": 
                    self.mode = "main"
                    self.inFastTime = False

    def checkHelpButtons(self, x, y):
        for button in self.helpButtons:
            if super(type(button), button).onClick(x, y):
                if isinstance(button, ModeButton) and button.name == "return":
                    self.mode = self.lastMode

    def checkQuizButtons(self, x, y):
        for button in self.quizButtons:
            if super(type(button), button).onClick(x, y):
                if isinstance(button, HintButton) and button.name == "hint":
                    #if box is check: click again to move to next const
                    result = self.checkAnswer()
                    self.hint.setText(result)
                    self.hint.display() 

    def checkHint(self, x, y):
        clicked = self.hint.onClick(x, y)
        if (clicked and (self.hint.text == "Correct!" or 
                    self.hint.text == "You have completed the quiz!")):
            self.constindex+=1
            self.hint.text = ""
            if self.constindex == len(self.quizzes):
                self.hint.setText("You have completed the quiz!")
                self.lines = [ ]
                self.hint.display(True)
            elif self.constindex > len(self.quizzes):
                self.hint.setText("")
                self.mode = "draw"
                self.infostar = None
                self.resetDrawMode()
            else:
                self.loadConstellation(self.quizzes[self.constindex])


################################# BASE FUNCTIONS ##############################


    def mousePressed(self, x, y):
        #Splash screen
        if self.mode == "splash":
            self.checkSplashButtons(x, y)
        elif self.mode == "help":
            self.checkHelpButtons(x, y)
        #Options screen:
        elif self.mode == "options":
            self.optionsMousePressed(x, y)
        #In main screen:
        #check all buttons
        elif self.mode == "draw" or self.mode == "quiz":
            if self.mode == "quiz": 
                self.checkHint(x, y)
                self.checkQuizButtons(x, y)
            check = self.checkDrawButtons(x, y)
            if check == 1: return 
            #check the nav buttons
            check = self.checkNavButtons(x, y)
            if check == 1: return
            check = self.checkStarsDrawMode(x, y)
            if check==1: return
            self.checkLines(x, y)


        elif self.mode == "main":
            #check all buttons
            check = self.checkNavButtons(x, y)
            if check == 1: return
            #check all stars
            self.checkStars(x, y)

    def mouseReleased(self, x, y):
        self.justClicked = False

    def mouseMotion(self, x, y):
        if self.onLine:
            #shows line drawing in real time
            if self.lines != [ ]:
                self.lines[-1].updateEndPoint(x, y)

    def mouseDrag(self, x, y):
        if self.mode == "main" or self.mode == "draw" or self.mode == "quiz":
            if self.justClicked == False:
                self.justClicked = True
                (self.mouseStartX, self.mouseStartY) = (x, y)
            else:
                (posX, posY) = self.screenPos
                (dx, dy) = (self.mouseStartX-x, self.mouseStartY-y)
                if self.legalScreenPos(posX+dx*1//4, posY+dy*1//4):
                    self.screenPos = (posX+dx*1//4, posY+dy*1//4)


                    #to make the drag slower

    def keyPressed(self, keyCode, modifier):
        if self.mode == "options" and self.selectedButton != None:
            val = None
            if keyCode == pygame.K_UP:
                val = self.selectedButton.up()
            elif keyCode == pygame.K_DOWN:
                val = self.selectedButton.down()
            if val != None: 
                if val == "Pittsburgh": 
                    self.city = self.pgh
                    self.cityName = val
                else: 
                    self.city = ephem.city(val)
                    self.cityName = val

    def keyReleased(self, keyCode, modifier):
        pass

    def isKeyPressed(self, key):
        # return whether a specific key is being held 
        return self._keys.get(key, False)

    def mouseScrollUp(self, x, y):
        self.updateScreenPos(min(self.shiftChange, self.maxZoom-self.shift))

    def mouseScrollDown(self, x, y):
        if self.shift-self.shiftChange < self.minZoom:
            pass
        else:
            self.updateScreenPos(-self.shiftChange)

    def timerFired(self, dt):
        if self.mode == "quit":
            pygame.quit()

        if self.inFastTime:
            newMinute = self.date.minute+1
            newHour = self.date.hour
            if self.date.minute+1 >= 60: 
                newMinute = (self.date.minute+1)%60
                newHour = self.date.hour+1
            self.date = self.date.replace(self.date.year, self.date.month, 
                            self.date.day, newHour%23, newMinute)
            self.updateCity()

        elif self.inRealTime:
            self.date = datetime.datetime.now()
            self.updateCity()

        if self.mode == "draw" or self.mode == "quiz":
            for line in self.lines:
                if line.star2 != None:
                    line.updateLine(self.screenPos) 

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


######################## REDRAW FUNCTIONS ######################################


    def redrawAll(self, screen):
        if self.mode == "splash":
            self.drawSplash(screen)
        elif self.mode == "options":
            self.drawOptions(screen)
        elif self.mode == "help":
            self.drawHelp(screen)
        elif self.mode == "main":
            self.drawStars(screen)
            self.drawButtons(screen)
        elif self.mode == "draw":
            self.drawStars(screen)
            self.drawLines(screen)
            self.drawButtons(screen)
            self.drawDrawButtons(screen)
        elif self.mode == "quiz":
            self.drawStars(screen)
            self.drawLines(screen)
            self.drawButtons(screen)
            self.drawDrawButtons(screen)
            self.drawQuiz(screen)
        self.screen = screen

    def drawSplash(self, screen):
        self.drawStars(screen, False)
        screen.blit(self.splashScreen, (0, 0))
        for button in self.splashButtons:
            button.draw(screen, self.bigFont)

    def drawOptions(self, screen):
        word = "OPTIONS"
        (fx, fy) = self.font.size("OPTIONS")
        x = self.width//2-fx//2
        y = self.height*1//8
        self.drawText(screen, word, x, y, self.font, self.WHITE)

        word = "Date:"
        x = self.width*1//9
        y = self.height*3//8
        self.drawText(screen, word, x, y, self.font, self.WHITE)

        word = "City:"
        x = self.width*2//9
        y = self.height*4//8
        self.drawText(screen, word, x, y, self.font, self.WHITE)

        word = "Stars move in real time:"
        x = self.width*1//18
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

    def drawStars(self, screen, drawNames=True):
        (left, up) = self.screenPos
        for star in self.starList:
            star.calculate(self.city, self.shift)
            
            pos = star.displayPos(left, up)
            if pos != None:
                if pointInBox(pos, (0,0,self.width,self.height)):
                    if star.r < 0: continue
                    pygame.draw.circle(screen, self.WHITE, pos, star.r)
                    if drawNames:
                        label = self.smallFont.render(star.name, 1, self.GREEN)
                        screen.blit(label, pos)
        if self.infostar == None: return        
        self.drawStarInfo(self.infostar, screen, self.infostar.displayPos(left, up))

    def drawStarInfo(self, star, screen, pos):
        (x, y) = pos
        starObj = star.body 
        # RA will be the longest line
        (width, height) = self.smallFont.size(
                                    "Right Ascension: " + str(starObj.a_ra))
        fontHeight = height
        pygame.draw.rect(screen, self.BLACK, 
                            pygame.Rect(x, y+fontHeight, width, height*4 + 8))

        # Magnitude
        mag = self.smallFont.render("Magnitude: " + str(starObj.mag), 1, 
                                                                self.WHITE)
        screen.blit(mag, (x, y+height+2))
        # RA
        ra=self.smallFont.render("Right Ascension: "+str(starObj.a_ra),1,
                                                                    self.WHITE)
        screen.blit(ra, (x, y+2*height+2))
        # Dec
        dec = self.smallFont.render("Declination: "+str(starObj.dec), 1, 
                                                                    self.WHITE)
        screen.blit(dec, (x, y+3*height+2))
        # Constellation - ephem.constellation(obj)[1] returns the name of
        # the constellation the star is within
        const = self.smallFont.render("Constellation: " +
                        ephem.constellation(starObj)[1], 1, self.WHITE)
        screen.blit(const, (x, y+4*height+2))

    def drawDrawButtons(self, screen):
        for button in self.drawModeButtons:
            font = self.font
            if self.drawMode == "erase" and button.name == "erase":
                button.drawSelected(screen)
            if button.name == "quiz":
                font = self.bigFont
                if self.mode == "quiz": button.color = self.GREEN
                else: button.color = self.PINK
            button.draw(screen, font)

    def drawHelp(self, screen):
        screen.blit(self.helpScreen, (0,0))
        for button in self.helpButtons:
            button.draw(screen, self.font)

    def drawQuiz(self, screen):
        const=""
        if self.const == "bigdipper":
            const = "The Big Dipper!"
        elif self.const == "littledipper":
            const = "The Little Dipper!"
        title = self.bigFont.render("Draw: " + const, 1, self.WHITE)
        screen.blit(title, 
                (self.width//2-50-self.bigFont.size("Draw: "+const)[0]//2, 0))
        for button in self.quizButtons:
            button.draw(screen, self.font)
        self.hint.draw(screen, self.smallFont)


Planetarium().run()