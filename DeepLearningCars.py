import timeit
from game import Game, AutoSimulation
import pygame

pygame.init()


def main():
    g = Game()
    g.world.generation += 1
    while g.running:
        g.play()


main()
