"""
main_window.py
--------------
Application logic for the main window. This file imports the *generated*
Ui_MainWindow class (ui/main_window_ui.py, produced from ui/main_window.ui
by pyuic5) and attaches behavior to it: populating the game grid, handling
navigation between pages, search/filtering, and the statistics dashboard.

This is the file to extend with new features — never edit
ui/main_window_ui.py directly, since pyuic5 regenerates it from the .ui
file and any manual edits would be lost.
"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QFrame, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QSizePolicy, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from ui.main_window_ui import Ui_MainWindow
from database import GameDatabase
from dialogs import GameDialog, AchievementDialog
from utils.cover_manager import load_cover_pixmap

GENRES = ["Action", "RPG", "Adventure", "Strategy", "Shooter",
          "Platformer", "Simulation", "Sports", "Puzzle", "Horror", "Other"]
STATUSES = ["Not Started", "Playing", "Completed", "On Hold", "Dropped"]

STATUS_COLORS = {
    "Not Started": "#8f98a0",
    "Playing": "#66c0f4",
    "Completed": "#a4d007",
    "On Hold": "#e1a94c",
    "Dropped": "#c0392b",
}

CARD_WIDTH = 220
COVER_WIDTH = 200
COVER_HEIGHT = 230


class GameCard(QFrame):
    """A single Steam-style card widget representing one game in the grid."""

    def __init__(self, game_row, on_edit, on_delete, on_toggle_fav, on_achievements):
        super().__init__()
        self.game_id = game_row["id"]
        self.game_row = game_row
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_toggle_fav = on_toggle_fav
        self.on_achievements = on_achievements

        self.setObjectName("gameCard")
        self.setFixedWidth(CARD_WIDTH)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # --- Cover image -------------------------------------------------
        self.cover_label = QLabel()
        self.cover_label.setObjectName("cardCoverLabel")
        self.cover_label.setFixedSize(COVER_WIDTH, COVER_HEIGHT)
        self.cover_label.setAlignment(Qt.AlignCenter)
        pixmap = load_cover_pixmap(game_row["cover_path"], game_row["title"],
                                    COVER_WIDTH, COVER_HEIGHT)
        self.cover_label.setPixmap(pixmap)
        layout.addWidget(self.cover_label)

        # --- Title + favorite row ----------------------------------------
        title_row = QHBoxLayout()
        title_label = QLabel(game_row["title"])
        title_label.setObjectName("cardTitleLabel")
        title_label.setWordWrap(True)
        title_row.addWidget(title_label, 1)

        self.fav_btn = QPushButton("❤" if game_row["is_favorite"] else "♡")
        self.fav_btn.setObjectName("cardFavBtn")
        self.fav_btn.setFixedWidth(28)
        self.fav_btn.setToolTip("Toggle favorite")
        self.fav_btn.clicked.connect(self._toggle_fav)
        title_row.addWidget(self.fav_btn)
        layout.addLayout(title_row)

        # --- Meta line: genre · platform ----------------------------------
        meta_label = QLabel(f"{game_row['genre']}  ·  {game_row['platform']}")
        meta_label.setObjectName("cardMetaLabel")
        layout.addWidget(meta_label)

        # --- Status badge + rating row -------------------------------------
        badge_row = QHBoxLayout()
        status = game_row["status"]
        if not game_row["is_wishlist"]:
            status_badge = QLabel(status)
            status_badge.setObjectName("cardStatusBadge")
            color = STATUS_COLORS.get(status, "#8f98a0")
            status_badge.setStyleSheet(f"background-color: {color};")
            badge_row.addWidget(status_badge)
        else:
            wishlist_badge = QLabel("WISHLIST")
            wishlist_badge.setObjectName("cardStatusBadge")
            wishlist_badge.setStyleSheet("background-color: #e1a94c;")
            badge_row.addWidget(wishlist_badge)

        badge_row.addStretch()

        if not game_row["is_wishlist"] and game_row["rating"]:
            rating_label = QLabel(f"★ {game_row['rating']}/10")
            rating_label.setObjectName("cardRatingLabel")
            badge_row.addWidget(rating_label)
        layout.addLayout(badge_row)

        # --- Playtime line ---------------------------------------------------
        if not game_row["is_wishlist"]:
            playtime_label = QLabel(f"⏱  {game_row['playtime_hours']:g} hrs played")
            playtime_label.setObjectName("cardMetaLabel")
            layout.addWidget(playtime_label)

        # --- Action buttons row ----------------------------------------------
        actions_row = QHBoxLayout()
        actions_row.setSpacing(4)

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("cardEditBtn")
        edit_btn.clicked.connect(lambda: self.on_edit(self.game_id))
        actions_row.addWidget(edit_btn)

        if not game_row["is_wishlist"]:
            ach_btn = QPushButton("🏆")
            ach_btn.setObjectName("cardAchBtn")
            ach_btn.setToolTip("Achievements")
            ach_btn.clicked.connect(lambda: self.on_achievements(self.game_id, self.game_row["title"]))
            actions_row.addWidget(ach_btn)

        delete_btn = QPushButton("✕")
        delete_btn.setObjectName("cardDeleteBtn")
        delete_btn.setToolTip("Delete game")
        delete_btn.clicked.connect(lambda: self.on_delete(self.game_id, self.game_row["title"]))
        actions_row.addWidget(delete_btn)

        layout.addLayout(actions_row)

    def _toggle_fav(self):
        self.on_toggle_fav(self.game_id)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.db = GameDatabase()
        self.current_view = "all"   # 'all' | 'favorites' | 'wishlist' | 'stats'

        self._load_stylesheet()
        self._setup_filters()
        self._connect_signals()
        self.refresh_view()

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #
    def _load_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "ui", "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _setup_filters(self):
        self.ui.genreFilterCombo.clear()
        self.ui.genreFilterCombo.addItem("All Genres")
        self.ui.genreFilterCombo.addItems(GENRES)

        self.ui.statusFilterCombo.clear()
        self.ui.statusFilterCombo.addItem("All Statuses")
        self.ui.statusFilterCombo.addItems(STATUSES)

    def _connect_signals(self):
        self.ui.navAllGamesBtn.clicked.connect(lambda: self._switch_view("all"))
        self.ui.navFavoritesBtn.clicked.connect(lambda: self._switch_view("favorites"))
        self.ui.navWishlistBtn.clicked.connect(lambda: self._switch_view("wishlist"))
        self.ui.navStatsBtn.clicked.connect(lambda: self._switch_view("stats"))

        self.ui.addGameBtn.clicked.connect(self.on_add_game)
        self.ui.searchBar.textChanged.connect(self.refresh_view)
        self.ui.genreFilterCombo.currentIndexChanged.connect(self.refresh_view)
        self.ui.statusFilterCombo.currentIndexChanged.connect(self.refresh_view)

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #
    def _switch_view(self, view_name):
        self.current_view = view_name

        for btn, name in [
            (self.ui.navAllGamesBtn, "all"),
            (self.ui.navFavoritesBtn, "favorites"),
            (self.ui.navWishlistBtn, "wishlist"),
            (self.ui.navStatsBtn, "stats"),
        ]:
            btn.setChecked(name == view_name)

        titles = {
            "all": "All Games",
            "favorites": "Favorites",
            "wishlist": "Wishlist",
            "stats": "Statistics",
        }
        self.ui.pageTitleLabel.setText(titles[view_name])

        is_stats = (view_name == "stats")
        self.ui.stackedWidget.setCurrentIndex(1 if is_stats else 0)
        self.ui.searchBar.setVisible(not is_stats)
        self.ui.genreFilterCombo.setVisible(not is_stats and view_name != "wishlist")
        self.ui.statusFilterCombo.setVisible(not is_stats and view_name != "wishlist")

        self.refresh_view()

    # ------------------------------------------------------------------ #
    # Data refresh
    # ------------------------------------------------------------------ #
    def refresh_view(self):
        if self.current_view == "stats":
            self._render_stats()
        else:
            self._render_library_grid()

    def _get_games_for_current_view(self):
        keyword = self.ui.searchBar.text().strip()
        genre = self.ui.genreFilterCombo.currentText() if self.ui.genreFilterCombo.currentIndex() > 0 else "All"
        status = self.ui.statusFilterCombo.currentText() if self.ui.statusFilterCombo.currentIndex() > 0 else "All"

        if self.current_view == "favorites":
            games = self.db.get_favorite_games()
            if keyword:
                games = [g for g in games if keyword.lower() in g["title"].lower()]
            return games

        if self.current_view == "wishlist":
            games = self.db.get_wishlist_games()
            if keyword:
                games = [g for g in games if keyword.lower() in g["title"].lower()]
            return games

        # "all"
        return self.db.search_games(keyword=keyword, genre=genre, status=status,
                                     include_wishlist=False)

    def _render_library_grid(self):
        grid = self.ui.gameGridLayout
        self._clear_layout(grid)

        games = self._get_games_for_current_view()

        if not games:
            empty_label = QLabel(self._empty_message())
            empty_label.setObjectName("cardMetaLabel")
            empty_label.setAlignment(Qt.AlignCenter)
            grid.addWidget(empty_label, 0, 0)
            return

        columns = 4
        for index, game_row in enumerate(games):
            card = GameCard(
                game_row,
                on_edit=self.on_edit_game,
                on_delete=self.on_delete_game,
                on_toggle_fav=self.on_toggle_favorite,
                on_achievements=self.on_open_achievements,
            )
            row, col = divmod(index, columns)
            grid.addWidget(card, row, col, alignment=Qt.AlignTop)

    def _empty_message(self):
        return {
            "all": "No games yet. Click '＋ Add Game' to build your library.",
            "favorites": "No favorites yet. Mark a game with ❤ to see it here.",
            "wishlist": "Your wishlist is empty. Add a game and check 'Add to Wishlist'.",
        }.get(self.current_view, "Nothing to show.")

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    # ------------------------------------------------------------------ #
    # Statistics dashboard
    # ------------------------------------------------------------------ #
    def _render_stats(self):
        stats = self.db.get_statistics()

        grid = self.ui.statCardsGridLayout
        self._clear_layout(grid)

        cards = [
            ("Total Games", str(stats["total_games"]), "📚"),
            ("Total Playtime", f"{stats['total_playtime']:g} hrs", "⏱"),
            ("Highest Rated", f"{stats['highest_rated'][0]}\n({stats['highest_rated'][1]}/10)", "⭐"),
            ("Most Played", f"{stats['most_played'][0]}\n({stats['most_played'][1]:g} hrs)", "🔥"),
            ("Favorites", str(stats["total_favorites"]), "❤"),
            ("Wishlist Items", str(stats["total_wishlist"]), "🛒"),
            ("Achievements Unlocked",
             f"{stats['achievements_unlocked']} / {stats['achievements_total']}", "🏆"),
        ]

        columns = 4
        for index, (label, value, icon) in enumerate(cards):
            card = self._build_stat_card(label, value, icon)
            row, col = divmod(index, columns)
            grid.addWidget(card, row, col)

        self._render_genre_breakdown(stats["genre_breakdown"], stats["total_games"])

    @staticmethod
    def _build_stat_card(label, value, icon):
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumSize(230, 110)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        icon_value_row = QHBoxLayout()
        value_label = QLabel(f"{icon}  {value}")
        value_label.setObjectName("statValueLabel")
        value_label.setWordWrap(True)
        icon_value_row.addWidget(value_label)
        layout.addLayout(icon_value_row)

        title_label = QLabel(label.upper())
        title_label.setObjectName("statLabel")
        layout.addWidget(title_label)
        layout.addStretch()
        return card

    def _render_genre_breakdown(self, genre_breakdown: dict, total_games: int):
        layout = self.ui.genreBreakdownLayout

        # Remove every row after the title (index 0) before re-rendering.
        while layout.count() > 1:
            item = layout.takeAt(1)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        if not genre_breakdown:
            empty = QLabel("Add some games to see your genre breakdown.")
            empty.setObjectName("cardMetaLabel")
            layout.addWidget(empty)
            return

        for genre, count in genre_breakdown.items():
            row = QHBoxLayout()
            row.setSpacing(12)
            label = QLabel(f"{genre}  ({count})")
            label.setObjectName("genreBarLabel")
            label.setMinimumWidth(150)
            row.addWidget(label)

            bar = QProgressBar()
            bar.setMinimumHeight(18)
            bar.setMaximum(total_games if total_games else 1)
            bar.setValue(count)
            bar.setFormat("")
            row.addWidget(bar, 1)

            layout.addLayout(row)

    # ------------------------------------------------------------------ #
    # Actions: add / edit / delete / favorite / achievements
    # ------------------------------------------------------------------ #
    def on_add_game(self):
        dialog = GameDialog(self)
        if dialog.exec_() == GameDialog.Accepted:
            data = dialog.get_data()
            self.db.add_game(data)
            self.refresh_view()

    def on_edit_game(self, game_id):
        row = self.db.get_game(game_id)
        if row is None:
            return
        dialog = GameDialog(self, game_row=row)
        if dialog.exec_() == GameDialog.Accepted:
            data = dialog.get_data()
            self.db.update_game(game_id, data)
            self.refresh_view()

    def on_delete_game(self, game_id, title):
        reply = QMessageBox.question(
            self, "Delete Game",
            f"Are you sure you want to delete \"{title}\"? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_game(game_id)
            self.refresh_view()

    def on_toggle_favorite(self, game_id):
        row = self.db.get_game(game_id)
        if row is None:
            return
        data = dict(row)
        data["is_favorite"] = not bool(row["is_favorite"])
        self.db.update_game(game_id, data)
        self.refresh_view()

    def on_open_achievements(self, game_id, title):
        dialog = AchievementDialog(self, self.db, game_id, title)
        dialog.exec_()
        self.refresh_view()

    # ------------------------------------------------------------------ #
    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
