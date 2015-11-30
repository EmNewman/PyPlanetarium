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

class Star(object):
    def __init__(self, name, body):
        self.name = name
        self.body = body #type == ephem.Body
        self.screenPos = None
        self.showInfo = False
        self.r = 2

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


class Planetarium(Framework):
    def __init__(self, width=600, height=400, fps=50, title="PGH Planetarium"):
        super(Planetarium, self).__init__()
        self.title = "PGH Planetarium"
        self.bgColor = self.BLACK
        self.shift = 400 #changes with zooming?
        #full screen width and height
        self.fullWidth = self.shift*2
        self.fullHeight = self.shift*2
        self.log = dict() #stores all stars based on computed values WRT PGH
        self.pos = dict() #stores all screen positions of stars
        (self.MIN_ALT, self.MAX_ALT) = (0, math.pi/2)
        (self.MIN_AZ, self.MAX_AZ) = (0, 2*math.pi) #radians
        # upper left corner of screen in terms of sky
        # starts w/ center of screen being (0,0) of sky
        self.screenPos = (self.shift-self.width//2, self.shift-self.height//2)
        self.date = datetime.datetime.now() #always Datetime form
        self.starList = [ ]
        self.initPittsburgh()
        self.initStars()
        # self.calculateStars()
        self.showStarInfo = True
        

        self.inRealTime = False

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
        # for star in ephem.stars.db.split("\n"):
        #     starName = star.split(",")[0]
        #     if starName == "": continue #not a star
        #     self.log[starName] = ephem.star(starName)
        #     self.log[starName].compute(self.pgh)
        #     if self.log[starName].alt < 0: #below horizon
        #         self.pos[starName] = None
        #         continue
        #     phi = self.log[starName].alt + math.pi/2
        #     theta = 2*math.pi - self.log[starName].az
        #     #convert from spherical to cartesian xy coordinates
        #     #constant sphere radius
        #     x = math.sin(phi)*math.cos(theta)
        #     y = math.sin(phi)*math.sin(theta)
        #     #convert to draw-able coordinates
        #     #stores them based on "big" screen, not "current" screen
        #     self.pos[starName] = (self.shift * (x + 1), self.shift * (-y + 1))

        for star in self.starList:
            star.calculate(self.shift)




    def init(self):
        pass



    def mousePressed(self, x, y):
        (left, up) = self.screenPos
        for star in self.starList:
            if star.displayPos(left,up) == None: continue
            if self.pointInCircle((x,y), star.displayPos(left,up), star.r):
                star.changeInfo()


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

    def drawStars(self, screen):
        #count = 0
        # for star in self.pos:
        #     if self.pos[star] != None: #star is above horizon
        #         (x, y) = self.pos[star] 
        #         #convert "big screen" coords to "current screen" coords
        #         (screenLeft, screenUp) = self.screenPos
        #         x = int(x - screenLeft)
        #         y = int(y - screenUp)
        #         if self.pointInBox(x, y, (0, 0, self.width, self.height)):
        #             point = (x, y)
        #             pygame.draw.circle(screen, self.WHITE, point, self.starR)
        #             label = self.font.render(star, 1, self.GREEN)
        #             screen.blit(label, (x, y))
        #             if self.showInfo[star] == True:
        #                 self.drawStarInfo(star, screen, x, y)
        for star in self.starList:
            star.calculate(self.pgh, self.shift)
            (left, up) = self.screenPos
            pos = star.displayPos(left, up)
            if pos != None:
                if self.pointInBox(pos, (0,0,self.width,self.height)):
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


    @staticmethod
    def pointInBox(point, boxCoords): #from my hw8a.py
        (x, y) = point
        (boxLeft, boxTop, boxRight, boxBot) = boxCoords
        return boxLeft<=x<=boxRight and boxTop<=y<=boxBot 

    @staticmethod
    def pointInCircle(point, circlePos, r):
        (x, y) = point
        (cx, cy) = circlePos
        return (x-cx)**2 + (y-cy)**2 <= r**2

Planetarium().run()