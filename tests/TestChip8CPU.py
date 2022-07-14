import os
import sys
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")

from chip8.Chip8CPU import Chip8CPU

class TestChip8CPU(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestChip8CPU, self).__init__(*args, **kwargs)

    def setUp(self):
        self.chip8 = Chip8CPU()

    def test_load_rom(self):
        """
        Test first and last byte of ROM
        """
        self.chip8.load_rom("tests/test_opcode.ch8")

        # First byte of file
        self.assertEqual(self.chip8.memory[0x200], 0x12)

        # Last byte of file
        self.assertEqual(self.chip8.memory[0x200 + 0x01DD], 0xDC)


    def test_clear_screen(self):
        """
        Test Opcode 0x00E0 - CLS
        
        Clear the screen.
        """

        self.chip8.display = MagicMock()
        
        self.chip8.clear_screen()
        
        self.chip8.display.clear_display.assert_called_with()
        self.chip8.display.update_display.assert_called_with()

    def test_return_from_subrtn(self):
        """
        Test Opcode 00EE - RET
        
        Return from a subroutine by popping the stack and setting the program counter to the popped value.
        """

        self.chip8.registers["pc"] = 0x240
        self.chip8.stack[0x1] = 0x220
        self.chip8.registers["sp"] = 0x1
        
        self.chip8.return_from_subrtn()
        
        self.assertEqual(self.chip8.registers["pc"], 0x220)


    def test_jump_addr(self):
        """
        Test Opcode 1nnn - JP addr
        
        Jump to address nnn.
        """
        
        nibble_dict = {
            "last_three_bits": 0x0300   
        }
        
        self.chip8.registers["pc"] = 0x230

        self.chip8.jump_addr(nibble_dict)

        self.assertEqual(self.chip8.registers["pc"],  (0x0300 - 0x2))

    def test_call_addr(self):
        """
        Test Opcode 2nnn - CALL addr
        
        Call subroutine at nnn. Push current pc onto stack and jump to nnn.
        """

        nibble_dict = {
            "last_three_bits": 0x0350   
        }
        
        self.chip8.registers["pc"] = 0x240
        self.chip8.registers["sp"] = 0x4
        
        self.assertEqual(self.chip8.registers["sp"], 0x4)
        
        self.chip8.call_addr(nibble_dict)

        self.assertEqual(self.chip8.registers["pc"],  (0x0350 - 0x2))
        self.assertEqual(self.chip8.stack[0x5], 0x240)
        self.assertEqual(self.chip8.registers["sp"], 0x5)


    def test_skip_reg_eq_byte_neq(self):
        """
        Test Opcode 3xkk - SE Vx, byte
        Test when not equal
        
        Skip next instruction if Vx = kk.
        """

        nibble_dict = {
            "second_nibble": 0x1,
            "last_byte": 0x23,
        }
        
        self.chip8.registers["pc"] = 0x330
        
        self.chip8.registers["v"][0x1] = 0x10
        
        self.chip8.skip_reg_eq_byte(nibble_dict)
        
        self.assertEqual(self.chip8.registers["pc"], 0x330)
        

    def test_skip_reg_eq_byte_eq(self):
        """
        Test Opcode 3xkk - SE Vx, byte
        Test when equal
        
        Skip next instruction if Vx = kk.
        """

        nibble_dict = {
            "second_nibble": 0x2,
            "last_byte": 0x12,
        }
        
        self.chip8.registers["pc"] = 0x430
        
        self.chip8.registers["v"][0x2] = 0x12
        
        self.chip8.skip_reg_eq_byte(nibble_dict)
        
        self.assertEqual(self.chip8.registers["pc"], 0x432)

    def test_skip_reg_neq_byte_neq(self):
        """
        Test Opcode 4xkk - SNE Vx, byte
        Test when not equal
        
        Skip next instruction if Vx != kk.
        """

        nibble_dict = {
            "second_nibble": 0x4,
            "last_byte": 0x10,
        }
        
        self.chip8.registers["pc"] = 0x510
        
        self.chip8.registers["v"][0x4] = 0x22
        
        self.chip8.skip_reg_neq_byte(nibble_dict)
        
        self.assertEqual(self.chip8.registers["pc"], 0x512)

    def test_skip_reg_neq_byte_eq(self):
        """
        Test Opcode 4xkk - SNE Vx, byte
        Test when equal
        
        Skip next instruction if Vx != kk.
        """

        nibble_dict = {
            "second_nibble": 0x8,
            "last_byte": 0x50,
        }
        
        self.chip8.registers["pc"] = 0x600
        
        self.chip8.registers["v"][0x8] = 0x50
        
        self.chip8.skip_reg_neq_byte(nibble_dict)
        
        self.assertEqual(self.chip8.registers["pc"], 0x600)

    def test_skip_reg_eq_reg_neq(self):
        """
        Test Opcode 5xy0 - SE Vx, Vy
        Test when not equal
        
        Skip next instruction if Vx = Vy.
        """
        
        nibble_dict = {
            "second_nibble": 0x4,
            "third_nibble": 0x0,
        }
        
        self.chip8.registers["pc"] = 0x440
        
        self.chip8.registers["v"][0x4] = 0x22
        self.chip8.registers["v"][0x0] = 0x10
        
        self.chip8.skip_reg_eq_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["pc"], 0x440)

    def test_skip_reg_eq_reg_eq(self):
        """
        Test Opcode 5xy0 - SE Vx, Vy
        Test when equal
        
        Skip next instruction if Vx = Vy.
        """

        nibble_dict = {
            "second_nibble": 0xE,
            "third_nibble": 0xF,
        }
        
        self.chip8.registers["pc"] = 0xFA0
        
        self.chip8.registers["v"][0xE] = 0xAA
        self.chip8.registers["v"][0xF] = 0xAA
        
        self.chip8.skip_reg_eq_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["pc"], 0xFA2)

    def test_ld_to_reg(self):
        """
        Test Opcode 6xkk - LD Vx, byte
        
        Load byte into Vx.
        """

        nibble_dict = {
            "second_nibble": 0xB,
            "last_byte": 0xBB,
        }
        
        self.chip8.registers["v"][0xB] = 0x0
        
        self.chip8.ld_to_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0xB], 0xBB)

    def test_add_byte_to_reg(self):
        """
        Test Opcode 7xkk - ADD Vx, byte
        
        Add byte to Vx.
        """

        nibble_dict = {
            "second_nibble": 0xC,
            "last_byte": 0xDA,
        }
        
        self.chip8.registers["v"][0xC] = 0x01

        self.chip8.add_byte_to_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0xC], 0xDB)
    
    def test_add_byte_to_reg_overflow(self):
        """
        Test Opcode 7xkk - ADD Vx, byte
        Test when addition goes over 255
        
        Add byte to Vx.
        """

        nibble_dict = {
            "second_nibble": 0xD,
            "last_byte": 0xFF,
        }
        
        self.chip8.registers["v"][0xD] = 0x0A

        self.chip8.add_byte_to_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0xD], 0x09)

    def test_ld_reg_to_reg(self):
        """
        Test Opcode 8xy0 - LD Vx, Vy
        
        Load Vy into Vx.
        """

        nibble_dict = {
            "second_nibble": 0x1,
            "third_nibble": 0x2,
        }
        
        self.chip8.registers["v"][0x1] = 0x00
        self.chip8.registers["v"][0x2] = 0x11
        
        self.chip8.ld_reg_to_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0x1], 0x11)


    def test_or_regs(self):
        """
        Test Opcode 8xy1 - OR Vx, Vy
        
        Or Vx and Vy. Set Vx to result.
        """

        nibble_dict = {
            "second_nibble": 0x2,
            "third_nibble": 0x3,
        }
        
        self.chip8.registers["v"][0x2] = 0x0F
        self.chip8.registers["v"][0x3] = 0xF0
        
        self.chip8.or_regs(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0x2], 0xFF)

    def test_and_regs(self):
        """
        Test Opcode 8xy2 - AND Vx, Vy
        
        And Vx and Vy. Set Vx to result.
        """

        nibble_dict = {
            "second_nibble": 0xD,
            "third_nibble": 0xE,
        }
        
        self.chip8.registers["v"][0xD] = 0x0A
        self.chip8.registers["v"][0xE] = 0x0D
        
        self.chip8.and_regs(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0xD], 0x08)

    def test_xor_regs(self):
        """
        Test Opcode 8xy3 - XOR Vx, Vy
        
        Xor Vx and Vy. Set Vx to result.
        """

        nibble_dict = {
            "second_nibble": 0x4,
            "third_nibble": 0x5,
        }
        
        self.chip8.registers["v"][0x4] = 0x0F
        self.chip8.registers["v"][0x5] = 0xAB
        
        self.chip8.xor_regs(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0x4], 0xA4)

    def test_add_regs_no_carry(self):
        """
        Test Opcode 8xy4 - ADD Vx, Vy
        Test without carry
        
        Add Vx and Vy. Set Vx to result.
        Set VF to 1 if there is a carry, 0 otherwise.
        """

        nibble_dict = {
            "second_nibble": 0x6,
            "third_nibble": 0x7,
        }
        
        self.chip8.registers["v"][0x6] = 0x0F
        self.chip8.registers["v"][0x7] = 0xAB
        
        self.chip8.add_regs(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0x6], 0xBA)
        self.assertEqual(self.chip8.registers["v"][0xF], 0x0)

    def test_add_regs_carry(self):
        """
        Test Opcode 8xy4 - ADD Vx, Vy
        Test with carry
        
        Add Vx and Vy. Set Vx to result.
        Set VF to 1 if there is a carry, 0 otherwise.
        """

        nibble_dict = {
            "second_nibble": 0x8,
            "third_nibble": 0x9,
        }
        
        self.chip8.registers["v"][0x8] = 0xFF
        self.chip8.registers["v"][0x9] = 0x0B
        
        self.chip8.add_regs(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0x8], 0x0A)
        self.assertEqual(self.chip8.registers["v"][0xF], 0x1)

    def test_sub_regs_no_borrow(self):
        """
        Test Opcode 8xy5 - SUB Vx, Vy
        Test without borrow
        
        Subtract Vx from Vy. Set Vx to result.
        Set VF to 1 if there is no borrow, 0 otherwise.
        """

        nibble_dict = {
            "second_nibble": 0xA,
            "third_nibble": 0xB,
        }
        
        self.chip8.registers["v"][0xA] = 0xAC
        self.chip8.registers["v"][0xB] = 0x0C
        
        self.chip8.sub_regs(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0xA], 0xA0)
        self.assertEqual(self.chip8.registers["v"][0xF], 0x1)

    def test_sub_regs_borrow(self):
        """
        Test Opcode 8xy5 - SUB Vx, Vy
        Test with borrow
        
        Subtract Vx from Vy. Set Vx to result.
        Set VF to 1 if there is no borrow, 0 otherwise.
        """

        nibble_dict = {
            "second_nibble": 0xC,
            "third_nibble": 0xD,
        }
        
        self.chip8.registers["v"][0xC] = 0x0A
        self.chip8.registers["v"][0xD] = 0xDD
        
        self.chip8.sub_regs(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0xC], 0x2D)
        self.assertEqual(self.chip8.registers["v"][0xF], 0x0)

    def test_right_shift_reg(self):
        """
        Test Opcode 8xy6 - SHR Vx {, Vy}
        
        Right shift Vx. Set Vx to result.
        """

        nibble_dict = {
            "second_nibble": 0xE,
            "third_nibble": 0xF,
        }
        
        self.chip8.registers["v"][0xE] = 0x0F
        
        self.chip8.right_shift_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0xE], 0x07)

    def test_reverse_sub_regs_no_borrow(self):
        """
        Test Opcode 8xy7 - SUBN Vx, Vy
        Test without borrow
        
        Subtract Vy from Vx. Set Vx to result.
        Set VF to 1 if there is no borrow, 0 otherwise.
        """


        nibble_dict = {
            "second_nibble": 0xA,
            "third_nibble": 0xE,
        }
        
        self.chip8.registers["v"][0xA] = 0xCA
        self.chip8.registers["v"][0xE] = 0xFA
        
        self.chip8.reverse_sub_regs(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0xA], 0x30)
        self.assertEqual(self.chip8.registers["v"][0xF], 0x1)

    def test_reverse_sub_regs_borrow(self):
        """
        Test Opcode 8xy7 - SUBN Vx, Vy
        Test with borrow
        
        Subtract Vy from Vx. Set Vx to result.
        Set VF to 1 if there is no borrow, 0 otherwise.
        """

        nibble_dict = {
            "second_nibble": 0xB,
            "third_nibble": 0xF,
        }
        
        self.chip8.registers["v"][0xB] = 0xF0
        self.chip8.registers["v"][0xF] = 0x08
        
        self.chip8.reverse_sub_regs(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0xB], 0x18)
        self.assertEqual(self.chip8.registers["v"][0xF], 0x0)

    def test_left_shift_reg_no_carry(self):
        """
        Test Opcode 8xyE - SHL Vx {, Vy}
        Test with no carry
        
        Shift Vx left. Set Vx to result.
        Set VF to 1 if most significant bit is set, 0 otherwise.
        """
            
        nibble_dict = {
            "second_nibble": 0xE,
        }
            
        self.chip8.registers["v"][0xE] = 0x0A
        
        self.chip8.left_shift_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0xE], 0x14)
        self.assertEqual(self.chip8.registers["v"][0xF], 0x0)

    def test_left_shift_reg_carry(self):
        """
        Test Opcode 8xyE - SHL Vx {, Vy}
        Test with carry
        
        Shift Vx left. Set Vx to result.
        Set VF to 1 if most significant bit is set, 0 otherwise.
        """
            
        nibble_dict = {
            "second_nibble": 0x3,
        }
            
        self.chip8.registers["v"][0x3] = 0xF0
        
        self.chip8.left_shift_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0x3], 0xE0)
        self.assertEqual(self.chip8.registers["v"][0xF], 0x1)
        
    def test_reg_neq_reg_eq(self):
        """
        Test Opcode 9xy0 - SNE Vx, Vy
        Test when equal
        
        Skip next instruction if Vx != Vy.
        """
        
        nibble_dict = {
            "second_nibble": 0xA,
            "third_nibble": 0xB,
        }
        
        self.chip8.registers["v"][0xA] = 0x0A
        self.chip8.registers["v"][0xB] = 0x0A
        
        self.chip8.skip_reg_neq_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["pc"], 0x200)
        
    def test_reg_neq_reg_neq(self):
        """
        Test Opcode 9xy0 - SNE Vx, Vy
        Test when not equal
        
        Skip next instruction if Vx != Vy.
        """
        
        nibble_dict = {
            "second_nibble": 0xC,
            "third_nibble": 0x7,
        }
        
        self.chip8.registers["v"][0xC] = 0x10
        self.chip8.registers["v"][0x7] = 0x22
        
        self.chip8.skip_reg_neq_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["pc"], 0x202)
        
    def test_ld_i(self):
        """
        Test Opcode Annn - LD I, addr
        
        Load I with nnn
        """
        
        nibble_dict = {
            "last_three_bits": 0x400
        }
        
        self.chip8.registers["i"] = 0x0
        
        self.chip8.ld_i(nibble_dict)
        
        self.assertEqual(self.chip8.registers["i"], 0x400)
        

    def test_jmp_reg0_with_byte(self):
        """
        Opcode Bnnn - JP V0, addr
        
        Jump to location nnn + V0.
        """
        
        nibble_dict = {
            "last_three_bits": 0xB00
        }
        
        self.chip8.registers["v"][0x0] = 0xF
        
        self.chip8.jmp_reg0_with_byte(nibble_dict)
        
        self.assertEqual(self.chip8.registers["pc"], 0xB0D)
        
    @patch("random.randint")  
    def test_store_rnd_anded_byte_to_reg(self, mock_randint):
        """
        Opcode Cxkk - RND Vx, byte
        
        Set Vx to random byte ANDed with kk.
        """
        
        mock_randint.return_value = 0xCD
        
        nibble_dict = {
            "second_nibble": 0xC,
            "last_byte": 0x07
        }
        
        self.chip8.registers["v"][0xC] = 0x0
        
        self.chip8.store_rnd_anded_byte_to_reg(nibble_dict)
        
        self.assertEqual(self.chip8.registers["v"][0xC], 0x05)

    def test_draw_bytes(self):
        """
        Test Opcode Dxyn - DRW Vx, Vy, nibble
        
        Draws a sprite at coordinate (Vx, Vy) with width 8 pixels and height n pixels.
        """
        
        self.chip8.display = MagicMock()
        self.chip8.display.draw_byte.return_value = False
        
        nibble_dict = {
            "second_nibble": 0xD,
            "third_nibble": 0x0,
            "fourth_nibble": 0x3
        }
        
        self.chip8.registers["v"][0xD] = 0x01
        self.chip8.registers["v"][0x0] = 0x03
        
        self.chip8.registers["i"] = 0x50
        
        self.chip8.memory[self.chip8.registers["i"]]     = 0xF0
        self.chip8.memory[self.chip8.registers["i"] + 1] = 0xBB
        self.chip8.memory[self.chip8.registers["i"] + 2] = 0xA7
        
        self.chip8.draw_bytes(nibble_dict)
        
        self.chip8.display.draw_byte.assert_has_calls([
            mock.call(0x01, 0x03, 0xF0),
            mock.call(0x01, 0x04, 0xBB),
            mock.call(0x01, 0x05, 0xA7)
        ])        
        
        
        

if __name__ == "__main__":
    unittest.main()
