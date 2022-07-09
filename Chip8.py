"""
Chip8 emulator written in Python

:author dylan-brackett
"""

import random
from time import sleep

import pygame


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
class Chip8:
    def __init__(self):
        
        ###########################
        # CONSTANTS
        ###########################
        
        self.STACK_SIZE = 16
        self.MEMORY_SIZE = 4096
        self.NUM_REGISTERS = 16
        self.START_ADDR = 0x200
        
        ###########################
        # CHIP8 STATE
        ###########################
        
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
            0x0A: self.op_Fx0A
        }
        

        self.load_fontset()

        self.display = None
        self.SCALE = 10
        
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
        pass

    def validate_data_size(self, start_addr, data):
        """
        Validate that the size of the data is not greater than the memory available.

        :param data: Array of bytes for the rom.
        
        :raises DataTooLarge: Data larger than available memory.
        """
        
        if len(data) > (self.MEMORY_SIZE - start_addr):
                raise DataTooLarge("Data is too large to fit in memory.")
            
    def load_memory(self, start_addr, data):
        """
        Load the data into memory.

        :param start_addr: Address to start loading data at.
        :param data: Array of bytes for the data.
        """
        
        self.validate_data_size(start_addr, data)
        for i in range(len(data)):
            self.memory[start_addr + i] = data[i]

    def load_rom(self, file_path):
        """
        Load the rom into the internal memory.

        :param file_path: Path to the rom file.
        """
        
        with open(file_path, "rb") as f:
            rom_data = f.read()
            self.load_memory(self.START_ADDR, rom_data)

    def fetch_opcode(self):
        """
        Fetch the next opcode from memory.

        :return: The next 2 bytes in memory.
        """
        
        return self.memory[self.registers["pc"] : self.registers["pc"] + 2]

    def emulate_cyle(self):
        opcode = self.fetch_opcode()
        self.execute_opcode(opcode)

    # Create pygame display
    def create_display(self):
        self.display = pygame.display.set_mode((64 * self.SCALE, 32 * self.SCALE))
        self.display.fill((0, 0, 0))
        self.update_display()

    def draw_pixel(self, x, y, color):
        pygame.draw.rect(
            self.display,
            color,
            (x * self.SCALE, y * self.SCALE, self.SCALE, self.SCALE),
        )
        self.update_display()

    # Xor x,y with location on screen
    def surface_xor(
        self,
        bit,
        x,
        y,
    ):

        if self.display.get_at((x * self.SCALE, y * self.SCALE)) == (0, 0, 0):
            pixel_present = False
        else:
            pixel_present = True

        return pixel_present ^ bit

    def update_display(self):
        pygame.display.update()

    # Main emulator loop
    def main_loop(self):
        self.create_display()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
            self.emulate_cyle()
            pygame.time.delay(10)

    def get_opcode_nibble_dict(self, opcode):
        """
        Create dictionary of opcode nibbles and masked bits
        """
        
        combined_opcode = (opcode[0] << 8 | opcode[1]) & 0xFFFF
        opcode_nibbles = {
            "all:"              : combined_opcode,
            "first_nibble"      : (combined_opcode & 0xF000) >> 12,
            "second_nibble"     : (combined_opcode & 0x0F00) >> 8,
            "third_nibble"      : (combined_opcode & 0x00F0) >> 4,
            "fourth_nibble"     : combined_opcode & 0x000F,
            "last_three_nibbles": combined_opcode & 0x0FFF,           # 12 bit data, normally addr
            "last_byte"         : combined_opcode & 0x00FF            # Last byte in opcode
        }
        
        return opcode_nibbles
    
    # Execute chip8 opcode
    def execute_opcode(self, opcode):
        opcode_nibbles = self.get_opcode_nibble_dict(opcode)
        first_nibble = opcode_nibbles["first_nibble"]
        
        lookup_function = self.opcode_first_nibble_lookup[first_nibble]
        lookup_function(opcode_nibbles)
        
        # Increase program counter
        self.registers["pc"] += 2
        
    ###########################
    # Opcode functions
    ###########################

    def clear_screen(self, opcode_nibbles):
        """
        Opcode 00E0 - CLS
        
        Clear the screen.
        """

        self.display.fill((0, 0, 0))
        self.update_display()

    def return_from_subrtn(self, opcode_nibbles):
        """
        Opcode 00EE - RET
        """

        self.registers["pc"] = self.stack[self.registers["sp"]]
        self.stack[self.registers["sp"]] = 0
        self.registers["sp"] -= 1

    def jump_addr(self, opcode_nibbles):
        """
        Opcode 1nnn - JP addr
        
        Jump to address nnn.
        """

        self.registers["pc"] = opcode_nibbles["last_three_nibbles"]
        self.registers["pc"] -= 2

    def call_addr(self, opcode_nibbles):
        """
        Opcode 2nnn - CALL addr
        
        Call subroutine at nnn. Push current pc onto stack and jump to nnn.
        """

        self.registers["sp"] += 1
        self.stack[self.registers["sp"]] = self.registers["pc"]
        self.registers["pc"] = opcode_nibbles["last_three_nibbles"]
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

        self.registers["v"][opcode_nibbles["second_nibble"]] += opcode_nibbles["last_byte"]

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

        if (
            self.registers["v"][opcode_nibbles["second_nibble"]]
            + self.registers["v"][opcode_nibbles["third_nibble"]]
        ) > 0xFF:
            self.registers["v"][0xF] = 1
        else:
            self.registers["v"][0xF] = 0
        self.registers["v"][opcode_nibbles["second_nibble"]] += self.registers["v"][
            opcode_nibbles["third_nibble"]
        ]
        self.registers["v"][opcode_nibbles["second_nibble"]] &= 0xFF

    # TODO: Reimplement this
    def sub_regs(self, opcode_nibbles):
        """
        Opcode 8xy5 - SUB Vx, Vy
        
        Subtract Vx from Vy. Set Vx to result.
        Set VF to 1 if there is no borrow, 0 otherwise.
        """

        if (
            self.registers["v"][opcode_nibbles["second_nibble"]]
            > self.registers["v"][opcode_nibbles["third_nibble"]]
        ):
            self.registers["v"][0xF] = 1
        else:
            self.registers["v"][0xF] = 0

        self.registers["v"][opcode_nibbles["second_nibble"]] -= self.registers["v"][
            opcode_nibbles["third_nibble"]
        ]
        self.registers["v"][opcode_nibbles["second_nibble"]] &= 0xFF

    def right_shift_reg(self, opcode_nibbles):
        """
        Opcode 8xy6 - SHR Vx {, Vy}
        
        Right shift Vx. Set Vx to result.
        """

        self.registers["v"][0xF] = self.registers["v"][opcode_nibbles["second_nibble"]] & 0x1
        self.registers["v"][opcode_nibbles["second_nibble"]] >>= 1
        self.registers["v"][opcode_nibbles["second_nibble"]] &= 0xFF

    # TODO: Reimplement this
    def reverse_sub_regs(self, opcode_nibbles):
        """
        Opcode 8xy7 - SUBN Vx, Vy
        
        Subtract Vy from Vx. Set Vx to result.
        Set VF to 1 if there is no borrow, 0 otherwise.
        """

        if (
            self.registers["v"][opcode_nibbles["third_nibble"]]
            > self.registers["v"][opcode_nibbles["second_nibble"]]
        ):
            self.registers["v"][0xF] = 1
        else:
            self.registers["v"][0xF] = 0
        self.registers["v"][opcode_nibbles["second_nibble"]] = (
            self.registers["v"][opcode_nibbles["third_nibble"]]
            - self.registers["v"][opcode_nibbles["second_nibble"]]
        )
        self.registers["v"][opcode_nibbles["second_nibble"]] &= 0xFF

    def left_shift_reg(self, opcode_nibbles):
        """
        Opcode 8xyE - SHL Vx {, Vy}
        
        Shift Vx left. Set Vx to result.
        Set VF to 1 if most significant bit is set, 0 otherwise.
        """

        self.registers["v"][0xF] = (self.registers["v"][opcode_nibbles["second_nibble"]] & 0x80) >> 7
        self.registers["v"][opcode_nibbles["second_nibble"]] <<= 1
        self.registers["v"][opcode_nibbles["second_nibble"]] &= 0xFF

    def skip_reg_neq_reg(self, opcode_nibbles):
        """
        Opcode 9xy0 - SNE Vx, Vy
        """

        if (
            self.registers["v"][opcode_nibbles["second_nibble"]]
            != self.registers["v"][opcode_nibbles["third_nibble"]]
        ):
            self.registers["pc"] += 2

    def ld_i(self, opcode_nibbles):
        """
        Opcode Annn - LD I, addr
        """

        self.i = opcode_nibbles["last_three_nibbles"]

    def jmp_reg0_with_byte(self, opcode_nibbles):
        """
        Opcode Bnnn - JP V0, addr
        """

        self.registers["pc"] = (opcode_nibbles["last_three_nibbles"]) + self.registers["v"][0x0]
        self.registers["pc"] &= 0xFFFF
        self.registers["pc"] -= 2

    def store_rnd_anded_byte_to_reg(self, opcode_nibbles):
        """
        Opcode Cxkk - RND Vx, byte
        """

        self.registers["v"][opcode_nibbles["second_nibble"]] = (
            random.randint(0, 255) & opcode_nibbles["last_byte"]
        )

    def draw_bytes(self, opcode_nibbles):
        """
        Opcode Dxyn - DRW Vx, Vy, nibble
        
        Draws a sprite at coordinate (Vx, Vy) with width 8 pixels and height n pixels.
        """

        # Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
        for i in range(opcode_nibbles["fourth_nibble"]):
            sprite = self.memory[self.i + i]
            for j in range(8):
                sprite_bit = sprite & (0x80 >> j)
                if sprite_bit:
                    # Wrap x around screen
                    x_wrap = (
                        self.registers["v"][opcode_nibbles["second_nibble"]] + j + (8 * i)
                    ) % (self.display.get_width() / self.SCALE)
                    x_wrap = int(x_wrap)

                    if self.surface_xor(
                        sprite_bit, x_wrap, self.registers["v"][opcode_nibbles["third_nibble"]]
                    ):
                        self.draw_pixel(
                            x_wrap,
                            self.registers["v"][opcode_nibbles["third_nibble"]],
                            (255, 255, 255),
                        )
                else:
                    self.registers["v"][0xF] = 0

  
    def skip_on_keypress(self, opcode_nibbles):
        """
        TODO
        Opcode Ex9E - SKP Vx
        """

        pass

    

    def skip_on_not_keypress(self, opcode_nibbles):
        """
        TODO
        Opcode ExA1 - SKNP Vx
        """
        pass

    def ld_reg_with_dly_timer(self, opcode_nibbles):
        """
        Opcode Fx07 - LD Vx, DT
        """

        self.registers["v"][opcode_nibbles["second_nibble"]] = self.delay_timer

    


    def op_Fx0A(self, opcode_nibbles):
        """
        TODO
        Opcode Fx0A - LD Vx, K
        """
        pass

    def op_Fx15(self, opcode_nibbles):
        """
        Opcode Fx15 - LD DT, Vx
        """

        self.delay_timer = self.registers["v"][opcode_nibbles["second_nibble"]]

  

    def op_Fx18(self, opcode_nibbles):
          
        """
        TODO
        Opcode Fx18 - LD ST, Vx
        """
        pass

    def add_i_with_reg(self, opcode_nibbles):
        """
        Opcode Fx1E - ADD I, Vx
        """

        self.i += self.registers["v"][opcode_nibbles["second_nibble"]]
        self.i &= 0xFFFF



    def op_Fx29(self, opcode_nibbles):
        """
        TODO
        Opcode Fx29 - LD F, Vx
        """
        pass

    def op_Fx33(self, opcode_nibbles):
        """
        Opcode Fx33 - LD B, Vx
        """

        # 100s
        self.memory[self.i] = (
            int((self.registers["v"][opcode_nibbles["second_nibble"]] / 100) % 10) & 0xFF
        )
        # 10s place
        self.memory[self.i + 1] = (
            int((self.registers["v"][opcode_nibbles["second_nibble"]] / 10) % 10) & 0xFF
        )
        # 1s place
        self.memory[self.i + 2] = (
            int(self.registers["v"][opcode_nibbles["second_nibble"]] % 10) & 0xFF
        )

    def op_Fx55(self, opcode_nibbles):
        """
        Opcode Fx55 - LD [I], Vx
        """

        for i in range(opcode_nibbles["second_nibble"] + 1):
            self.memory[self.i + i] = self.registers["v"][i]

    def ld_num_reg_bytes_at_i_addr(self, opcode_nibbles):
        """
        Opcode Fx65 - LD Vx, [I]
        """

        for i in range(opcode_nibbles["second_nibble"] + 1):
            self.registers["v"][i] = self.memory[self.i + i]

    def load_fontset(self):
        self.memory[0x0:0xA0] = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80,  # F
        ]


if __name__ == "__main__":
    x = Chip8()
    x.load_rom("test_opcode.ch8")
    x.main_loop()
