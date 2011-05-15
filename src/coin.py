import pymunk
import pygame

from settings import *


class Coin(object):

    def __init__(self, position):
        self.position = position
        self.picked_up = False
        self._init_pymunk()

    def _init_pymunk(self):
        self.body = pymunk.Body(pymunk.inf, pymunk.inf)
        self.body.position = self.position
        self.shape = pymunk.Circle(self.body, 8)
        self.shape.collision_type = COLLTYPE_COIN
        
    def __getstate__(self):
        return {'position' : (self.position[0], self.position[1])}
    
    def __setstate__(self, state):
        self.position = state['position']
        self.picked_up = False
        self._init_pymunk()
        
    def draw(self, screen, game):
        if not self.picked_up:
            pygame.draw.circle(screen, (192,192,10), game.world2screen(self.body.position), 8)

        