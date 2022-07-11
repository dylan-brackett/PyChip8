"""
A debugger for the Chip8 CPU.
This debugger will act similarly to gdb.
"""

import re
import sys


class Chip8Debugger:
    def __init__(self, Chip8CPU):
        self.chip8 = Chip8CPU
        self.breakpoints = []
        
        self.valid_commands = ["b", "s", "c", "p", "d", "q"]
        
        # Run debugger before launching the emulator
        self.halt = True
        
        self.last_input = ""
            
    def run(self):
        """
        Main debugger loop
        """
        
        opcode = self.get_opcode()
        self.hex_print(self.chip8.registers["pc"], opcode)
        
        self.halt = self.should_halt()
        
        if self.halt:
            self.halt = False
            
            should_continue = False
            while not should_continue:
                command_array = self.get_input()
                should_continue = self.parse_input(command_array)
                self.last_input = command_array
                
    def get_opcode(self):
        return self.chip8.memory[self.chip8.registers["pc"]] << 8 | self.chip8.memory[self.chip8.registers["pc"] + 1]

    def hex_print(self, addr, opcode):
        print("0x%04X\t%04X" % (addr, opcode))

    def should_halt(self):
        """
        Check if the CPU should halt.
        
        :return: True if the CPU should halt, False otherwise.
        """
        
        return bool(self.is_addr_breakpoint(self.chip8.registers["pc"]) or self.halt)

    def is_addr_breakpoint(self, address):
        return bool(address in self.breakpoints)
    
    def get_input(self):
        valid_input = False
        command_array = []
        
        while not valid_input:
            command = input(">> ")
            command = self.format_string(command)
            
            # Use enter to reuse last command
            if len(command) == 0 and self.last_input:
                command_array = self.last_input
                valid_input = True
                return command_array
            
            command_array = command.split(" ")
            

            
            if command_array[0] in self.valid_commands:
                valid_input = True
            
        return command_array
    
    def format_string(self, string):
        """
        Remove extra whitespace from a string.
        
        :param string: The string to remove whitespace from.
        :return: The string without extra whitespace.
        """
        
        string = string.strip()
        string = re.sub(r"\s+", " ", string)
        string = string.lower()
        
        return string
        
    def parse_input(self, command_array):
        should_continue = True
        
        if command_array[0] == "b":
            # Add breakpoint
            self.add_breakpoint(int(command_array[1], 16) & 0xFFFF)
            should_continue = False
        elif command_array[0] == "d":
            # Delete breakpoint
            if command_array[1] in self.breakpoints:
                self.breakpoints.remove(int(command_array[1], 16) & 0xFFFF)
                
            should_continue = False
        elif command_array[0] in  ["s", "n"]:
            # Step
            self.halt = True
        elif command_array[0] == "p":
            should_continue = False
            self.debug_print(command_array)
        elif command_array[0] == "c":
            # Continue running
            pass
        elif command_array[0] == "q":
            # Quit
            sys.exit(0)
        
        return should_continue

    def add_breakpoint(self, address):
        """
        Define a breakpoint at address.
        
        Address format: 0x0000
        
        :param address: The address to break at.
        """
        
        if address not in self.breakpoints:
            self.breakpoints.append(address)

    def debug_print(self, command_array):
        if command_array[1].startswith("0x"):
            # Print memory address
            opcode = self.get_mem_addr(int(command_array[1], 16) & 0xFFFF)
            # Pretty print opcode in hex
            print("0x%04X\t%04X" % (int(command_array[1], 16) & 0xFFFF, opcode))
        elif command_array[1].startswith("v"):
            # Print specified V register as hex
            print("V%s\t%04X" % (command_array[1][1:], \
                  self.chip8.registers["v"][int(command_array[1][1:], 16)]))
            
        elif command_array[1].startswith("i"):
            # Print I register as hex
            print("0x%04X" % self.chip8.registers["i"])
        elif command_array[1].startswith("pc"):
            # Print PC as hex
            print("0x%04X" % self.chip8.registers["pc"])
        elif command_array[1].startswith("sp"):
            print("0x%04X" % self.chip8.registers["sp"])
        elif command_array[1].startswith("stack"):
            for i in range(len(self.chip8.stack)):
                print("\tStack[%d]: %d" % (i, self.chip8.stack[i]))
        elif command_array[1].startswith("b"):
            # Print breakpoints in hex
            for i in self.breakpoints:
                print("0x%04X" % i)
        
    def get_mem_addr(self, address):
        """
        Get the memory address of the given address.
        
        :param address: The address to get the memory address of.
        :return: The opcode at the memory address
        """
    
        opcode = self.chip8.memory[address] << 8 | self.chip8.memory[address + 1]
        return opcode
