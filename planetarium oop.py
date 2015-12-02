from __future__ import division

"""
Emily Newman's TP F15

Using Pygame and PyEphem libraries
"""
import pygame
from framework import Framework 
import ephem
import ephem.stars
import datetime, time
import math



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

    def setEnd(self, star, ref):
        (left, up) = ref
        self.star2 = star
        (self.x2, self.y2) = self.star2.screenPos
        (self.dispX2, self.dispY2) = self.star2.displayPos


    def updateEndPoint(self, x, y):
        #only used temporarily for aesthetic purposes
        self.dispX2 = x
        self.dispY2 = y

    def displayPoints(self, ref):
        (left, up) = ref
        if self.star2 == None:
            return (self.star1.displayPos(left,up), (self.x2, self.y2))
        else:
            return (self.star1.displayPos, self.star2.displayPos)

    def draw(self, screen, ref):
        (start, end) = self.displayPoints(ref)
        start = list(start)
        end = list(end)
        pygame.draw.line(screen, self.color, start, end, 2)



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


class Planetarium(Framework):
    def __init__(self, width=600, height=400, fps=50, title="PGH Planetarium"):
        super(Planetarium, self).__init__()
        self.title = "PGH Planetarium"
        self.bgColor = self.BLACK
        self.shift = 500 #changes with zooming?
        #full screen width and height
        self.fullWidth = self.shift*2
        self.fullHeight = self.shift*2
        self.log = dict() #stores all stars based on computed values WRT PGH
        self.pos = dict() #stores all screen positions of stars
        (self.MIN_ALT, self.MAX_ALT) = (0, math.pi/2)
        (self.MIN_AZ, self.MAX_AZ) = (0, 2*math.pi) #radians
        # upper left corner of screen in terms of sky
        # starts w/ center of screen being (0,0) of sky
        self.screenPos = (0,0)
        self.date = datetime.datetime.now() #always Datetime form
        self.starList = [ ]
        self.initPittsburgh()
        self.initStars()
        #read in more stars!
        yaleCatalog = self.readInDB("ybs.edb")
        self.starList += yaleCatalog
        self.zoomColor = (114, 164, 255) #light blue
        self.buttons = [ 
                ZoomButton("zoomIn", 0, 0, self.zoomColor),
                ZoomButton("zoomOut", 25, 0, self.zoomColor),
                DirButton("up", self.width-50, self.height-50,
                                                self.zoomColor),
                DirButton("down", self.width-50, self.height-20,
                                                self.zoomColor),
                DirButton("left", self.width-75, self.height-35,
                                                self.zoomColor),
                DirButton("right", self.width-25, self.height-35,
                                                self.zoomColor) ,
                ModeButton("draw", self.width-self.font.size("draw")[0], 0, 
                                                self.zoomColor),
                ModeButton("options",self.width-self.font.size("draw")[0] 
                            -self.font.size("options")[0]-10, 0, self.zoomColor)
                        ]

        self.inRealTime = False
        self.mode = "main"

        #draw mode initializing
        self.onLine = False
        self.drawModeButtons = [ ]
        self.lines = [ ]

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
        count = 1
        for line in db.splitlines():
            print count
            count+=1
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
        (left, up) = self.screenPos
        #Options screen:
        if self.mode == "options":
            pass





        #In main screen:
        #check all buttons
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
                if name != None: self.mode = name

        #toggles info
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
                        print "appended line"
                        self.onLine = True
                        return
                    else: #self.onLine = True
                        self.lines[-1].setEnd(star, self.screenPos)
                        self.onLine = False
                        return
                else: #clicked on point not a star
                    if self.onLine: 
                        self.lines.pop()
                        self.onLine = False
                        return


    def mouseReleased(self, x, y):
        pass

    def mouseMotion(self, x, y):
        if self.onLine:
            #shows line drawing in real time
            self.lines[-1].updateEndPoint(x, y)


    def mouseDrag(self, x, y):
        pass

    def keyPressed(self, keyCode, modifier):
        pass

    def keyReleased(self, keyCode, modifier):
        pass

    def timerFired(self, dt):
        self.inRealTime = True
        if self.inRealTime == True:
            self.date = datetime.datetime.now()
        else: #for testing
            newMinute = self.date.minute+1
            newHour = self.date.hour
            if self.date.minute+1 >= 60: 
                newMinute = (self.date.minute+1)%60
                newHour = self.date.hour+1
            self.date = self.date.replace(self.date.year, self.date.month, 
                                    self.date.day, newHour%24, newMinute)
        self.updatePgh()
        #self.calculateStars()

    def updatePgh(self):
        self.pgh.date = ephem.Date(self.date)
        # self.pgh.epoch = self.pgh.date

    def redrawAll(self, screen):
        if self.mode == "options":
            self.drawOptions(screen)
        else:
            self.drawStars(screen)
            self.drawButtons(screen)
            if self.mode == "draw":
                self.drawLines(screen)

    def drawOptions(self, screen):
        pass


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

        #print count
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



    def isKeyPressed(self, key):
        # return whether a specific key is being held 
        return self._keys.get(key, False)



Planetarium().run()