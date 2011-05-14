import pygame
from state import *
from settings import *
from game import game

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH,HEIGHT),0,32)
    clock = pygame.time.Clock()

    g = game()

    state=0
    while 1:
        if state == 0:
            state = attract(screen,clock)
        if state == 1:
            state = g.tick(screen,clock)
        if state == 2:
            state = pause(screen,clock)
        if state == 3:
            state = game_over(screen,clock)
        if state == 4:
            exit()


if __name__ == '__main__': main()
