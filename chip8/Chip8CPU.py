"""
Chip8 emulator written in Python

author: dylan-brackett

TODO: Add sound
TODO: Add more unit tests
TODO: Further refactor the code
TODO: Add Super Chip-8 features
"""

import random
import sys

import pygame

from .Chip8Debugger import Chip8Debugger
from .Chip8Display import Chip8Display
from .config import (CLOCK_SPEED, DEBUG, DISPLAY_HEIGHT, DISPLAY_WIDTH,
                     FONT_ADDR_START, FONT_SET, KEY_MAPPINGS, MEMORY_SIZE,
                     NUM_REGISTERS, STACK_SIZE, START_ADDR, TIMER_SPEED)


class InvalidLookup(Exception):
    """
    Exception raised when an invalid lookup is attempted.
    """
    pass

class DataTooLarge(Exception):
    """
    Exception raised when a ROM is too large.
    """
    pass

# CPU class
class Chip8CPU:
    def __init__(self):
        
        ###########################
        # CONSTANTS
        ###########################
        
        self.STACK_SIZE = STACK_SIZE
        self.MEMORY_SIZE = MEMORY_SIZE
        self.NUM_REGISTERS = NUM_REGISTERS
        self.START_ADDR = START_ADDR
        self.DISPLAY_WIDTH = DISPLAY_WIDTH
        self.DISPLAY_HEIGHT = DISPLAY_HEIGHT
        
        self.CLOCK_SPEED = CLOCK_SPEED
        self.TIMER_SPEED = TIMER_SPEED
        
        
        self.FONT_ADDR_START = FONT_ADDR_START
        self.FONT_SET = FONT_SET
        
        self.KEY_MAPPINGS = KEY_MAPPINGS
        
        self.DEBUG = DEBUG

        ###########################
        # VARIABLES
        ###########################
        
        if self.DEBUG:
            self.debugger = Chip8Debugger(self)
        
        pygame.init()
        
        self.memory = [0] * self.MEMORY_SIZE
        
        self.registers =  {
            "v" : [0] * self.NUM_REGISTERS, # General purpose registers
            "i" : 0x0000,                   # 2 byte address register
            "sp": 0x00,                     # Stack pointer
            "pc": self.START_ADDR,          # Program counter
        }
        
        self.stack = [0] * self.STACK_SIZE

        self.timers = {
            "delay": 0x00,
            "sound": 0x00,  
        }
        
        self.clock_ticks = 0
        
        self.timer_ticks = 0
        
        self.display = None

        self.load_fontset()

        ###########################
        # OPCODE LOOKUP TABLES
        ###########################
        
        """
        Not all opcodes can be identified by the first nibble.
        So some opcodes are sent to another function to handle looking up the correct opcode.
        """
        
        self.opcode_first_nibble_lookup = {
            0x0: self.lookup_opcode_0x0,
            0x1: self.jump_addr,
            0x2: self.call_addr,
            0x3: self.skip_reg_eq_byte,
            0x4: self.skip_reg_neq_byte,
            0x5: self.skip_reg_eq_reg,
            0x6: self.ld_to_reg,
            0x7: self.add_byte_to_reg,
            0x8: self.lookup_opcode_0x8,
            0x9: self.skip_reg_neq_reg,
            0xA: self.ld_i,
            0xB: self.jump_addr,
            0xC: self.store_rnd_anded_byte_to_reg,
            0xD: self.draw_bytes,
            0xE: self.lookup_opcode_0xE,
            0xF: self.lookup_opcode_0xF,
        }
        
        self.opcode_0x0_last_byte_lookup = {
            0xE0: self.clear_screen,
            0xEE: self.return_from_subrtn,
        }
        
        self.opcode_0x8_fourth_nibble_lookup = {
            0x0: self.ld_reg_to_reg,
            0x1: self.or_regs,
            0x2: self.and_regs,
            0x3: self.xor_regs,
            0x4: self.add_regs,
            0x5: self.sub_regs,
            0x6: self.right_shift_reg,
            0x7: self.reverse_sub_regs,
            0xE: self.left_shift_reg
        }
        
        self.opcode_0xE_last_byte_lookup = {
            0x9E: self.skip_on_keypress,
            0xA1: self.skip_on_not_keypress
        }
        
        self.opcode_0xF_last_byte_lookup = {
            0x07: self.ld_reg_with_dly_timer,
            0x0A: self.wait_for_input,
            0x15: self.ld_delay_timer_with_reg,
            0x18: self.ld_sound_timer_with_reg,
            0x1E: self.add_i_with_reg,
            0x29: self.ld_i_font_sprite,
            0x33: self.ld_i_bcd_of_reg,
            0x55: self.store_regs_at_i,
            0x65: self.ld_regs_at_i
        }
        
        
    def load_rom(self, file_path):
        """
        Load the rom into the internal memory.

        :param file_path: Path to the rom file.
        """
        
        with open(file_path, "rb") as f:
            rom_data = f.read()
            self.load_memory(self.START_ADDR, rom_data)
       
    def load_memory(self, start_addr, data):
        """
        Load the data into memory.

        :param start_addr: Address to start loading data at.
        :param data: Array of bytes for the data.
        """
        
        self.validate_data_size(start_addr, data)
        for i in range(len(data)):
            self.memory[start_addr + i] = data[i]

    def validate_data_size(self, start_addr, data):
        """
        Validate that the size of the data is not greater than the memory available.

        :param data: Array of bytes for the rom.
        
        :raises DataTooLarge: Data larger than available memory.
        """
        
        if len(data) > (self.MEMORY_SIZE - start_addr):
                raise DataTooLarge("Data is too large to fit in memory.")

    def main_loop(self):
        self.create_display()
        self.init_clocks()
        
        while True:
            self.handle_pygame_events()
            
            if self.DEBUG:
                self.debugger.run()
            
            self.emulate_cyle()
            self.update_timers() 
            self.cpu_clock_delay()


    def create_display(self):
        """
        Create a pygame display.
        """
        
        if self.display is None:
            self.display = Chip8Display(self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)
            self.display.create_display()

    def init_clocks(self):
        self.clock_ticks = pygame.time.get_ticks()
        self.timer_ticks = pygame.time.get_ticks()
        
    def handle_pygame_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                
    def emulate_cyle(self):
        opcode = self.fetch_opcode()
        self.execute_opcode(opcode)
        
    def fetch_opcode(self):
        """
        Fetch the next opcode from memory.

        :return: The next 2 bytes in memory.
        """
        
        return self.memory[self.registers["pc"] : self.registers["pc"] + 2]

    def execute_opcode(self, opcode):
        opcode_nibbles = self.get_opcode_nibble_dict(opcode)
                
        first_nibble = opcode_nibbles["first_nibble"]
        
        lookup_function = self.opcode_first_nibble_lookup[first_nibble]
        lookup_function(opcode_nibbles)
        
        # Increase program counter
        self.registers["pc"] += 2
      
    def get_opcode_nibble_dict(self, opcode):
        """
        Create dictionary of opcode nibbles and masked bits
        """
        
        combined_opcode = (opcode[0] << 8 | opcode[1]) & 0xFFFF
        opcode_nibbles = {
            "all"              : combined_opcode,
            "first_nibble"      : (combined_opcode & 0xF000) >> 12,
            "second_nibble"     : (combined_opcode & 0x0F00) >> 8,
            "third_nibble"      : (combined_opcode & 0x00F0) >> 4,
            "fourth_nibble"     : combined_opcode & 0x000F,
            "last_three_bits": combined_opcode & 0x0FFF,           # 12 bit data, normally addr
            "last_byte"         : combined_opcode & 0x00FF            # Last byte in opcode
        }
        
        return opcode_nibbles

    def update_timers(self):
        cur_tick = pygame.time.get_ticks()
        if (cur_tick - self.timer_ticks) >= self.TIMER_SPEED:
            self.decrease_timers()
            self.timer_ticks = cur_tick

    def cpu_clock_delay(self):
        cur_tick = pygame.time.get_ticks()
        if (cur_tick - self.clock_ticks) < self.CLOCK_SPEED:
            pygame.time.delay(cur_tick - self.clock_ticks)
            self.clock_ticks = cur_tick

    def decrease_timers(self):
        """
        Update the timers.
        """
        # cur_time_ms = self.timer_clock.tick()
        # if not (cur_time_ms >= self.TIMER_SPEED):
        #     return
        
        if self.timers["delay"] > 0:
            self.timers["delay"] -= 1
        if self.timers["sound"] > 0:
            self.timers["sound"] -= 1

    def lookup_opcode_0x0(self, opcode_nibbles):
        """
        Lookup opcode beginning with 0x0, running the appropriate function
        based on the last byte.

        :param opcode_nibbles: dict of opcode nibbles
        """
        
        last_byte = opcode_nibbles["last_byte"]
        self.validate_lookup(self.opcode_0x0_last_byte_lookup, last_byte)
    
        function_lookup = self.opcode_0x0_last_byte_lookup[last_byte]
        function_lookup(opcode_nibbles)
        
    def lookup_opcode_0x8(self, opcode_nibbles):
        """
        Lookup opcode beginning with 0x8, running the appropriate function
        based on the fourth nibble.

        :param opcode_nibbles: dict of opcode nibbles
        """
        
        fourth_nibble = opcode_nibbles["fourth_nibble"]
        self.validate_lookup(self.opcode_0x8_fourth_nibble_lookup, fourth_nibble)
        
        function_lookup = self.opcode_0x8_fourth_nibble_lookup[fourth_nibble]
        function_lookup(opcode_nibbles)
        
    def lookup_opcode_0xE(self, opcode_nibbles):
        """
        Lookup opcode beginning with 0xE, running the appropriate function
        based on the last byte.

        :param opcode_nibbles: dict of opcode nibbles
        """
        
        last_byte = opcode_nibbles["last_byte"]
        self.validate_lookup(self.opcode_0xE_last_byte_lookup, last_byte)
    
        function_lookup = self.opcode_0xE_last_byte_lookup[last_byte]
        function_lookup(opcode_nibbles)
        
    def lookup_opcode_0xF(self, opcode_nibbles):
        """
        Lookup opcode beginning with 0xF, running the appropriate function
        based on the last byte.

        :param opcode_nibbles: dict of opcode nibbles
        """
        
        last_byte = opcode_nibbles["last_byte"]
        self.validate_lookup(self.opcode_0xF_last_byte_lookup, last_byte)
    
        function_lookup = self.opcode_0xF_last_byte_lookup[last_byte]
        function_lookup(opcode_nibbles)

    def validate_lookup(self, lookup_table, nibble):
        """
        Check if a lookup table contains a key for the given nibble.
        Raise exception if not.
        
        :param lookup_table: Lookup table to check
        :param nibble: Nibble to check
        
        :raises InvalidLookup: If nibble is not in lookup table
        """
        
        try:
            lookup_table[nibble]
        except KeyError as e:
            raise InvalidLookup(f"{nibble} not found in {str(lookup_table)}.") from e
    
    def load_fontset(self):
        self.load_memory(self.FONT_ADDR_START, self.FONT_SET)

    ###########################
    # Opcode functions
    ###########################

    def clear_screen(self, opcode_nibbles=None):
        """
        Opcode 00E0 - CLS
        
        Clear the screen.
        """

        self.display.clear_display()
        self.display.update_display()

    def return_from_subrtn(self, opcode_nibbles=None):
        """
        Opcode 00EE - RET
        
        Return from a subroutine by popping the stack and setting the program counter to the popped value.
        """

        self.registers["pc"] = self.stack[self.registers["sp"]]
        self.stack[self.registers["sp"]] = 0
        self.registers["sp"] -= 1

    def jump_addr(self, opcode_nibbles):
        """
        Opcode 1nnn - JP addr
        
        Jump to address nnn.
        """

        self.registers["pc"] = opcode_nibbles["last_three_bits"]
        self.registers["pc"] -= 2

    def call_addr(self, opcode_nibbles):
        """
        Opcode 2nnn - CALL addr
        
        Call subroutine at nnn. Push current pc onto stack and jump to nnn.
        """

        self.registers["sp"] += 1
        self.stack[self.registers["sp"]] = self.registers["pc"]
        self.registers["pc"] = opcode_nibbles["last_three_bits"]
        self.registers["pc"] -= 2        

    def skip_reg_eq_byte(self, opcode_nibbles):
        """
        Opcode 3xkk - SE Vx, byte
        
        Skip next instruction if Vx = kk.
        """

        if self.registers["v"][opcode_nibbles["second_nibble"]] == opcode_nibbles["last_byte"]:
            self.registers["pc"] += 2

    def skip_reg_neq_byte(self, opcode_nibbles):
        """
        Opcode 4xkk - SNE Vx, byte
        
        Skip next instruction if Vx != kk.
        """

        if self.registers["v"][opcode_nibbles["second_nibble"]] != opcode_nibbles["last_byte"]:
            self.registers["pc"] += 2

    def skip_reg_eq_reg(self, opcode_nibbles):
        """
        Opcode 5xy0 - SE Vx, Vy
        
        Skip next instruction if Vx = Vy.
        """

        if (
            self.registers["v"][opcode_nibbles["second_nibble"]]
            == self.registers["v"][opcode_nibbles["third_nibble"]]
        ):
            self.registers["pc"] += 2

    def ld_to_reg(self, opcode_nibbles):
        """
        Opcode 6xkk - LD Vx, byte
        
        Load byte into Vx.
        """

        self.registers["v"][opcode_nibbles["second_nibble"]] = opcode_nibbles["last_byte"]

    def add_byte_to_reg(self, opcode_nibbles):
        """
        Opcode 7xkk - ADD Vx, byte
        
        Add byte to Vx.
        """

        second_nibble = self.registers["v"][opcode_nibbles["second_nibble"]]
        last_byte = opcode_nibbles["last_byte"]
        
        temp = second_nibble + last_byte
        if temp > 255:
            temp -= 256
            
        self.registers["v"][opcode_nibbles["second_nibble"]] = temp

    def ld_reg_to_reg(self, opcode_nibbles):
        """
        Opcode 8xy0 - LD Vx, Vy
        
        Load Vy into Vx.
        """

        self.registers["v"][opcode_nibbles["second_nibble"]] = self.registers["v"][
            opcode_nibbles["third_nibble"]
        ]

    def or_regs(self, opcode_nibbles):
        """
        Opcode 8xy1 - OR Vx, Vy
        
        Or Vx and Vy. Set Vx to result.
        """

        self.registers["v"][opcode_nibbles["second_nibble"]] |= self.registers["v"][
            opcode_nibbles["third_nibble"]
        ]

    def and_regs(self, opcode_nibbles):
        """
        Opcode 8xy2 - AND Vx, Vy
        
        And Vx and Vy. Set Vx to result.
        """

        self.registers["v"][opcode_nibbles["second_nibble"]] &= self.registers["v"][
            opcode_nibbles["third_nibble"]
        ]

    def xor_regs(self, opcode_nibbles):
        """
        Opcode 8xy3 - XOR Vx, Vy
        
        Xor Vx and Vy. Set Vx to result.
        """

        self.registers["v"][opcode_nibbles["second_nibble"]] ^= self.registers["v"][
            opcode_nibbles["third_nibble"]
        ]

    def add_regs(self, opcode_nibbles):
        """
        Opcode 8xy4 - ADD Vx, Vy
        
        Add Vx and Vy. Set Vx to result.
        Set VF to 1 if there is a carry, 0 otherwise.
        """

        second_nibble = self.registers["v"][opcode_nibbles["second_nibble"]]
        third_nibble = self.registers["v"][opcode_nibbles["third_nibble"]]

        temp = second_nibble + third_nibble

        carry = False
        if (temp > 255):
            carry = True
            temp -= 256
            
        temp &= 0xFF
        self.registers["v"][opcode_nibbles["second_nibble"]] = temp
        
        self.registers["v"][0xF] = 1 if carry else 0

    def sub_regs(self, opcode_nibbles):
        """
        Opcode 8xy5 - SUB Vx, Vy
        
        Subtract Vx from Vy. Set Vx to result.
        Set VF to 1 if there is no borrow, 0 otherwise.
        """

        second_nibble = self.registers["v"][opcode_nibbles["second_nibble"]]
        third_nibble = self.registers["v"][opcode_nibbles["third_nibble"]]
        
        borrow = False
        if (second_nibble > third_nibble):
            second_nibble -= third_nibble
        else:
            second_nibble = 256 + second_nibble - third_nibble
            borrow = True
        
        second_nibble &= 0xFF
        self.registers["v"][opcode_nibbles["second_nibble"]] = second_nibble
        
        self.registers["v"][0xF] = 0 if borrow else 1

    def right_shift_reg(self, opcode_nibbles):
        """
        Opcode 8xy6 - SHR Vx {, Vy}
        
        Right shift Vx. Set Vx to result.
        """

        self.registers["v"][0xF] = self.registers["v"][opcode_nibbles["second_nibble"]] & 0x1
        self.registers["v"][opcode_nibbles["second_nibble"]] >>= 1
        self.registers["v"][opcode_nibbles["second_nibble"]] &= 0xFF

    def reverse_sub_regs(self, opcode_nibbles):
        """
        Opcode 8xy7 - SUBN Vx, Vy
        
        Subtract Vy from Vx. Set Vx to result.
        Set VF to 1 if there is no borrow, 0 otherwise.
        """

        second_nibble = self.registers["v"][opcode_nibbles["second_nibble"]]
        third_nibble = self.registers["v"][opcode_nibbles["third_nibble"]]

        borrow = False
        if (third_nibble > second_nibble):
            third_nibble -= second_nibble
        else:
            third_nibble = 256 + third_nibble - second_nibble
            borrow = True

        third_nibble &= 0xFF
        self.registers["v"][opcode_nibbles["second_nibble"]] = third_nibble
        
        self.registers["v"][0xF] = 0 if borrow else 1

    def left_shift_reg(self, opcode_nibbles):
        """
        Opcode 8xyE - SHL Vx {, Vy}
        
        Shift Vx left. Set Vx to result.
        Set VF to 1 if most significant bit is set, 0 otherwise.
        """

        self.registers["v"][0xF] = \
            (self.registers["v"][opcode_nibbles["second_nibble"]] & 0x80) >> 7
            
        self.registers["v"][opcode_nibbles["second_nibble"]] <<= 1
        self.registers["v"][opcode_nibbles["second_nibble"]] &= 0xFF

    def skip_reg_neq_reg(self, opcode_nibbles):
        """
        Opcode 9xy0 - SNE Vx, Vy
        
        Skip next instruction if Vx != Vy.
        """

        if (
            self.registers["v"][opcode_nibbles["second_nibble"]]
            != self.registers["v"][opcode_nibbles["third_nibble"]]
        ):
            self.registers["pc"] += 2

    def ld_i(self, opcode_nibbles):
        """
        Opcode Annn - LD I, addr
        
        Load I with nnn.
        """

        self.registers["i"] = opcode_nibbles["last_three_bits"]

    def jmp_reg0_with_byte(self, opcode_nibbles):
        """
        Opcode Bnnn - JP V0, addr
        
        Jump to location nnn + V0.
        """

        self.registers["pc"] = (opcode_nibbles["last_three_bits"]) + self.registers["v"][0x0]
        self.registers["pc"] &= 0xFFFF
        self.registers["pc"] -= 2

    def store_rnd_anded_byte_to_reg(self, opcode_nibbles):
        """
        Opcode Cxkk - RND Vx, byte
        
        Set Vx to random byte ANDed with kk.
        """

        self.registers["v"][opcode_nibbles["second_nibble"]] = (
            random.randint(0, 255) & opcode_nibbles["last_byte"]
        )

    def draw_bytes(self, opcode_nibbles):
        """
        Opcode Dxyn - DRW Vx, Vy, nibble
        
        Draws a sprite at coordinate (Vx, Vy) with width 8 pixels and height n pixels.
        """

        num_bytes_to_draw = opcode_nibbles["fourth_nibble"]
        x_pos = self.registers["v"][opcode_nibbles["second_nibble"]]
        y_pos = self.registers["v"][opcode_nibbles["third_nibble"]]

        overwritten = False

        for i in range(num_bytes_to_draw):
            byte_to_draw = self.memory[self.registers["i"] + i]
            draw_byte_ret_val = self.display.draw_byte(x_pos, y_pos + i, byte_to_draw)

            if draw_byte_ret_val:
                overwritten = True

        self.registers["v"][0xF] = 1 if overwritten else 0

    def skip_on_keypress(self, opcode_nibbles):
        """
        Opcode Ex9E - SKP Vx
        
        Skip next instruction if key with the value of Vx is pressed.
        """
    
        key = self.registers["v"][opcode_nibbles["second_nibble"]]
        if self.is_key_pressed(key):
            self.registers["pc"] += 2
        
    def skip_on_not_keypress(self, opcode_nibbles):
        """
        Opcode ExA1 - SKNP Vx
        
        Skip next instruction if key with the value of Vx is not pressed.
        """
        
        key = self.registers["v"][opcode_nibbles["second_nibble"]]
        if not self.is_key_pressed(key):
            self.registers["pc"] += 2

    def is_key_pressed(self, key):
        """
        Check if a key is pressed.
        
        :param key: Key to check
        
        :return: True if key is pressed, False otherwise
        """
        
        keys_pressed = pygame.key.get_pressed()

        return bool(keys_pressed[self.KEY_MAPPINGS[key]])

    def ld_reg_with_dly_timer(self, opcode_nibbles):
        """
        Opcode Fx07 - LD Vx, DT
        
        Load the value of DT into Vx.
        """

        self.registers["v"][opcode_nibbles["second_nibble"]] = self.timers["delay"]

    def wait_for_input(self, opcode_nibbles):
        """
        Opcode Fx0A - LD Vx, K
        
        Wait for a key press, store the value of the key in Vx.
        """
        
        key_pressed = self.wait_and_get_key()
        self.registers["v"][opcode_nibbles["second_nibble"]] = key_pressed

    def wait_and_get_key(self):
        """
        Wait for a keypress.
        
        :return: Key pressed
        """
        while True:
            for event in pygame.event.get():
                # Handle quit event
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                # Wait until a valid key is pressed
                if (event.type == pygame.KEYDOWN) and (event.key in self.KEY_MAPPINGS.values()):
                    return event.key

    def ld_delay_timer_with_reg(self, opcode_nibbles):
        """
        Opcode Fx15 - LD DT, Vx
        
        Set the delay timer to Vx.
        """

        self.timers["delay"] = self.registers["v"][opcode_nibbles["second_nibble"]]

    def ld_sound_timer_with_reg(self, opcode_nibbles):
        """
        Opcode Fx18 - LD ST, Vx
        
        Set the sound timer to Vx.
        """
        self.timers["sound"] = self.registers["v"][opcode_nibbles["second_nibble"]]

    def add_i_with_reg(self, opcode_nibbles):
        """
        Opcode Fx1E - ADD I, Vx
        """

        self.registers["i"] += self.registers["v"][opcode_nibbles["second_nibble"]]
        self.registers["i"] &= 0xFFFF

    def ld_i_font_sprite(self, opcode_nibbles):
        """
        Opcode Fx29 - LD F, Vx
        
        Set I to the location of the sprite for the character in Vx.
        """
        
        sprite_char = self.registers["v"][opcode_nibbles["second_nibble"]]
        sprite_char_addr = self.FONT_ADDR_START + (sprite_char * 5)

    def ld_i_bcd_of_reg(self, opcode_nibbles):
        """
        Opcode Fx33 - LD B, Vx
        
        Load the BCD representation of Vx into memory locations I, I+1, and I+2.
        """

        second_nibble = self.registers["v"][opcode_nibbles["second_nibble"]]
        
        # 100s places
        self.memory[self.registers["i"]] = (
            int((second_nibble / 100) % 10) & 0xFF
        )
        
        # 10s place
        self.memory[self.registers["i"] + 1] = (
            int((second_nibble / 10) % 10) & 0xFF
        )
        
        # 1s place
        self.memory[self.registers["i"] + 2] = (
            int(second_nibble % 10) & 0xFF
        )

    def store_regs_at_i(self, opcode_nibbles):
        """
        Opcode Fx55 - LD [I], Vx
        
        Store registers V0 through Vx in memory starting at location I.
        """

        for i in range(opcode_nibbles["second_nibble"] + 1):
            self.memory[self.registers["i"] + i] = self.registers["v"][i]

    def ld_regs_at_i(self, opcode_nibbles):
        """
        Opcode Fx65 - LD Vx, [I]
        
        Load registers V0 through Vx from memory starting at location I.
        """

        for i in range(opcode_nibbles["second_nibble"] + 1):
            self.registers["v"][i] = self.memory[self.registers["i"] + i]

if __name__ == "__main__":
    x = Chip8CPU()
    x.load_rom("break.ch8")
    x.main_loop()
