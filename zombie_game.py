import pygame
import time
import os
import random
from pygame.locals import *

ZOMBIE_PATH = os.path.join('data', 'zombie')
ZOMBIE_SPAWN_IMG = os.path.join(ZOMBIE_PATH, 'zombie_spawn.png')
ZOMBIE_IDLE_IMG = os.path.join(ZOMBIE_PATH, 'zombie_idle.png')
ZOMBIE_DEATH_IMG = os.path.join(ZOMBIE_PATH, 'zombie_death.png')
BACKGROUND_IMG = os.path.join('data', 'background.png')
SPAWN_TIME = 1
SPAWN_LOCATIONS = [(320, 120), (300, 500)]

class Zombie:
    def __init__(self, position):
        self.SPAWN = 0
        self.IDLE = 1
        self.DEATH = 2

        self.SPAWN_SPRITE = pygame.image.load(ZOMBIE_SPAWN_IMG)
        self.IDLE_SPRITE = pygame.image.load(ZOMBIE_IDLE_IMG)
        self.DEATH_SPRITE = pygame.image.load(ZOMBIE_DEATH_IMG)

        self._position = position
        self._alive_time = 1

        self._anim_frame = 0
        self._anim_timer = 0.5 #2 fps
        self._sprite_rect = pygame.Rect(0, 0, 64, 64)

        self._status = self.SPAWN

        self.should_be_destroyed = False
        self.box_collider = (10, 10)
        pass

    def _animate(self, frametime):
        self._anim_timer = self._anim_timer - frametime
        if self._anim_timer <= 0:
            new_cords = self._anim_frame * 64
            self._sprite_rect = pygame.Rect(new_cords, 0, 64, 64)
            self._anim_timer = 0.5
            self._anim_frame = (self._anim_frame + 1) % 8

    def on_loop(self, frametime):
        self._animate(frametime)
        if self._status == self.DEATH and self._anim_frame >= 7:
            self.should_be_destroyed = True
        elif self._status == self.SPAWN and self._anim_frame >= 7:
            self._status = self.IDLE

        self._alive_time = self._alive_time - frametime

    def on_render(self, display_surf):
        if self._status == self.SPAWN:
            display_surf.blit(self.SPAWN_SPRITE, self._position, self._sprite_rect)
        elif self._status == self.IDLE:
            display_surf.blit(self.IDLE_SPRITE, self._position, self._sprite_rect)
        else:
            display_surf.blit(self.DEATH_SPRITE, self._position, self._sprite_rect)

    def on_event(self, event):
        pass
 
class App():
    def __init__(self):
        self._display_surf = None
        self._alive_zombies = []

        self._free_spawn_locations = SPAWN_LOCATIONS
        self._occupied_spawn_locations = []

        self._background_sprite = pygame.image.load(BACKGROUND_IMG)

        self._spawn_timer = SPAWN_TIME
        self._frametime = 0
        random.seed(time.time())

        self.size = self.weight, self.height = 1584, 887

    def create_spawn_locations(self):
        retval = []
        for i in range(3):
            for j in range(3):
                retval.append((300 + i * 256, 100 + j * 256))
        return retval

    def get_random_spawn_location(self):
        if(len(self._free_spawn_locations) == 0):
            return (-1)

        retval = self._free_spawn_locations[random.randrange(0, len(self._free_spawn_locations))]

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
        if self._spawn_timer <= 0 and len(self._free_spawn_locations) > 0:
            spawn_location = self.get_random_spawn_location()
            self._occupied_spawn_locations.append(spawn_location)
            self._free_spawn_locations.remove(spawn_location)

            self._alive_zombies.append(Zombie(spawn_location))

    def on_render(self):
        self._display_surf.blit(self._background_sprite, self._background_sprite.get_rect())
        for zombie in self._alive_zombies:
            zombie.on_render(self._display_surf)
        pygame.display.flip()

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

        for zombie in self._alive_zombies:
            zombie.on_event(event)

    def on_cleanup(self):
        pygame.quit()
 
    def on_execute(self):
        if self.on_init() == False:
            self._running = False
 
        while( self._running ):
            #print(len(self._free_spawn_locations))
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
