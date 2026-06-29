# 🎮 Game Library Manager

A desktop application for organizing and tracking your personal video game
collection — built with **Python**, **PyQt5**, and **SQLite**. Inspired by
Steam's library interface: game covers, favorites, a wishlist, achievements,
ratings, reviews, and a statistics dashboard.

---

## Features

| Feature | Description |
|---|---|
| 📚 Game Management | Add, edit, delete, and view full details for each game |
| 🔍 Search & Filter | Search by title, filter by genre or status |
| ⏱ Playtime Tracking | Record and update hours played per game |
| ⭐ Rating System | Rate games 1–10 |
| 📝 Reviews | Write personal notes/reviews per game |
| ❤ Favorites | Mark and view favorite games separately |
| ⭐ Wishlist | Track games you want to buy (Steam-style) |
| 🏆 Achievements | Add custom achievements per game and track unlock progress |
| 🖼 Game Covers | Add a custom cover image, or get an auto-generated placeholder |
| 📊 Statistics Dashboard | Total games, total playtime, highest rated, most played, genre breakdown |
| 💾 SQLite Storage | All data is saved permanently in a local `.db` file |

---

## Project Structure

```
GameLibraryManager/
├── main.py                      # Application entry point — run this file
├── main_window.py                # Main window logic (connects UI to database)
├── dialogs.py                     # Add/Edit Game dialog + Achievements dialog logic
├── database.py                     # All SQLite database code (SQL lives only here)
├── requirements.txt
├── README.md
│
├── ui/                              # Everything related to the GUI
│   ├── main_window.ui                # ⭐ Qt Designer source file — open THIS in Qt Designer
│   ├── main_window_ui.py              # Auto-generated from main_window.ui (do not edit by hand)
│   ├── game_dialog.ui                  # Qt Designer source for the Add/Edit Game dialog
│   ├── game_dialog_ui.py                # Auto-generated from game_dialog.ui
│   ├── achievement_dialog.ui             # Qt Designer source for the Achievements dialog
│   ├── achievement_dialog_ui.py           # Auto-generated from achievement_dialog.ui
│   └── style.qss                           # Steam-style dark theme stylesheet
│
├── utils/
│   └── cover_manager.py             # Handles cover image copying + placeholder generation
│
├── assets/
│   ├── covers/                      # Cover images you add get copied here
│   ├── achievements/                # (reserved for achievement icons, optional)
│   └── icons/                       # (reserved for app icons, optional)
│
└── data/
    └── game_library.db              # Created automatically on first run — your saved data
```

---

## Setup & Run

**1. Install Python 3.8+** if you don't already have it.

**2. Install the one dependency (PyQt5):**

```bash
pip install -r requirements.txt
```

**3. Run the app:**

```bash
python main.py
```

That's it — a window opens, and a `data/game_library.db` SQLite file is
created automatically the first time you run it. Every game, review,
rating, and achievement you add is saved there permanently, even after
you close the app.

---

## Editing the GUI in Qt Designer

The **`.ui` files inside the `ui/` folder are the real Qt Designer source
files** — open them directly in Qt Designer (or Qt Creator's design mode)
to visually edit the layout:

- `ui/main_window.ui` — the main library window (sidebar, game grid, stats page)
- `ui/game_dialog.ui` — the Add/Edit Game popup form
- `ui/achievement_dialog.ui` — the Achievements popup

After editing a `.ui` file in Qt Designer and saving it, **regenerate its
matching `_ui.py` file** so the app picks up your changes:

```bash
pyuic5 ui/main_window.ui -o ui/main_window_ui.py
pyuic5 ui/game_dialog.ui -o ui/game_dialog_ui.py
pyuic5 ui/achievement_dialog.ui -o ui/achievement_dialog_ui.py
```

(`pyuic5` is installed automatically alongside PyQt5.)

**Never hand-edit the `*_ui.py` files** — they get fully overwritten every
time you regenerate them from the `.ui` source. All custom behavior (what
happens when you click a button, how data loads, etc.) lives in
`main_window.py` and `dialogs.py` instead, which import the generated
`Ui_*` classes and attach logic to them. This separation is exactly why you
can freely redesign the look in Qt Designer without ever touching the
application logic.

---

## Customizing the Look

The dark Steam-style theme lives entirely in `ui/style.qss` — a plain Qt
stylesheet (CSS-like syntax). Colors, fonts, border-radius, hover effects,
etc. can all be tweaked there without touching any Python or `.ui` files.

---

## Notes on the Database

- All data lives in `data/game_library.db`, a single SQLite file.
- Two tables: `games` (one row per game) and `achievements` (linked to a
  game by `game_id`, with cascading delete — removing a game also removes
  its achievements).
- To start over with a clean library, simply delete `data/game_library.db`
  — a fresh empty one is created automatically the next time you run the app.
- To back up your library, just copy that one `.db` file somewhere safe.
