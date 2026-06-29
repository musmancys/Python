"""
database.py
-----------
SQLite data-access layer for the Game Library Manager.

Every read/write to the database goes through the GameDatabase class.
Keeping all SQL in one place makes the rest of the app (UI code) free
of SQL strings and easy to maintain.
"""

import sqlite3
import os
from datetime import datetime

# The .db file lives inside the data/ folder so the project root stays clean.
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "game_library.db")


class GameDatabase:
    """Handles every interaction with the SQLite database."""

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(DB_DIR, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    # ------------------------------------------------------------------ #
    # Schema
    # ------------------------------------------------------------------ #
    def _create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT    NOT NULL,
                genre           TEXT    DEFAULT 'Other',
                platform        TEXT    DEFAULT 'PC',
                status          TEXT    DEFAULT 'Not Started',
                rating          INTEGER DEFAULT 0,
                playtime_hours  REAL    DEFAULT 0,
                review          TEXT    DEFAULT '',
                is_favorite     INTEGER DEFAULT 0,
                is_wishlist     INTEGER DEFAULT 0,
                cover_path      TEXT    DEFAULT '',
                release_year    INTEGER DEFAULT 0,
                developer       TEXT    DEFAULT '',
                price           REAL    DEFAULT 0,
                date_added      TEXT    DEFAULT '',
                last_played     TEXT    DEFAULT ''
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id     INTEGER NOT NULL,
                name        TEXT    NOT NULL,
                description TEXT    DEFAULT '',
                unlocked    INTEGER DEFAULT 0,
                date_unlocked TEXT  DEFAULT '',
                FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Games: CRUD
    # ------------------------------------------------------------------ #
    def add_game(self, data: dict) -> int:
        """Insert a new game. Returns the new game's id."""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO games
                (title, genre, platform, status, rating, playtime_hours,
                 review, is_favorite, is_wishlist, cover_path, release_year,
                 developer, price, date_added, last_played)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("title", "Untitled"),
            data.get("genre", "Other"),
            data.get("platform", "PC"),
            data.get("status", "Not Started"),
            data.get("rating", 0),
            data.get("playtime_hours", 0),
            data.get("review", ""),
            int(data.get("is_favorite", False)),
            int(data.get("is_wishlist", False)),
            data.get("cover_path", ""),
            data.get("release_year", 0),
            data.get("developer", ""),
            data.get("price", 0),
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            data.get("last_played", ""),
        ))
        self.conn.commit()
        return cur.lastrowid

    def update_game(self, game_id: int, data: dict):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE games SET
                title=?, genre=?, platform=?, status=?, rating=?,
                playtime_hours=?, review=?, is_favorite=?, is_wishlist=?,
                cover_path=?, release_year=?, developer=?, price=?,
                last_played=?
            WHERE id=?
        """, (
            data.get("title", "Untitled"),
            data.get("genre", "Other"),
            data.get("platform", "PC"),
            data.get("status", "Not Started"),
            data.get("rating", 0),
            data.get("playtime_hours", 0),
            data.get("review", ""),
            int(data.get("is_favorite", False)),
            int(data.get("is_wishlist", False)),
            data.get("cover_path", ""),
            data.get("release_year", 0),
            data.get("developer", ""),
            data.get("price", 0),
            data.get("last_played", ""),
            game_id,
        ))
        self.conn.commit()

    def delete_game(self, game_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM games WHERE id=?", (game_id,))
        self.conn.commit()

    def get_game(self, game_id: int) -> sqlite3.Row:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM games WHERE id=?", (game_id,))
        return cur.fetchone()

    def get_all_games(self, include_wishlist: bool = True) -> list:
        cur = self.conn.cursor()
        if include_wishlist:
            cur.execute("SELECT * FROM games ORDER BY title COLLATE NOCASE ASC")
        else:
            cur.execute(
                "SELECT * FROM games WHERE is_wishlist=0 ORDER BY title COLLATE NOCASE ASC")
        return cur.fetchall()

    def get_wishlist_games(self) -> list:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM games WHERE is_wishlist=1 ORDER BY title COLLATE NOCASE ASC")
        return cur.fetchall()

    def get_favorite_games(self) -> list:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM games WHERE is_favorite=1 AND is_wishlist=0 "
            "ORDER BY title COLLATE NOCASE ASC")
        return cur.fetchall()

    def search_games(self, keyword: str = "", genre: str = "All",
                      status: str = "All", include_wishlist: bool = False) -> list:
        query = "SELECT * FROM games WHERE 1=1"
        params = []

        if not include_wishlist:
            query += " AND is_wishlist=0"

        if keyword:
            query += " AND title LIKE ?"
            params.append(f"%{keyword}%")

        if genre and genre != "All":
            query += " AND genre=?"
            params.append(genre)

        if status and status != "All":
            query += " AND status=?"
            params.append(status)

        query += " ORDER BY title COLLATE NOCASE ASC"
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def touch_last_played(self, game_id: int):
        """Stamp 'now' as the last played date for a game."""
        cur = self.conn.cursor()
        cur.execute("UPDATE games SET last_played=? WHERE id=?",
                    (datetime.now().strftime("%Y-%m-%d %H:%M"), game_id))
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Achievements
    # ------------------------------------------------------------------ #
    def add_achievement(self, game_id: int, name: str, description: str = "",
                         unlocked: bool = False) -> int:
        cur = self.conn.cursor()
        date_unlocked = datetime.now().strftime("%Y-%m-%d %H:%M") if unlocked else ""
        cur.execute("""
            INSERT INTO achievements (game_id, name, description, unlocked, date_unlocked)
            VALUES (?, ?, ?, ?, ?)
        """, (game_id, name, description, int(unlocked), date_unlocked))
        self.conn.commit()
        return cur.lastrowid

    def get_achievements(self, game_id: int) -> list:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM achievements WHERE game_id=? ORDER BY id ASC", (game_id,))
        return cur.fetchall()

    def toggle_achievement(self, achievement_id: int, unlocked: bool):
        cur = self.conn.cursor()
        date_unlocked = datetime.now().strftime("%Y-%m-%d %H:%M") if unlocked else ""
        cur.execute(
            "UPDATE achievements SET unlocked=?, date_unlocked=? WHERE id=?",
            (int(unlocked), date_unlocked, achievement_id))
        self.conn.commit()

    def delete_achievement(self, achievement_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM achievements WHERE id=?", (achievement_id,))
        self.conn.commit()

    def achievement_progress(self, game_id: int) -> tuple:
        """Returns (unlocked_count, total_count) for a game."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) AS total FROM achievements WHERE game_id=?",
                    (game_id,))
        total = cur.fetchone()["total"]
        cur.execute(
            "SELECT COUNT(*) AS done FROM achievements WHERE game_id=? AND unlocked=1",
            (game_id,))
        done = cur.fetchone()["done"]
        return done, total

    # ------------------------------------------------------------------ #
    # Statistics dashboard
    # ------------------------------------------------------------------ #
    def get_statistics(self) -> dict:
        cur = self.conn.cursor()

        cur.execute("SELECT COUNT(*) AS c FROM games WHERE is_wishlist=0")
        total_games = cur.fetchone()["c"]

        cur.execute(
            "SELECT COALESCE(SUM(playtime_hours),0) AS s FROM games WHERE is_wishlist=0")
        total_playtime = cur.fetchone()["s"]

        cur.execute("""
            SELECT title, rating FROM games
            WHERE is_wishlist=0 ORDER BY rating DESC, title ASC LIMIT 1
        """)
        row = cur.fetchone()
        highest_rated = (row["title"], row["rating"]) if row and total_games else ("--", 0)

        cur.execute("""
            SELECT title, playtime_hours FROM games
            WHERE is_wishlist=0 ORDER BY playtime_hours DESC, title ASC LIMIT 1
        """)
        row = cur.fetchone()
        most_played = (row["title"], row["playtime_hours"]) if row and total_games else ("--", 0)

        cur.execute("SELECT COUNT(*) AS c FROM games WHERE is_favorite=1 AND is_wishlist=0")
        total_favorites = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM games WHERE is_wishlist=1")
        total_wishlist = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM achievements WHERE unlocked=1")
        achievements_unlocked = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM achievements")
        achievements_total = cur.fetchone()["c"]

        cur.execute("""
            SELECT genre, COUNT(*) as c FROM games
            WHERE is_wishlist=0 GROUP BY genre ORDER BY c DESC
        """)
        genre_breakdown = {r["genre"]: r["c"] for r in cur.fetchall()}

        cur.execute("""
            SELECT status, COUNT(*) as c FROM games
            WHERE is_wishlist=0 GROUP BY status
        """)
        status_breakdown = {r["status"]: r["c"] for r in cur.fetchall()}

        return {
            "total_games": total_games,
            "total_playtime": round(total_playtime, 1),
            "highest_rated": highest_rated,
            "most_played": most_played,
            "total_favorites": total_favorites,
            "total_wishlist": total_wishlist,
            "achievements_unlocked": achievements_unlocked,
            "achievements_total": achievements_total,
            "genre_breakdown": genre_breakdown,
            "status_breakdown": status_breakdown,
        }

    # ------------------------------------------------------------------ #
    def close(self):
        self.conn.close()
