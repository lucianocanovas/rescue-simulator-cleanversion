# 🚁 Rescue Simulator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![License](https://img.shields.io/badge/License-Educational-orange.svg)

**A strategic rescue simulation game developed for educational purposes**

*Algorithms and Data Structures 2 - Academic Project*

[Features](#-features) • [Installation](#-installation) • [How to Play](#-how-to-play) • [Credits](#-credits)

</div>

---

## 📋 Description

**Rescue Simulator** is a turn-based strategy game where two teams compete to rescue survivors and collect resources from a dangerous minefield. Each team controls different types of vehicles with unique capabilities, and must navigate through hazardous terrain while avoiding mines and optimizing their collection strategies.

This project was developed as part of the **Algorithms and Data Structures 2** course, demonstrating the implementation of:
- 🔍 **Pathfinding algorithms** (BFS for safe route planning)
- 🎯 **Strategy patterns** (Multiple AI behaviors for vehicles)
- 📊 **Data structures** (Grids, queues, graphs)
- 💾 **Game state management** (Serialization and persistence)
- 📈 **Statistical analysis** (CSV generation for performance metrics)

### 🎮 Key Features

- **Multiple Vehicle Types**: Trucks, Jeeps, Cars, and Motorcycles with different capacities
- **Dynamic Mine System**: Various mine types with different danger radius
- **AI Strategies**: 5 different strategies (PickNearest, Kamikaze, Escort, Invader, FullSafe)
- **Turn-based Gameplay**: Step through turns or use autoplay mode
- **Statistics Tracking**: Comprehensive CSV reports with strategy efficiency analysis
- **Save/Load System**: Persistent game states with turn-by-turn replay

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/lucianocanovas/rescue-simulator-cleanversion.git
   cd rescue-simulator-cleanversion
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   The main dependency is:
   - `pygame` - Game engine and graphics

---

## 🎯 How to Play

### Starting the Game

Run the main simulator:
```bash
python rescue_simulator.py
```

### Game Controls

| Key | Action |
|-----|--------|
| `→` (Right Arrow) | Advance one turn |
| `←` (Left Arrow) | Go back one turn |
| `SPACE` | Toggle Autoplay ON/OFF |

### Menu Options

1. **New Game**: Start a fresh simulation with random vehicle/item placement
2. **Load Game**: Resume a previously saved game session
3. **Exit**: Quit the simulator

### Game Modes

- **Manual Mode**: Control each turn with arrow keys
- **Autoplay Mode**: Automatic turn progression (configurable delay in `config.json`)

### Game End Conditions

The simulation ends when:
- ❌ All vehicles are destroyed
- ✅ All items are collected
- 🚫 No reachable items remain

### Statistics

After each game, a **CSV file** is generated in the save folder with:
- Final scores and winner
- Strategy efficiency comparison
- Items collected per team
- Vehicle losses and collision data
- Turn-by-turn progression

---

## 🎨 Credits

### Development Team
- **Project**: Educational implementation for Algorithms and Data Structures 2
- **Institution**: Facultad de Ingenieria - UNCUYO
- **Year**: 2025

### Assets & Resources

This project uses graphics and audio assets from various sources:

#### Graphics
- **Sprites**: Custom pixel art and open-source game assets
- **Icons**: Game icons from community resources
- **UI Elements**: Minecraft-inspired font and interface elements

#### Audio
- **Sound Effects**: 
  - Unload sound effects
  - Victory/game over audio
- **Font**: Minecraft TTF font for retro gaming aesthetic

---

## 📂 Project Structure

```
rescue-simulator/
├── assets/              # Graphics, sounds, and fonts
├── classes/             # Game entities (Vehicle, Mine, Item, Player)
├── saves/               # Game save files and statistics
├── map_manager.py       # Core game logic and state management
├── strategies.py        # AI strategy implementations
├── pathfinding.py       # BFS pathfinding algorithms
├── visualization.py     # Pygame rendering and UI
├── rescue_simulator.py  # Main entry point
├── config.json          # Game configuration
└── requirements.txt     # Python dependencies
```

---

## 🏆 Strategy Guide

### Available Strategies

1. **PickNearest** - Goes for the closest item (default behavior)
2. **Kamikaze** - Aggressive, ignores danger zones
3. **Escort** - Follows teammates for coordinated collection
4. **Invader** - Targets enemy territory items
5. **FullSafe** - Conservative, avoids all dangers including G1 mines

Each strategy's efficiency is tracked and compared in the final statistics report!

---

## 📊 Configuration

Edit `config.json` to customize:
- Grid size and cell dimensions
- Autoplay speed
- Vehicle strategies

---

## 📝 License

This project is developed for **educational purposes only** as part of an academic course.

---