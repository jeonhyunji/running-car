import os
import pygame
import math
from math import sin, radians, degrees, copysign
from pygame.math import Vector2

SCREEN_WIDTH = 1000
SCRENN_HEIGHT = 800

IMAGE_PATH = "resources/images/greencar.png"
TRACK_IMAGE_PATH = "resources/images/track.png"
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN= (0, 255, 0)
RED  = (255, 0, 0)
YELLOW = (255, 255, 0)

CAR_WIDTH = 60
CAR_HEIGHT = 30

class Car:
    # length is car length
    # max_steering is 30 degree 
    # max_acceleration is 5 meters per second
    def __init__(self, x, y, angle=0.0, length=4, max_steering=100, max_acceleration=5.0):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0.0, 0.0)
        self.angle = angle
        self.length = length
        self.max_acceleration = max_acceleration
        self.max_steering = max_steering
        self.max_velocity = 20
        self.brake_deceleration = 10
        self.free_deceleration = 2

        self.acceleration = 0.0
        self.steering = 0.0

    def update(self, dt):
        self.velocity += (self.acceleration * dt, 0)
        self.velocity.x = max(-self.max_velocity, min(self.velocity.x, self.max_velocity))

        if self.steering:
            turning_radius = self.length / sin(radians(self.steering))
            angular_velocity = self.velocity.x / turning_radius
        else:
            angular_velocity = 0

        self.position += self.velocity.rotate(-self.angle) * dt
        self.angle += degrees(angular_velocity) * dt

# car, track image load
track_image = pygame.image.load(TRACK_IMAGE_PATH)
car_image = pygame.image.load(IMAGE_PATH)

# create a mask for each of them.
track_mask = pygame.mask.from_surface(track_image, 50)
car_mask = pygame.mask.from_surface(car_image, 50)

# this is where the car, track are.
track_rect = track_image.get_rect()
car_rect = car_image.get_rect()

mask = pygame.mask.from_surface(track_image)
mask_fx = pygame.mask.from_surface(pygame.transform.flip(track_image, True, False))
mask_fy = pygame.mask.from_surface(pygame.transform.flip(track_image, False, True))
mask_fx_fy = pygame.mask.from_surface(pygame.transform.flip(track_image, True, True))
flipped_masks = [[mask, mask_fy], [mask_fx, mask_fx_fy]]

beam_surface = pygame.Surface((250, 250), pygame.SRCALPHA)

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Car tutorial")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCRENN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.ticks = 60
        self.exit = False
        self.alive = True

    def run(self):
        # car_image = pygame.image.load(IMAGE_PATH)
        # car = Car(10, 10)
        car = Car(4, 8)
        ppu = 32

        while not self.exit:
            dt = self.clock.get_time() / 1000

            # Event queue
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("pygame quit")
                    pygame.quit()
            
            if (self.alive):
                # User input
                pressed = pygame.key.get_pressed()

                # calculate car acceleration
                if pressed[pygame.K_UP]:
                    if car.velocity.x < 0:
                        car.acceleration = car.brake_deceleration
                    else:
                        car.acceleration += 1 * dt
                elif pressed[pygame.K_DOWN]:
                    if car.velocity.x > 0:
                        car.acceleration = -car.brake_deceleration
                    else:
                        car.acceleration -= 1 * dt
                elif pressed[pygame.K_SPACE]:
                    if abs(car.velocity.x) > dt * car.brake_deceleration:
                        car.acceleration = -copysign(car.brake_deceleration, car.velocity.x)
                    else:
                        car.acceleration = -car.velocity.x / dt
                else:
                    if abs(car.velocity.x) > dt * car.free_deceleration:
                        car.acceleration = -copysign(car.free_deceleration, car.velocity.x)
                    else:
                        if dt != 0:
                            car.acceleration = -car.velocity.x / dt
                car.acceleration = max(-car.max_acceleration, min(car.acceleration, car.max_acceleration))

                # calculate car steering
                if pressed[pygame.K_RIGHT]:
                    # car.steering -= 30 * dt
                    car.steering -= 100 * dt
                elif pressed[pygame.K_LEFT]:
                    car.steering += 100 * dt
                else:
                    car.steering = 0
                car.steering = max(-car.max_steering, min(car.steering, car.max_steering))

                # update car position & angle
                car.update(dt)

            # get new position from rotated rectangular object
            rotated = pygame.transform.rotate(car_image, car.angle)
            rect = rotated.get_rect()
            carNewPosition = car.position * ppu - (rect.width / 2, rect.height / 2)

            # reset screen
            self.screen.fill(WHITE)

            # draw
            # for angle in range(0, 359, 30):
            for angle in range(-45, 135, 45):
                self.draw_beam(angle, carNewPosition)

            # check crash, if crash draw yellow rectangular ! and don't move!
            isCrash = self.checkCrash(carNewPosition)
            if (isCrash):
                self.alive = False
                self.drawCrash(rotated, carNewPosition)

            # print car infomation
            self.printText("car position: " + str(car.position), 10, 10)
            self.printText("car new position: " + str(carNewPosition), 10, 40)
            self.printText("acceleration: " + str(car.acceleration), 10, 70)
            self.printText("velocity: " + str(car.velocity), 10, 100)
            self.printText("rotate rect: " + str(rect), 10, 130)

            # drawing car new position
            self.screen.blit(rotated, carNewPosition)
            self.screen.blit(track_image, (0,0))
            pygame.display.flip()
            self.clock.tick(self.ticks)

    def checkCrash(self, position):
        offset_x = position.x - track_rect[0]
        offset_y = position.y - track_rect[1]
        overlap = track_mask.overlap(car_mask, (int(offset_x), int(offset_y)))
        if (overlap):
            return True
        else:
            return False

    def drawCrash(self, rotated, position):
        self.printText("crash!!", 20, 20)
        rotatedRect = self.screen.blit(rotated, position)
        pygame.draw.rect(self.screen, YELLOW, rotatedRect, 2)

    def draw_beam(self, angle, pos):
        c = math.cos(math.radians(angle))
        s = math.sin(math.radians(angle))

        flip_x = c < 0
        flip_y = s < 0
        filpped_mask = flipped_masks[flip_x][flip_y]

        # compute beam final point
        x_dest = 500 * abs(c)
        y_dest = 500 * abs(s)

        beam_surface.fill((0, 0, 0, 0))

        # draw a single beam to the beam surface based on computed final point
        pygame.draw.line(beam_surface, BLUE, (0, 0), (x_dest, y_dest))
        beam_mask = pygame.mask.from_surface(beam_surface)

        # find overlap between "global mask" and current beam mask
        offset_x = 499-pos[0] if flip_x else pos[0]
        offset_y = 499-pos[1] if flip_y else pos[1]
        hit = filpped_mask.overlap(beam_mask, (int(offset_x), int(offset_y)))
        if hit is not None and (hit[0] != pos[0] or hit[1] != pos[1]):
            hx = 499 - hit[0] if flip_x else hit[0]
            hy = 499 - hit[1] if flip_y else hit[1]
            hit_pos = (hx, hy)

            pygame.draw.line(self.screen, BLUE, pos, hit_pos)
            pygame.draw.circle(self.screen, GREEN, hit_pos, 3)

    def printText(self, text, x, y):
        # font loading, text size: 15
        fontObj = pygame.font.Font('resources/NanumSquareOTF_acB.otf', 15)
        printTextObj = fontObj.render(text, True, WHITE)   
        printTextRect = printTextObj.get_rect();                     
        printTextRect.topleft = (x, y)                               
        self.screen.blit(printTextObj, printTextRect)    


if __name__ == '__main__':
    game = Game()
    game.run()