# PyChip8
A Chip8 emulator written in Python. The goal of this project was to learn how to emulators are developed and to create a Chip8 emulator that is well tested, documented, and easy to use.


## Usage

```
python pychip8.py {rom_file}
```

## Controls

The original Chip8 design used a hexadecimal keypad that was laid out like this:

|    |    |    |    |
| -- | -- | -- | -- |
| 1  | 2  | 3  | C  |
| 4  | 5  | 6  | D  |
| 7  | 8  | 9  | E  |
| A  | 0  | B  | F  |

The keypad keys of the emulator are mapped to the following keys:

|    |    |    |    |
| -- | -- | -- | -- |
| 1  | 2  | 3  | 4  |
| Q  | W  | E  | R  |
| A  | S  | D  | F  |
| Z  | X  | C  | V  |

If you want to reassign a key, you can do so in the `config.py` file.

## Testing

To run tests, you can use `python -m unittest discover` in your cloned repository