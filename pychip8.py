from chip8.Chip8CPU import Chip8CPU
import sys

if __name__ == "__main__":
    # Parse command line args
    if len(sys.argv) != 2:
        print("Usage: %s <rom>" % sys.argv[0])
        sys.exit(1)


    # Create a new Chip8 CPU
    chip8 = Chip8CPU()

    # Load the ROM into the CPU
    rom = sys.argv[1]    
    chip8.load_rom(rom)

    # Run the CPU
    chip8.main_loop()
