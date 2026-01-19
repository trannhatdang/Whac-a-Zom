import pygame
import time
import os
import random
import cevent
from pygame.locals import *

ZOMBIE_IDLE_IMG = os.path.join('data', 'zombie', 'zombie_idle.png')
ZOMBIE_DEATH_IMG = os.path.join('data', 'zombie', 'zombie_death.png')
BACKGROUND_IMG = os.path.join('data', 'background.png')
SPAWN_TIME = 1
SPAWN_LOCATIONS = [(100, 100), (100, 50)]

'''
class SpawnLocation:
    def __init__(self, position):
        self._position = position
        self.is_occupied = False
'''

class Zombie:
    def __init__(self, position):
        self._position = position
        self._alive_time = 1

        self.IDLE = 0
        self.DEATH = 1

        self.IDLE_SPRITE = ZOMBIE_IDLE_IMG
        self.DEATH_SPRITE = ZOMBIE_DEATH_IMG

        self.anim_frame = 0
        self.sprite = self._animate()
        self.sprite_rect = pygame.Rect(0, 0, 256, 256)

        self.status = self.IDLE
        self.should_be_destroyed = False
        self.box_collider = (10, 10)
        pass

    def on_loop(self, frametime):
        self._animate()
        if self.status == self.DEATH and self.anim_frame >= 8:
            self.should_be_destroyed = True
        else:
            self.anim_frame = (self.anim_frame + 1) % 8

    def _animate():
        new_cords = self.anim_frame * 256
        self.sprite_rect = pygame.Rect(256 + self.anim_frame, 256 + self.anim_frame, 256, 256)
        pass
 
class App(cevent.CEvent):
    def __init__(self):
        self._display_surf = None
        self._alive_zombies = []

        self._free_spawn_locations = self.create_spawn_locations()
        self._occupied_spawn_locations = []

        self._spawn_timer = SPAWN_TIME
        self._frametime = 0
        random.seed(time.time())

        self.size = self.weight, self.height = 1280, 720

    def create_spawn_locations(self):
        retval = []
        for i in range(3):
            for j in range(3):
                retval.append((300 + i * 100, 100 + j * 100))
        
        return retval

    def get_random_spawn_location(self):
        retval = self._spawn_locations[random.randrange(0, len(self._spawn_locations))]

        return retval

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True
 
    def on_loop(self):
        for zombie in self._alive_zombies:
            zombie.on_loop(self._frametime)

            if zombie.should_be_destroyed:
                location = zombie.position
                self._free_spawn_location.remove(location)
                self._occupied_spawn_location.append(location)
                self._alive_zombies.remove(zombie)

        self._spawn_timer = self._spawn_timer - self._frametime
        if self._spawn_timer <= 0:
            spawn_location = self.get_random_spawn_location()
            self._occupied_spawn_locations.append(spawn_location)
            self._free_spawn_locations.remove(spawn_location)

            self._alive_zombies.append(Zombie(spawn_location))

    def on_render(self):
        for zombie in self._alive_zombies:
            self._display_surf.blit(zombie.SPRITE, zombie.position)

    def on_cleanup(self):
        pygame.quit()
 
    def on_execute(self):
        if self.on_init() == False:
            self._running = False
 
        while( self._running ):
            start_time = time.time()

            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()

            self._frametime = time.time() - start_time
        self.on_cleanup()
 
if __name__ == "__main__" :
    game = App()
    game.on_execute()
