"""
Class containing the display of the Chip8 emulator.
"""

import pygame

class Chip8Display:
    def __init__(self, width, height, scale=10):
        ###########################
        # CONSTANTS
        ###########################
        self.BG_COLOR   = (0, 0, 0)
        self.MAIN_COLOR = (255, 255, 255)
        
        ###########################
        # VARIABLES
        ###########################
        
        self.width   = width
        self.height  = height
        self.scale   = scale
        self.display = None
        

    def create_display(self):
        """
        Creates the display of the Chip8 emulator.
        """
        
        if self.display is None:
            self.display = pygame.display.set_mode(
                (self.width * self.scale, self.height * self.scale)
            )
            self.clear_display()
            self.update_display()

    def update_display(self):
        """
        Updates the display of the Chip8 emulator.
        """
        
        pygame.display.update()

    def clear_display(self):
        """
        Clears the display of the Chip8 emulator.
        """
        
        self.display.fill(self.BG_COLOR)
        self.update_display()
        
    def is_drawn_pixel_present(self, x_pos, y_pos):
        """
        Returns True if the pixel at (x_pos, y_pos) is already drawn.
        
        :param x_pos: x-coordinate of the pixel to check.
        :param y_pos: y-coordinate of the pixel to check.
        """
        
        return self.display.get_at((x_pos, y_pos)) == self.MAIN_COLOR
        
        
    def is_bit_set(self, byte, index):
        """
        Returns True if the bit at index is set in byte.
        Where index is 0-7, and index 0 is the most significant bit.
        
        :param byte: The byte to check.
        :param index: The index of the bit to check.
        
        :return: True if the bit is set, False otherwise.
        """
        if index < 0 or index > 7:
            raise ValueError("Index must be between 0 and 7")
        
        return (byte & (1 << (7 - index))) != 0


    def draw_pixel(self, x_pos, y_pos):
        """
        Draws a pixel at coordinate (x_pos, y_pos).
        
        Xors with the pixel on the screen so that pixels already set are unset
        if bit to be drawn is already set.

        :param x_pos: x-coordinate of the pixel to draw.
        :param y_pos: y-coordinate of the pixel to draw.
        :return: True if pixel was overwritten, False otherwise.
        """
        
        overwrite = self.is_drawn_pixel_present(x_pos, y_pos)
        
        if not overwrite:
            # Draw pixel
            pygame.draw.rect(
                self.display,
                self.MAIN_COLOR,
                (x_pos * self.scale, y_pos * self.scale, self.scale, self.scale),
            )
            self.update_display()
        else:
            # Clear pixel
            pygame.draw.rect(
                self.display,
                self.BG_COLOR,
                (x_pos * self.scale, y_pos * self.scale, self.scale, self.scale),
            )
            
        return overwrite
            

    
    def draw_byte(self, x_pos, y_pos, byte):
        """
        Opcode Dxyn - DRW Vx, Vy, nibble
        
        Draws a sprite at coordinate (Vx, Vy) with width 8 pixels and height n pixels.
        
        :param x_pos: x-coordinate of the sprite to draw.
        :param y_pos: y-coordinate of the sprite to draw.
        :param byte: The byte to draw.
        
        :return: True if pixel was overwritten, False otherwise.
        """
        overwritten = False
        for i in range(8):
            if self.is_bit_set(byte, i):
                # Wrap pixel around the screen if it goes out of bounds
                new_x_pos = (x_pos + i) % self.width
                # Adjust y_pos if out of range values are passed
                new_y_pos = (y_pos) % self.height
                
                draw_ret_val = self.draw_pixel(new_x_pos, new_y_pos)
                
                if draw_ret_val:
                    overwritten = True
        
        return overwritten