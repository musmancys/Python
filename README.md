# 🎮 Game Library Manager & 🎲 Tic Tac Toe

A small collection of Python projects — a full desktop app for tracking a personal game collection, and a classic console-based Tic Tac Toe game.

## Author

| Field | Details |
|-------|---------|
| **Name** | Muhammad Usman |
| **GitHub** | [musmancys](https://github.com/musmancys) |

---

## Projects

### 🎮 Game Library Manager
**Folder:** [GameLibraryManager](./GameLibraryManager/)

A desktop application for organizing and tracking a personal video game collection, built with **Python**, **PyQt4**, and **SQLite**. Inspired by Steam's library interface.

**Features:**
- Game management (add, edit, delete, view full details)
- Search and filter by title, genre, or status
- Playtime tracking and 0–10 rating system
- Personal reviews/notes per game
- Favorites and a Steam-style wishlist
- Custom achievements per game with unlock tracking
- Game cover images (custom or auto-generated placeholders)
- Statistics dashboard (total games, playtime, top rated, genre breakdown)
- Persistent storage via SQLite

**Tech Used:** Python 2, PyQt5, SQLite, Qt Designer

**Run it:**
```bash
cd GameLibraryManager
pip install -r requirements.txt
python main.py
```

---

### 🎲 Tic Tac Toe

**Folder:** [Tic_Tac_Toe_Game.py](./Tic_Tac_Toe_Game.py)

A console-based Tic Tac Toe game where the player (`O`) takes on the computer (`X`), which starts by claiming the center square and then plays the rest of its moves randomly.

**Features:**
- Text-based board rendered directly in the terminal
- Input validation (rejects out-of-range or already-occupied cells)
- Win detection across rows, columns, and both diagonals
- Random computer opponent
- Game-end messages for win, loss, or tie

**Tech Used:** Python 2 (standard library only — `random`)

**Run it:**
```bash
python "Tic_Tac_Toe_Game.py"
```

---

## Tools & Technologies

- **Language:** Python 2
- **Editor:** VS Code
- **Version Control:** Git & GitHub

---

*Muhammad Usman | [github.com/musmancys](https://github.com/musmancys)*
