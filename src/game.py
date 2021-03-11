import pygame
import car
import math
from pygame import Vector2

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN= (0, 255, 0)
RED  = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (169, 169, 169)

BACKGROUND_COLOR = GRAY
TEXT_COLOR = WHITE

IMAGE_PATH = "../resources/images/car_green.png"
TRACK_IMAGE_PATH = "../resources/images/track2.png"
FONT_PATH = "../resources/fonts/NanumSquareOTF_acB.otf"

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800

PPU = 32 # pixel per unit

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Running Car")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.ticks = 60
        self.exit = False
        self.alive = True
        self.status = "RUNNING"

        # car, track image load
        self.track_image = pygame.image.load(TRACK_IMAGE_PATH)
        self.car_image = pygame.image.load(IMAGE_PATH)

        # create car
        self.car = car.Car(4, 8)

        # create a mask for each of them.
        self.track_mask = pygame.mask.from_surface(self.track_image, 50)
        self.car_mask = pygame.mask.from_surface(self.car_image, 50)

        mask = pygame.mask.from_surface(self.track_image)
        mask_fx = pygame.mask.from_surface(pygame.transform.flip(self.track_image, True, False))
        mask_fy = pygame.mask.from_surface(pygame.transform.flip(self.track_image, False, True))
        mask_fx_fy = pygame.mask.from_surface(pygame.transform.flip(self.track_image, True, True))
        self.flipped_masks = [[mask, mask_fy], [mask_fx, mask_fx_fy]]

        self.beam_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    def run(self):
        while not self.exit:
            dt = self.clock.get_time() / 1000

            # Event queue
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("pygame quit")
                    self.exit = True
                elif event.type == pygame.KEYDOWN:
                    pressed = pygame.key.get_pressed()
                    if pressed[pygame.K_TAB]:
                        self.__init__()

            if (self.alive):
                # User input
                pressed = pygame.key.get_pressed()

                # calculate car acceleration
                if pressed[pygame.K_UP]:
                    if self.car.velocity.x < 0:
                        self.car.acceleration = self.car.brake_deceleration
                    else:
                        self.car.acceleration += 1 * dt
                elif pressed[pygame.K_DOWN]:
                    if self.car.velocity.x > 0:
                        self.car.acceleration = -self.car.brake_deceleration
                    else:
                        self.car.acceleration -= 1 * dt
                elif pressed[pygame.K_SPACE]:
                    if abs(self.car.velocity.x) > dt * self.car.brake_deceleration:
                        self.car.acceleration = -math.copysign(self.car.brake_deceleration, self.car.velocity.x)
                    else:
                        self.car.acceleration = -self.car.velocity.x / dt
                else:
                    if abs(self.car.velocity.x) > dt * self.car.free_deceleration:
                        self.car.acceleration = -math.copysign(self.car.free_deceleration, self.car.velocity.x)
                    else:
                        if dt != 0:
                            self.car.acceleration = -self.car.velocity.x / dt
                self.car.acceleration = max(-self.car.max_acceleration, min(self.car.acceleration, self.car.max_acceleration))

                # calculate car steering
                if pressed[pygame.K_RIGHT]:
                    # car.steering -= 30 * dt
                    self.car.steering -= 100 * dt
                elif pressed[pygame.K_LEFT]:
                    self.car.steering += 100 * dt
                else:
                    self.car.steering = 0
                self.car.steering = max(-self.car.max_steering, min(self.car.steering, self.car.max_steering))

                # update car position & angle
                self.car.update(dt)

            # get new position from rotated rectangular object
            rotated = pygame.transform.rotate(self.car_image, self.car.angle)
            rect = rotated.get_rect()
            carNewPosition = self.car.position * PPU - (rect.width / 2, rect.height / 2)

            # reset screen
            self.screen.fill(BACKGROUND_COLOR)

            # drawing car new position
            rotatedRect = self.screen.blit(rotated, carNewPosition)
            self.screen.blit(self.track_image, (0,0))

            # draw beam
            # for angle in range(-90, 91, 30):
            #     self.draw_beam(angle, rotatedRect.center)
            beam_angle_arr = [-90, -45, 0, 45, 90]
            beam_length_arr = []
            for angle in beam_angle_arr:
                beam_angle = angle - self.car.angle
                beam_length = self.draw_beam(beam_angle, rotatedRect.center)
                beam_length_arr.append(beam_length)
            
            # print beam length arr
            self.print_beam_length(beam_length_arr)

            # check crash, if crash draw yellow rectangular ! and don't move!
            isCrash = self.check_crash(carNewPosition)
            if (isCrash):
                self.alive = False
                self.status = "CRASH"
                self.draw_crash(rotatedRect, carNewPosition)

            # print car infomation
            self.print_text("acceleration: " + str(self.car.acceleration), 10, 10, TEXT_COLOR)
            self.print_text("velocity: " + str(self.car.velocity), 10, 40, TEXT_COLOR)
            self.print_text(self.status, 800, 10, YELLOW)

            pygame.display.flip()
            self.clock.tick(self.ticks)

        pygame.quit()

    def check_crash(self, position):
        track_rect = self.track_image.get_rect()
        offset_x = position.x - track_rect[0]
        offset_y = position.y - track_rect[1]
        overlap = self.track_mask.overlap(self.car_mask, (int(offset_x), int(offset_y)))
        if (overlap):
            return True
        else:
            return False

    def draw_crash(self, rotatedRect, position):
        self.print_text("crash!!", position.x, (position.y-20), TEXT_COLOR)
        pygame.draw.rect(self.screen, YELLOW, rotatedRect, 2)

    def draw_beam(self, angle, pos):
        c = math.cos(math.radians(angle))
        s = math.sin(math.radians(angle))

        flip_x = c < 0
        flip_y = s < 0
        filpped_mask = self.flipped_masks[flip_x][flip_y]

        # compute beam final point
        x_dest = SCREEN_WIDTH * abs(c)
        y_dest = SCREEN_HEIGHT * abs(s)

        self.beam_surface.fill((0, 0, 0, 0))

        # draw a single beam to the beam surface based on computed final point
        pygame.draw.line(self.beam_surface, BLUE, (0, 0), (x_dest, y_dest))
        beam_mask = pygame.mask.from_surface(self.beam_surface)

        # find overlap between "global mask" and current beam mask
        offset_x = (SCREEN_WIDTH-1)-pos[0] if flip_x else pos[0]
        offset_y = (SCREEN_HEIGHT-1)-pos[1] if flip_y else pos[1]
        hit = filpped_mask.overlap(beam_mask, (int(offset_x), int(offset_y)))
        if hit is not None and (hit[0] != pos[0] or hit[1] != pos[1]):
            hx = (SCREEN_WIDTH-1) - hit[0] if flip_x else hit[0]
            hy = (SCREEN_HEIGHT-1) - hit[1] if flip_y else hit[1]
            hit_pos = (hx, hy)

            pygame.draw.line(self.screen, BLUE, pos, hit_pos)
            pygame.draw.circle(self.screen, GREEN, hit_pos, 5)

            distance = self.distance(pos, hit_pos)
            return distance
        
    def print_beam_length(self, beam_length_arr):
        # print beam length arr
        length_arr_text = "[ "
        for idx, val in enumerate(beam_length_arr):
            if (idx == 0):
                length_arr_text += str(int(val))
            else:
                length_arr_text += ", "
                length_arr_text += str(int(val))
        length_arr_text += " ]"
        self.print_text("beam length arr: " + str(length_arr_text), 10, 70, TEXT_COLOR)

    def distance(self, pos1, pos2):
        result = math.sqrt( math.pow(pos1[0] - pos2[0], 2) + math.pow(pos1[1] - pos2[1], 2) )
        return result

    def print_text(self, text, x, y, textColor):
        # font loading, text size: 15
        fontObj = pygame.font.Font(FONT_PATH, 15)
        printTextObj = fontObj.render(text, True, textColor)   
        printTextRect = printTextObj.get_rect();                     
        printTextRect.topleft = (x, y)                               
        self.screen.blit(printTextObj, printTextRect)    
