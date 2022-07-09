import unittest

from Chip8 import Chip8


class Chip8_Test(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(Chip8_Test, self).__init__(*args, **kwargs)

    def setUp(self):
        self.chip8 = Chip8()

    def test_load_rom(self):
        """
        Test first and last byte of ROM
        """
        self.chip8.load_rom("test_opcode.ch8")

        # First byte of file
        self.assertEqual(self.chip8.memory[0x200], 0x12)

        # Last byte of file
        self.assertEqual(self.chip8.memory[0x200 + 0x01DD], 0xDC)

    def test_emulate_cycle(self):
        """
        Test emulate cycle
        """

        self.chip8.emulate_cyle()
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_clear_screen(self):
        """
        Test Opcode 00E0 - CLS
        
        Clear the screen.
        """

        # Create chip8 window
        self.chip8.create_display()

        # Fill chip8 window with red pixels
        self.chip8.display.fill((255, 0, 0))
        self.chip8.update_display()

        # Opcode 00E0
        self.chip8.memory[0x200] = 0x00
        self.chip8.memory[0x201] = 0xE0

        self.chip8.emulate_cyle()

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

        # Check if pygame display is cleared
        for x in range(self.chip8.display.get_width()):
            for y in range(self.chip8.display.get_height()):
                self.assertEqual(self.chip8.display.get_at((x, y)), (0, 0, 0))

    def test_return_from_subrtn(self):
        """
        Test opcode 00EE
        """

        # Opcode 2nnn
        self.chip8.memory[0x200] = 0x22
        self.chip8.memory[0x201] = 0x34

        # Opcode 00EE
        self.chip8.memory[0x234] = 0x00
        self.chip8.memory[0x235] = 0xEE

        self.chip8.emulate_cyle()

        # Check stack is not empty
        self.assertEqual(self.chip8.registers["sp"], 0x1)
        self.assertEqual(self.chip8.stack[self.chip8.registers["sp"]], 0x200)

        # PC should be 0x234
        self.assertEqual(self.chip8.registers["pc"], 0x234)

        self.chip8.emulate_cyle()

        # Check stack is empty
        self.assertEqual(self.chip8.registers["sp"], 0x0)

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_jump_addr(self):
        """
        Test Opcode 1nnn - JP addr
        
        Jump to address nnn.
        """

        # Opcode 1nnn
        self.chip8.memory[0x200] = 0x12
        self.chip8.memory[0x201] = 0x34

        self.chip8.emulate_cyle()

        # PC should be 0x234
        self.assertEqual(self.chip8.registers["pc"], 0x234)

    def test_op_2nnn(self):
        """
        Test Opcode 2nnn - CALL addr
        
        Call subroutine at nnn. Push current pc onto stack and jump to nnn.
        """

        # Opcode 2nnn
        self.chip8.memory[0x200] = 0x22
        self.chip8.memory[0x201] = 0x34

        self.chip8.emulate_cyle()

        # PC should be 0x234
        self.assertEqual(self.chip8.registers["pc"], 0x234)

        # SP should be 0x1
        self.assertEqual(self.chip8.registers["sp"], 0x1)

        # Stack should be 0x200
        self.assertEqual(self.chip8.stack[0x1], 0x200)

    def test_skip_reg_eq_byte_neq(self):
        """
        Test Opcode 3xkk - SE Vx, byte
        Test when not equal
        
        Skip next instruction if Vx = kk.
        """

        # Opcode 3xkk
        self.chip8.memory[0x200] = 0x31
        self.chip8.memory[0x201] = 0x23

        self.chip8.emulate_cyle()

        # Show that next opcode isn't skipped
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_skip_reg_eq_byte_eq(self):
        """
        Test Opcode 3xkk - SE Vx, byte
        Test when equal
        
        Skip next instruction if Vx = kk.
        """

        # Opcode 3xkk
        self.chip8.memory[0x200] = 0x31
        self.chip8.memory[0x201] = 0x23

        self.chip8.registers[0x1] = 0x23

        self.chip8.emulate_cyle()

        # Show that next opcode is skipped
        self.assertEqual(self.chip8.registers["pc"], 0x204)

    def test_skip_reg_neq_byte_neq(self):
        """
        Test Opcode 4xkk - SNE Vx, byte
        Test when not equal
        
        Skip next instruction if Vx != kk.
        """

        # Opcode 4xkk
        self.chip8.memory[0x200] = 0x41
        self.chip8.memory[0x201] = 0x23

        self.chip8.emulate_cyle()

        # PC should be 0x204
        self.assertEqual(self.chip8.registers["pc"], 0x204)

    def test_skip_reg_neq_byte_eq(self):
        """
        Test Opcode 4xkk - SNE Vx, byte
        Test when equal
        
        Skip next instruction if Vx != kk.
        """

        # Opcode 4xkk
        self.chip8.memory[0x200] = 0x41
        self.chip8.memory[0x201] = 0x23

        self.chip8.registers[0x1] = 0x23

        self.chip8.emulate_cyle()

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_skip_reg_eq_reg_neq(self):
        """
        Test Opcode 5xy0 - SE Vx, Vy
        Test when not equal
        
        Skip next instruction if Vx = Vy.
        """
        self.chip8.memory[0x200] = 0x51
        self.chip8.memory[0x201] = 0x20

        self.chip8.registers[0x0] = 1
        self.chip8.registers[0x1] = 2

        self.chip8.emulate_cyle()

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_skip_reg_eq_reg_eq(self):
        """
        Test Opcode 5xy0 - SE Vx, Vy
        Test when equal
        
        Skip next instruction if Vx = Vy.
        """

        self.chip8.memory[0x200] = 0x51
        self.chip8.memory[0x201] = 0x20

        self.chip8.registers[0x1] = 0x23
        self.chip8.registers[0x2] = 0x23

        self.chip8.emulate_cyle()

        # PC should be 0x204
        self.assertEqual(self.chip8.registers["pc"], 0x204)

    def test_ld_to_reg(self):
        """
        Opcode 6xkk - LD Vx, byte
        
        Load byte into Vx.
        """

        self.chip8.memory[0x200] = 0x61
        self.chip8.memory[0x201] = 0x23

        self.chip8.emulate_cyle()

        # V1 should be 0x23
        self.assertEqual(self.chip8.registers[0x1], 0x23)

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_7xkk(self):
        """
        Test opcode 7xkk
        """

        self.chip8.memory[0x200] = 0x71
        self.chip8.memory[0x201] = 0x23

        self.chip8.registers[0x1] = 0x01

        self.chip8.emulate_cyle()

        # V1 should be 0x24
        self.assertEqual(self.chip8.registers[0x1], 0x24)

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_8xy0(self):
        """
        Test opcode 8xy0
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x20

        self.chip8.registers[0x1] = 0x23
        self.chip8.registers[0x2] = 0x25

        self.chip8.emulate_cyle()

        # V1 should be 0x25
        self.assertEqual(self.chip8.registers[0x1], 0x25)

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_8xy1(self):
        """
        Test opcode 8xy1
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x21

        self.chip8.registers[0x1] = 0x23
        self.chip8.registers[0x2] = 0x25

        self.chip8.emulate_cyle()

        # V1 should be (0x23 | 0x25)
        self.assertEqual(self.chip8.registers[0x1], (0x23 | 0x25))

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_8xy2(self):
        """
        Test opcode 8xy2
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x22

        self.chip8.registers[0x1] = 0x23
        self.chip8.registers[0x2] = 0x25

        self.chip8.emulate_cyle()

        # V1 should be (0x23 & 0x25)
        self.assertEqual(self.chip8.registers[0x1], (0x23 & 0x25))

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_8xy3(self):
        """
        Test opcode 8xy3
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x23

        self.chip8.registers[0x1] = 0x23
        self.chip8.registers[0x2] = 0x25

        self.chip8.emulate_cyle()

        # V1 should be (0x23 ^ 0x25)
        self.assertEqual(self.chip8.registers[0x1], (0x23 ^ 0x25))

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_8xy4_no_carry(self):
        """
        Test opcode 8xy4 without carry
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x24

        self.chip8.registers[0x1] = 0x23
        self.chip8.registers[0x2] = 0x25

        self.chip8.emulate_cyle()

        # V1 should be (0x23 + 0x25)
        self.assertEqual(self.chip8.registers[0x1], (0x23 + 0x25))

        # VF should be 0
        self.assertEqual(self.chip8.registers[0xF], 0)

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_8xy4_carry(self):
        """
        Test opcode 8xy4 with carry by exceeding 0xFF
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x24

        self.chip8.registers[0x1] = 0xFF
        self.chip8.registers[0x2] = 0xAB

        self.chip8.emulate_cyle()

        # V1 should be (0xFF + 0xAB)
        self.assertEqual(self.chip8.registers[0x1], (0xFF + 0xAB) & 0xFF)

        # VF should be 1
        self.assertEqual(self.chip8.registers[0xF], 1)

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_8xy4_carry_fail(self):
        """
        Test opcode 8xy4 with carry by exceeding 0xFF and ensuring result is not greater than
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x24

        self.chip8.registers[0x1] = 0xFF
        self.chip8.registers[0x2] = 0xAB

        self.chip8.emulate_cyle()

        # V1 should be (0xFF + 0xAB)
        self.assertNotEqual(self.chip8.registers[0x1], (0xFF + 0xAB))

        # VF should be 1
        self.assertEqual(self.chip8.registers[0xF], 1)

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_8xy5_no_carry(self):
        """
        Test opcode 8xy5 without carry
        VF is carry when 0
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x25

        self.chip8.registers[0x1] = 0x25
        self.chip8.registers[0x2] = 0x23

        self.chip8.emulate_cyle()

        # V1 should be (0x25 - 0x23)
        self.assertEqual(self.chip8.registers[0x1], ((0x25 - 0x23) & 0xFF))

        # VF should be 0
        self.assertEqual(self.chip8.registers[0xF], 1)

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_8xy5_carry(self):
        """
        Test opcode 8xy5 with carry
        VF is carry when 0
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x25

        self.chip8.registers[0x1] = 0x23
        self.chip8.registers[0x2] = 0x25

        self.chip8.emulate_cyle()

        # V1 should be (0x25 - 0x23)
        self.assertEqual(self.chip8.registers[0x1], 0xFE)

        # VF should be 0
        self.assertEqual(self.chip8.registers[0xF], 0)

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_8xy6(self):
        """
        Test opcode 8xy6
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x26

        self.chip8.registers[0x1] = 0x23

        self.chip8.emulate_cyle()

        # VF Should be 1
        self.assertEqual(self.chip8.registers[0xF], 1)

        # V1 should be (0x23 >> 1)
        self.assertEqual(self.chip8.registers[0x1], (0x23 >> 1))

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_8xy7(self):
        """
        Test opcode 8xy7
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x27

        self.chip8.registers[0x1] = 0x23
        self.chip8.registers[0x2] = 0x25

        self.chip8.emulate_cyle()

        # VF Should be 1
        self.assertEqual(self.chip8.registers[0xF], 1)

        # V1 should be (0x25 - 0x23)
        self.assertEqual(self.chip8.registers[0x1], (0x25 - 0x23))

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op8xyE_no_carry(self):
        """
        Test opcode 8xyE
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x2E

        self.chip8.registers[0x1] = 0x23

        self.chip8.emulate_cyle()

        # VF Should be 0
        self.assertEqual(self.chip8.registers[0xF], 0)

        # V1 should be (0x23 << 1)
        self.assertEqual(self.chip8.registers[0x1], (0x23 << 1) & 0xFF)

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op8xyE_carry(self):
        """
        Test opcode 8xyE
        Set most significant bit to 1 to test carry
        """

        self.chip8.memory[0x200] = 0x81
        self.chip8.memory[0x201] = 0x2E

        self.chip8.registers[0x1] = 0xFF

        self.chip8.emulate_cyle()

        # VF Should be 1
        self.assertEqual(self.chip8.registers[0xF], 1)

        # V1 should be (0xFF << 1)
        self.assertEqual(self.chip8.registers[0x1], (0xFF << 1) & 0xFF)

        # PC should be 0x202
        self.assertEqual(self.chip8.registers["pc"], 0x202)

    def test_op_Dxyn(self):
        """
        Test opcode Dxyn
        """

        self.chip8.create_display()
        self.chip8.memory[0x200] = 0xD0
        self.chip8.memory[0x201] = 0x11
        self.chip8.memory[0x250] = 0xFF
        self.chip8.i = 0x250
        self.chip8.registers[0x0] = 60
        self.chip8.registers[0x1] = 2
        self.chip8.emulate_cyle()

        # Check display if pixels are present
        self.assertEqual(
            self.chip8.display.get_at((60 * self.chip8.SCALE, 2 * self.chip8.SCALE)),
            (255, 255, 255),
        )
        # Check Wrap Around
        self.assertEqual(
            self.chip8.display.get_at((0 * self.chip8.SCALE, 2 * self.chip8.SCALE)),
            (255, 255, 255),
        )


if __name__ == "__main__":
    unittest.main()
