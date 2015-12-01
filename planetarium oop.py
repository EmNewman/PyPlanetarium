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
        self.r = 3

    def changeInfo(self):
        self.showInfo = not self.showInfo

    def calculate(self, ref, shift):
        self.body.compute(ref)
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
        self.zoom=10

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
            return name


class Planetarium(Framework):
    def __init__(self, width=600, height=400, fps=50, title="PGH Planetarium"):
        super(Planetarium, self).__init__()
        self.title = "PGH Planetarium"
        self.bgColor = self.BLACK
        self.shift = 200 #changes with zooming?
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

        self.showStarInfo = True
        self.inRealTime = False
        self.mode = "main"

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

    def calculateStars(self):
        for star in self.starList:
            star.calculate(self.pgh, self.shift)




    def init(self):
        pass

    def updateScreenPos(self, shift, x=0, y=0):
        (oldX, oldY) = self.screenPos
        if shift == 0:
            self.screenPos = (x+oldX, y+oldY)
        else:
            self.shift += shift
            self.screenPos = (oldX+shift, oldY+shift)


    def mousePressed(self, x, y):
        (left, up) = self.screenPos
        #In main screen:
        #check all buttons
        for button in self.buttons:
            if isinstance(button, ZoomButton):
                val = button.onClick(x,y)
                if self.shift+val < 0 or self.shift+val > 1000: continue
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

        #toggles info
        for star in self.starList:
            if star.displayPos(left,up) == None: continue
            (cx, cy) = star.displayPos(left,up)
            (width, height) = self.font.size(star.name)
            if (pointInCircle((x,y), (cx, cy), star.r)
                or pointInBox((x,y), (cx, cy, cx+width, cy+height))):
                star.changeInfo()
                return #ensures only one star info shown

    def mouseReleased(self, x, y):
        pass

    def mouseMotion(self, x, y):
        pass

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
        self.drawStars(screen)
        self.drawButtons(screen)

    def drawButtons(self, screen):
        for button in self.buttons:
            if isinstance(button, ModeButton):
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



    def isKeyPressed(self, key):
        # return whether a specific key is being held 
        return self._keys.get(key, False)



Planetarium().run()