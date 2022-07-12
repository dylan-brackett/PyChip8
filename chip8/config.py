import pygame

STACK_SIZE = 16
MEMORY_SIZE = 4096
NUM_REGISTERS = 16
START_ADDR = 0x200
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32

# Time in milliseconds between each instruction
CLOCK_SPEED = round((1 / 500) * 1000)
# Time in milliseconds between each timer update
TIMER_SPEED = round((1 / 60) * 1000)

FONT_ADDR_START = 0x0

KEY_MAPPINGS = {
    0x1: pygame.K_1,
    0x2: pygame.K_2,
    0x3: pygame.K_3,
    0xC: pygame.K_4,
    0x4: pygame.K_q,
    0x5: pygame.K_w,
    0x6: pygame.K_e,
    0xD: pygame.K_r,
    0x7: pygame.K_a,
    0x8: pygame.K_s,
    0x9: pygame.K_d,
    0xE: pygame.K_f,
    0xA: pygame.K_z,
    0x0: pygame.K_x,
    0xB: pygame.K_c,
    0xF: pygame.K_v
}

DEBUG = False
