import pygame
import time
import os
import random
import math
import operator
from pygame.locals import *

ZOMBIE_PATH = os.path.join("data", "zombie")
FONT_PATH = os.path.join("data", "font")
ZOMBIE_SPAWN_IMG = os.path.join(ZOMBIE_PATH, "zombie_spawn.png")
ZOMBIE_IDLE_IMG = os.path.join(ZOMBIE_PATH, "zombie_idle.png")
ZOMBIE_DEATH_IMG = os.path.join(ZOMBIE_PATH, "zombie_death.png")
ZOMBIE_HIDE_IMG = os.path.join(ZOMBIE_PATH, "zombie_hide.png")
HIT_EFFECT_IMG = os.path.join("data", "hit_effect.png")
BACKGROUND_IMG = os.path.join("data", "background.png")
STAR_IMG = os.path.join("data", "star.png")
VCR_OSD_MONO_FONT = os.path.join(FONT_PATH, "VCR_OSD_MONO.ttf")
BONK_SFX = os.path.join("data", "bonk_sfx.mp3")
DEFAULT_SPAWN_TIME = 1
DEFAULT_ZOMBIE_ALIVE_TIME = 5
SPAWN_LOCATIONS = [(310, 120), (760, 120), (1210, 120),
                   (310, 390), (760, 390), (1210, 390),
                   (310, 660), (760, 660), (1210, 660)]
ZOMBIE_HIDDEN_EVENT = pygame.event.custom_type()
DEFAULT_COLLIDER_OFFSET = (10, 10)

class GameObject:
    def __init__(self, position):
        self.position = position
        self.children_objects = []

        self.should_be_destroyed = False
        pass

    def on_loop(self, frametime):
        for child in self.children_objects:
            if child.should_be_destroyed:
                child.on_destroy()
                self.children_objects.remove(child)
                continue

            child.on_loop(frametime)
        pass

    def on_render(self, display_surf):
        for child in self.children_objects:
            child.on_render(display_surf)
        pass

    def on_event(self, event):
        for child in self.children_objects:
            child.on_event(event)
        pass

    def on_destroy(self):
        for child in self.children_objects:
            child.on_destroy()

        self.should_be_destroyed = True
        pass

class AnimatedObject(GameObject):
    def __init__(self, position, img_path, framerate = 12, frame_num = 8):
        self._anim_frame = 0
        self._init_anim_timer = 1/framerate
        self._anim_timer = self._init_anim_timer
        self._frame_num = frame_num
        self._anim_rect = pygame.Rect(0, 0, 64, 64)

        self._sprite = pygame.image.load(img_path)
        super().__init__(position)
        pass

    def on_loop(self, frametime):
        if self._anim_frame >= self._frame_num:
            self.should_be_destroyed = True
            return

        if self._anim_timer >= 0:
            self._anim_timer = self._anim_timer - frametime
            return

        self._anim_frame = self._anim_frame + 1
        new_cords = 64 * self._anim_frame
        self._anim_rect = pygame.Rect(new_cords, 0, 64, 64)

        self._anim_timer = self._init_anim_timer
        super().on_loop(frametime)
        pass

    def on_render(self, display_surf):
        if self._anim_frame >= self._frame_num:
            return
        display_surf.blit(self._sprite, self.position, self._anim_rect)
        super().on_render(display_surf)
        pass

class HitParticles:
    def __init__(self, position, beam_num = 4, alive_time = 0.00833):
        self._position = position
        self._star_beam = random.randrange(0, 4)
        self._anim_frame = 0
        self._init_anim_timer = 0.020444
        self._anim_timer = self._init_anim_timer 
        self._beam_num = beam_num
        self._alive_timer = alive_time

        vel = (3, 3)
        #beam_deg_range = math.floor(90/self._beam_num)
        beams_deg = [random.randrange(-45, -23), random.randrange(-23, 0), random.randrange(180, 203), random.randrange(203, 225)]
        #for i in range(1, self._beam_num):
        #    start_deg = 45 * i
        #    beams_deg.append(random.randrange(start_deg, start_deg + beam_deg_range))


        self._beams_vel = []
        for i in range(self._beam_num):
            deg = beams_deg[i]
            base_vel = (math.cos(math.radians(deg)), -math.sin(math.radians(deg)))
            self._beams_vel.append(tuple(map(operator.mul, base_vel, vel)))

        self._beams = []
        for i in range(self._beam_num):
            self._beams.append(
                    [
                        self.get_init_pos(
                                self._beams_vel[i],
                                (self._position[0], self._position[0] + 64, self._position[1], self._position[1] + 64)
                        )
                    ]
            )

    def get_init_pos(self, vel, box):
        retval = (self._position[0] + 32, self._position[1] + 32)
        left, right, top, bot = box
        while True:
            retval = (retval[0] + vel[0], retval[1] + vel[1])
            #print(retval)

            if retval[0] < left or retval[0] > right or retval[1] < top or retval[1] > bot:
                break

        retval = (math.floor(retval[0]), math.floor(retval[1]))

        return retval

    def render_dot(self, display_surf, position, sz):
        mid_point = (position[0] + sz/2, position[1] + sz/2)

        for i in range(sz):
            for j in range(sz):
                point = (position[0] + i, position[1] + j)
                dist = math.sqrt(pow(point[0] - mid_point[0], 2) + pow(point[1] - mid_point[1], 2))

                if dist < sz:
                    display_surf.set_at(point, (255, 0, 0))

    def render_beam(self, display_surf, beam, sz):
        for dot in beam:
            sz = sz - sz/len(beam)
            dot_int = (round(dot[0]), round(dot[1]))
            self.render_dot(display_surf, dot_int, math.ceil(sz))

    def on_loop(self, frametime):
        if self._anim_timer > 0:
            self._anim_timer = self._anim_timer - frametime
            return

        if self._alive_timer <= 0:
            return

        acc = [0, 0.2]

        for i in range(self._beam_num):
            beam = self._beams[i]
            self._beams_vel[i] = (self._beams_vel[i][0] + acc[0], self._beams_vel[i][1] + acc[1])

            beam_last_pos = beam[self._anim_frame]
            beam_next_pos = (beam_last_pos[0] + self._beams_vel[i][0], beam_last_pos[1] + self._beams_vel[i][1])

            beam.append(beam_next_pos)

            if len(beam) >= 256:
                beam.pop(0)

        self._anim_frame = min(self._anim_frame + 1, 256)
        self._anim_timer = self._init_anim_timer
        self._alive_timer = self._alive_timer - frametime

    def on_render(self, display_surf):
        if self._anim_timer <= 0:
            return
        for beam in self._beams:
            self.render_beam(display_surf, beam, 4)

class Zombie(GameObject):
    def __init__(self, position, alive_time = 5):
        self.SPAWN = 0
        self.IDLE = 1
        self.DEATH = 2
        self.HIDE = 3

        self.SPAWN_SPRITE = pygame.image.load(ZOMBIE_SPAWN_IMG)
        self.IDLE_SPRITE = pygame.image.load(ZOMBIE_IDLE_IMG)
        self.DEATH_SPRITE = pygame.image.load(ZOMBIE_DEATH_IMG)
        self.HIDE_SPRITE = pygame.image.load(ZOMBIE_HIDE_IMG)

        self._alive_time = alive_time

        self._anim_frame = 0
        self._init_anim_timer = 0.0833 #12 fps
        self._anim_timer = self._init_anim_timer 
        self._sprite_rect = pygame.Rect(0, 0, 64, 64)

        self._is_bonkable = False
        self.collider_offset = DEFAULT_COLLIDER_OFFSET

        self.hit_particles = None

        self.status = self.SPAWN
        super().__init__(position)

    def _animate(self, frametime):
        self._anim_timer = self._anim_timer - frametime
        if self._anim_timer <= 0:
            new_cords = self._anim_frame * 64
            self._sprite_rect = pygame.Rect(new_cords, 0, 64, 64)
            self._anim_timer = self._init_anim_timer
            self._anim_frame = (self._anim_frame + 1) % 8

    def on_loop(self, frametime):
        self._animate(frametime)
        if (self.status == self.DEATH or self.status == self.HIDE) and self._anim_frame >= 7:
            self.on_destroy()
        elif self.status == self.SPAWN and self._anim_frame >= 7:
            self.status = self.IDLE
            self._is_bonkable = True

        self._alive_time = self._alive_time - frametime
        if self._alive_time <= 0:
            self.status = self.HIDE
            zombie_hidden_event = pygame.event.EVENT(ZOMBIE_HIDDEN_EVENT)
            pygame.event.post(zombie_hidden_event)

        if self.hit_particles:
            self.hit_particles.on_loop(frametime)

        super().on_loop(frametime)

    def on_render(self, display_surf):
        if self.status == self.SPAWN:
            display_surf.blit(self.SPAWN_SPRITE, self.position, self._sprite_rect)
        elif self.status == self.IDLE:
            display_surf.blit(self.IDLE_SPRITE, self.position, self._sprite_rect)
        elif self.status == self.HIDE:
            display_surf.blit(self.HIDE_SPRITE, self.position, self._sprite_rect)
        else:
            display_surf.blit(self.DEATH_SPRITE, self.position, self._sprite_rect)

        if self.hit_particles:
            self.hit_particles.on_render(display_surf)

        super().on_render(display_surf)

    def on_event(self, event):
        super().on_event(event)

    def die(self):
        if self._is_bonkable or self.status == self.DEATH:
            return

        self.status = self.DEATH
        self._anim_frame = 0
        self._is_bonkable = False

        self.hit_particles = HitParticles(self.position)
        self.children_objects.append(AnimatedObject(position = tuple(map(operator.add, self.position, (0, -22))), img_path = HIT_EFFECT_IMG, framerate = 6, frame_num = 2))
        sound = pygame.mixer.Sound(BONK_SFX)
        sound.play()
        has_been_hit = True

    def get_bonkable(self):
        return self._is_bonkable
 
class App():
    def __init__(self):
        self._display_surf = None
        self._alive_zombies = []

        self._free_spawn_locations = SPAWN_LOCATIONS
        self._occupied_spawn_locations = []

        self._background_sprite = pygame.image.load(BACKGROUND_IMG)
        self._font = None

        self._spawn_time = DEFAULT_SPAWN_TIME
        self._curr_spawn_timer = self._spawn_time
        self._frametime = 0

        self._streak = 0
        self._points = 0
        self._misses = 0
        self._hitrate = 0

        self.size = self.weight, self.height = 1584, 887

    def get_random_spawn_location(self):
        if(len(self._free_spawn_locations) == 0):
            return (0, 0)

        retval = self._free_spawn_locations[random.randrange(0, len(self._free_spawn_locations))]

        return retval

    def on_init(self):
        random.seed(time.time())
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()
        self._font = pygame.font.Font(VCR_OSD_MONO_FONT, 32)
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True
 
    def on_loop(self):
        for zombie in self._alive_zombies:
            zombie.on_loop(self._frametime)

            if zombie.should_be_destroyed:
                location = zombie.position
                self._free_spawn_locations.append(location)
                self._occupied_spawn_locations.remove(location)
                self._alive_zombies.remove(zombie)

                self._spawn_time = max(self._spawn_time - self._streak * 0.05, .05)

                if(self._points + self._misses != 0):
                    self._hitrate = self._points / (self._points + self._misses)
                else:
                    self._hitrate = 0

        self._curr_spawn_timer = self._curr_spawn_timer - self._frametime
        if self._curr_spawn_timer <= 0 and len(self._free_spawn_locations) > 0:
            spawn_location = self.get_random_spawn_location()
            self._occupied_spawn_locations.append(spawn_location)
            self._free_spawn_locations.remove(spawn_location)

            self._alive_zombies.append(Zombie(spawn_location, alive_time = max(DEFAULT_ZOMBIE_ALIVE_TIME - self._streak * 0.25, 0.25)))
            self._curr_spawn_timer = self._spawn_time

    def on_render(self):
        self._display_surf.blit(self._background_sprite, self._background_sprite.get_rect())
        for zombie in self._alive_zombies:
            zombie.on_render(self._display_surf)

        points_surf = self._font.render("POINTS: " + str(self._points), False, (0, 0, 0))
        misses_surf = self._font.render("MISSES: " + str(self._misses), False, (0, 0, 0))
        hitrate_surf = self._font.render("HIT RATE: " + str(self._hitrate), False, (0, 0, 0))

        self._display_surf.blit(points_surf, (10, 50))
        self._display_surf.blit(misses_surf, (10, 75))
        self._display_surf.blit(hitrate_surf, (10, 100))

        pygame.display.flip()

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

        if event.type == pygame.MOUSEBUTTONDOWN
            self.on_mouse_down(event)

        if event.type == ZOMBIE_HIDDEN_EVENT:
            self._streak = 0
            self._misses = self._misses + 1
            self._spawn_time = DEFAULT_SPAWN_TIME

        for zombie in self._alive_zombies:
            zombie.on_event(event)

    def on_mouse_down(self, event):
        has_hit = False
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for zombie in self._alive_zombies:
            min_width = zombie.position[0]
            max_width = zombie.position[0] + 64 + zombie.collider_offset[0]
            min_height = zombie.position[1]
            max_height = zombie.position[1] + 64 + zombie.collider_offset[1]

            if mouse_x >= min_width and mouse_x <= max_width and mouse_y >= min_height and mouse_y <= max_height and zombie.get_bonkable() and zombie.status == zombie.IDLE:
                has_hit = True
                zombie.die()
                break

        if has_hit:
            self._streak = self._streak + 1
            self._points = self._points + 1
        else:
            self._streak = 0
            self._misses = self._misses + 1
            self._spawn_time = DEFAULT_SPAWN_TIME

    def on_cleanup(self):
        pygame.font.quit()
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
