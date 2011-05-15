import random
import math

import pymunk
import pygame
from pygame.locals import *

from settings import *


class Particle(object):

    def __init__(self, position, velocity, ttl=15):
        self.ttl = ttl
        self.body = pymunk.Body(1, 1)
        self.body.position = position
        self.body.velocity = velocity
        self.shape = pymunk.Circle(self.body, 1)
        self.shape.collision_type = COLLTYPE_PARTICLE
        
    def draw(self, screen, game):
        pygame.draw.circle(screen, (50,50,255), game.world2screen(self.body.position), 1)
                

class Emitter(object):
    
    def __init__(self, position, period):
        self.position = (position[0], position[1])
        self.period = period
        self.counter = 0
        
    def update(self, game, dt):
        self.counter += dt
        if self.counter > self.period:
            self.counter -= self.period
            pp = self.position
            pv = pymunk.Vec2d(0, 1)
            pv.length = 100
            pv.angle = random.random() * math.pi * 2
            p = Particle(pp, pv)
            game.particles.append(p)
            game.shape_map[p.shape] = p
            game.space.add(p.body, p.shape)
    
    def draw(self, screen, game):
        pygame.draw.circle(screen, (0,0,255), game.world2screen(self.position), 8, 2)
        