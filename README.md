# Slot-Machine
A simple project in python that simulates a slot machine, calculates payouts, probabilities, and analyzes the house edge.

## Game rules
### Base game
- **Layout:** 3x5,
- **Symbols:** 3 high paying, 3 low paying symbols,
- **WILD** symbol that replaces symbols in winning combinations, excluding SCATTER and CASHPOT symbols,
- **SCATTER** symbol that triggers a bonus game of freespins,
- **CASHPOT** symbols that pay out a fixed prize based on a collection mechanic. When they appear on the reels, their values are summed up and added to the total win, provided the number of cashpots reach a threshold of 5,
- **Win evaluation:** 20 fixed paylines, paying left to right.

### Freespins
- **Layout:** 3x5,
- **Number of spins:** 5 
- Only BLANK and CASHPOT symbols appear during free spins.

## Project Structure

The project is organized modularly, allowing for the separation of mathematical logic from the user interface and configuration.

```text
Slot-Machine/
│
├── Classes/                
│   ├── symbol.py           # Definition of individual symbol properties
│   ├── reel.py             # Logic of an individual reel
│   ├── reelSet.py          # Group of reels with specific weights
│   ├── payline.py          # Definition and validation of paylines
│   ├── paytable.py         # Paytable and winning combination rules
│   ├── symbolWindow.py     # Generation of the visible 3x5 grid
│   ├── spinWin.py          # Object storing data for an individual win
│   └── slotMachine.py      # Main game engine
│
├── assets/                 # Graphical assets
├── database/               # Saved session logs in JSON format
├── simulations/            # Mass simulation results
├── calculations/           # Mathematical calculations in Excel
│
├── config.json             # Mathematical configuration
├── main.py                 # Script for running a single spin in the console
├── simulator.py            # Tool for simulating a number of spins and verifying calculations
├── ui.py                   # Graphical User Interface
└── README.md               # Project documentation
```

## How to use
- Step 1: Prerequisites
  - Ensure you have Python 3.x installed on your system.
  - Install the 'Pillow' library (required for images in GUI):
    Command: pip install Pillow

- Step 2: Running from terminal
  - To play a single spin in the terminal:
    Command: python main.py
  - Game results are saved in '/database'

- Step 2: Running the graphical interface
  - To play the game visually and track wins in real-time:
    Command: python ui.py

- Step 3: Statistical simulations
  - To analyze the math (RTP, House Edge) over a number of spins:
    Command: python simulator.py
  - Results are saved in the '/simulations' folder.

- Step 4: Customization
  - Open 'config.json' to modify symbol weights, payout values, 
    or payline patterns. The game will update automatically 
    on the next run.
