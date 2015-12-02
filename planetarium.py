from __future__ import division

"""
Emily Newman's TP F15

Using Pygame and PyEphem libraries
Uses the Yale Bright Star Catalog, as well as PyEphem's star catalog

Used http://mathworld.wolfram.com/Point-LineDistance2-Dimensional.html 
for distance of a point from a line
"""
import pygame
from framework import Framework 
import ephem
import ephem.stars
import datetime, time
import math
import copy



# from the class notes on Basic File I/O
# http://www.cs.cmu.edu/~112/notes/notes-strings.html#basicFileIO
def readFile(path): 
    with open(path, "rt") as f:
        return f.read()

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

    def calculate(self, ref, shift):
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
    def __init__(self, startStar, screenPos):
        (left, up) = screenPos
        self.star1 = startStar
        (self.dispX1, self.dispY1) = self.star1.displayPos(left, up)
        (self.x1, self.y1) = self.star1.screenPos
        self.star2 = None
        (self.x2, self.y2) = self.star1.screenPos
        (self.dispX2, self.dispY2) = (self.dispX1, self.dispY1)
        self.color = (255, 255, 255) #white
        self.width = 2

    def onClick(self, x, y):
        #point distance from a line equation
        (x1, y1, x2, y2) = (self.dispX1, self.dispY1, self.dispX2, self.dispY2)
        d = abs((x2-x1)*(y1-y) - (x1-x)*(y2-y1))
        denom = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if denom != 0: d /= denom
       # print "successful click"
        return d <= self.width

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

class DirButton(Button):
    def __init__(self, name, x, y, color, width=25, height=15):
        super(DirButton, self).__init__(name, x, y, color, width, height)
        self.dirX = 0
        self.dirY = 0
        self.d = 10
        if self.name == "left":
            self.dirX = -1
            self.char = "<"
        elif self.name == "right":
            self.dirX = 1
            self.char = ">"
        elif self.name == "up":
            self.dirY = -1
            self.char = "^"
        elif self.name == "down":
            self.dirY = 1
            self.char = "v"

    def onClick(self, x, y):
        if pointInBox((x,y), (self.x, self.y, self.x+self.width, 
                                            self.y+self.height)):
            return self.dirX*self.d if self.dirX != 0 else self.dirY*self.d
        return 0

    def draw(self, screen, font):   
        super(DirButton, self).draw(screen, font)
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
        elif self.name == "month":
            self.minTime = 1
            self.maxTime = 12
        elif self.name == "day":
            self.minTime = 1
            self.maxTime = 31 #to be controlled in Planetarium
        else: #hour, minute
            self.maxTime = 59
        self.timeVal = 0
        self.YELLOW = (255, 255, 0)

    def timeUp(self):
        if self.minTime <= self.timeVal+1 <= self.maxTime:
            self.timeVal += 1

    def timeDown(self):
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

class DrawButton(Button):
    def draw(self, screen, font):
        super(DrawButton, self).draw(screen, font)
        word = self.name[0].upper() + self.name[1:]
        text = font.render(word, 1, self.BLACK)
        screen.blit(text, (self.x, self.y))

    def onClick(self, x, y):
        if pointInBox((x,y), (self.x, self.y, self.x+self.width, 
                                            self.y+self.height)):
           # print "clicked line"
            return self


class Planetarium(Framework):
    def __init__(self, width=600, height=400, fps=50, title="PGH Planetarium"):
        super(Planetarium, self).__init__()
        self.title = "PGH Planetarium"
        self.bgColor = self.BLACK
        self.shift = 1000 #changes with zooming?
        #full screen width and height
        self.fullWidth = self.shift*2
        self.fullHeight = self.shift*2

        (self.MIN_ALT, self.MAX_ALT) = (0, math.pi/2)
        (self.MIN_AZ, self.MAX_AZ) = (0, 2*math.pi) #radians
        # upper left corner of screen in terms of sky
        # starts w/ center of screen being (0,0) of sky
        self.screenPos = (self.fullWidth//2, self.fullHeight//2)
        self.date = datetime.datetime.now() #always Datetime form
        self.starList = [ ]
        self.initPittsburgh()
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

    def initButtons(self):
        self.buttons = [ 
        ZoomButton("zoomIn", 0, 0, self.LIGHT_BLUE),
        ZoomButton("zoomOut", 25, 0, self.LIGHT_BLUE),
        DirButton("up", self.width-50, self.height-50,
                                        self.LIGHT_BLUE),
        DirButton("down", self.width-50, self.height-20,
                                        self.LIGHT_BLUE),
        DirButton("left", self.width-75, self.height-35,
                                        self.LIGHT_BLUE),
        DirButton("right", self.width-25, self.height-35,
                                        self.LIGHT_BLUE) ,
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
        ToggleButton("realtime", self.width//2-self.font.size("OFF")[0]//2, 
                                    self.height*5//8, self.RED),
        ModeButton("return", self.width//2-self.font.size("Return")[0]//2, 
                                self.height*6//8, self.GREEN2),
        ModeButton("quit", self.width//2-self.font.size("Quit")[0]//2,
                        self.height*7//8, self.RED )
        ]
        self.selectedTimeButton = None


    def initDrawMode(self):
        size = self.height//7
        self.drawModeButtons = [ 
                                DrawButton("erase", 0, self.height*2//7, 
                                                    self.GREEN2, size, size),
                                DrawButton("undo", 0, self.height*3//7, 
                                                    self.GREEN2, size, size),
                                DrawButton("redo", 0, self.height*4//7, 
                                                    self.GREEN2, size, size),
                                DrawButton("save", 0, self.height*5//7, 
                                                    self.GREEN2, size, size),
                                DrawButton("clear", 0, self.height*6//7, 
                                                    self.GREEN2, size, size)
                                ]
        self.onLine = False
        self.lines = [ ]
        self.undidLines = [ ]
        self.erasedLines = [ ] 
        self.lastAction = "draw"
        self.selectedDrawButton = None
        self.drawMode = "draw"

    def initStars(self):
        for star in ephem.stars.db.split("\n"):
            starName = star.split(",")[0]
            if starName == "": continue #not a star
            self.starList.append(Star(starName, ephem.star(starName)))


    def initPittsburgh(self):
        self.pgh = ephem.Observer()
        self.pgh.lat = "40:26:26.3"
        self.pgh.long = "-79:59:45.20" 
        self.pgh.date = ephem.Date(self.date)

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

    def calculateStars(self):
        for star in self.starList:
            star.calculate(self.pgh, self.shift)


    def updateScreenPos(self, shift, x=0, y=0):
        (oldX, oldY) = self.screenPos
        if shift == 0:
            self.screenPos = (x+oldX, y+oldY)
        else:
            self.shift += shift
            self.screenPos = (oldX+shift, oldY+shift)


    def mousePressed(self, x, y):
        #Options screen:
        if self.mode == "options":
            self.optionsMousePressed(x, y)

        #In main screen:
        #check all buttons
        elif self.mode == "draw":
            check = self.checkDrawButtons(x, y)
            if check == 1: return 
            self.checkButtons(x, y)
            self.checkStars(x, y)
            self.checkLines(x, y)

        elif self.mode == "main":
            #check all buttons
            self.checkButtons(x, y)
            #check all stars
            self.checkStars(x, y)

    def checkDrawButtons(self, x, y):
        for button in self.drawModeButtons:
            #undo, redo, erase, clear, save
            if button.onClick(x, y) == None: continue
            self.selectedDrawButton = button
            if button.name == "undo":
                if self.lastAction == "draw":
                    if self.lines != [ ]:
                        self.undidLines.append(self.lines.pop())
                        return 1
                   # print self.undidLines
                   # print self.lines
                elif self.lastAction == "erase":
                    if self.erasedLines != [ ]:
                        self.lines.append(self.erasedLines.pop())
                        return 1
                   # print self.erasedLines
                   # print self.lines
                elif self.lastAction == "clear":
                    self.lines = copy.copy(self.erasedLines)
                    self.erasedLines = [ ]
                    return 1
            elif button.name == "redo":
                if self.lastAction == "draw":
                    if self.undidLines != [ ]:
                        self.lines.append(self.undidLines.pop())
                        return 1
                   # print self.undidLines
                   # print self.lines
                elif self.lastAction == "erase":
                    if self.lines != [ ]:
                        self.erasedLines.append(self.lines.pop())
                        return 1
                   # print self.erasedLines
                   # print self.lines
                elif self.lastAction == "clear":
                    self.erasedLines = copy.copy(self.lines)
                    self.lines = [ ]
                    return 1
                   # print self.erasedLines
                   # print self.lines
            elif button.name == "erase":
                if self.drawMode == "draw":
                    self.drawMode = "erase"
                    return 1
                else:
                    self.drawMode = "draw"
                    self.selectedDrawButton = None
                    return 1
            elif button.name == "clear":
                self.lastAction = "clear"
                self.erasedLines = copy.copy(self.lines)
                self.lines = [ ] 
               # print self.erasedLines
               # print self.lines
                return 1
            elif button.name == "save":
                pygame.image.save(self.screen, "screenshot.jpg")
                return 1
            #todo implement save

    def checkLines(self, x, y):
        if self.drawMode == "erase":
            erasedLine = None
            for line in self.lines:
                if line.onClick(x, y):
                    erasedLine = line
                    self.lastAction = "erase"
            if erasedLine != None: 
                self.erasedLines.append(erasedLine)
                self.lines.remove(erasedLine)
                erasedLine = None



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
                    self.selectedTimeButton = val
                   # print self.selectedTimeButton
                

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
            if self.mode == "main":
                if (pointInCircle((x,y), (cx, cy), star.r)
                    or pointInBox((x,y), (cx, cy, cx+width, cy+height))):
                    star.changeInfo()
                    return #ensures only one star info shown
            elif self.mode == "draw":
                if (pointInCircle((x,y), (cx, cy), star.r)
                        or pointInBox((x,y), (cx, cy, cx+width, cy+height))):
                    if self.onLine == False:
                        self.lines.append(Line(star, self.screenPos))
                        ## print "appended line"
                        ## print len(self.lines)
                        self.onLine = True
                        return
                    else: #is on a line
                        ## print "setting end"
                        self.lines[-1].setEnd(star, self.screenPos)
                        self.onLine = False
                        return
        if self.mode=="draw" and self.onLine and self.selectedDrawButton==None: 
           # print "removing line"
            if self.lines != [ ]: self.lines.pop()
            self.onLine = False
            return

    def checkButtons(self, x, y):
        (left, up) = self.screenPos
        for button in self.buttons:
            if isinstance(button, ZoomButton):
                val = button.onClick(x,y)
                if self.shift+val < 0 or self.shift+val > 10000: continue
                elif val != 0: 
                    self.updateScreenPos(val)
                    return
            elif isinstance(button, DirButton):
                val = button.onClick(x,y)
                (sx,sy) = (0,0)
                if button.name == "left" or button.name == "right":
                    sx = val
                else:
                    sy = val
                self.updateScreenPos(0, sx, sy)
                if sx !=0 or sy!=0: return
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
            if isinstance(button, TimeButton):
                button.color = self.WHITE

        if self.selectedTimeButton != None:
            self.selectedTimeButton.color = self.YELLOW

    def mouseReleased(self, x, y):
        pass

    def mouseMotion(self, x, y):
        if self.onLine:
            #shows line drawing in real time
            if self.lines != [ ]:
                self.lines[-1].updateEndPoint(x, y)

    def mouseDrag(self, x, y):
        pass

    def keyPressed(self, keyCode, modifier):
        if self.mode == "options":
            if keyCode == pygame.K_UP:
                self.selectedTimeButton.timeUp()
               # print self.date
            elif keyCode == pygame.K_DOWN:
                self.selectedTimeButton.timeDown()
               # print self.date


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
                    if self.selectedTimeButton != None:
                        self.selectedTimeButton.timeUp()
                while self.isKeyPressed("K_DOWN"):
                    if self.selectedTimeButton != None:
                        self.selectedTimeButton.timeDown()
                if self.selectedTimeButton != None:
                    self.updateDate() 

        self.updatePgh()
        self.calculateStars()

    def updatePgh(self):
        self.pgh.date = ephem.Date(self.date)
        # self.pgh.epoch = self.pgh.date

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
            star.calculate(self.pgh, self.shift)
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


    def drawStarInfo(self, star, screen, pos):
        (x, y) = pos
        starObj = star.body
        #Magnitude
        mag = self.font.render("Magnitude: " + str(starObj.mag), 1, self.WHITE)
        screen.blit(mag, (x, y+self.fontSize+2))
        #RA
        ra=self.font.render("Right Ascension: "+str(starObj.a_ra),1,self.WHITE)
        screen.blit(ra, (x, y+2*self.fontSize+2))
        #Dec
        dec = self.font.render("Declination: "+str(starObj.dec), 1, self.WHITE)
        screen.blit(dec, (x, y+3*self.fontSize+2))
        #Constellation
        const = self.font.render("Constellation: " +
                        ephem.constellation(starObj)[1], 1, self.WHITE)
        screen.blit(const, (x, y+4*self.fontSize+2))

    def resetDrawButtonColors(self):
        for button in self.drawModeButtons:
                button.color = self.GREEN2
        if self.selectedDrawButton != None:
            self.selectedDrawButton.color = self.YELLOW

    def drawDrawButtons(self, screen):
        self.resetDrawButtonColors()
        for button in self.drawModeButtons:
            button.draw(screen, self.font)


    def isKeyPressed(self, key):
        # return whether a specific key is being held 
        return self._keys.get(key, False)



Planetarium().run()