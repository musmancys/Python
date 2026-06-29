"""
dialogs.py
----------
Logic classes for the two pop-up dialogs used by the app:

  GameDialog        - Add / Edit a game's details (wraps ui/game_dialog.ui)
  AchievementDialog - View / add / remove achievements for a game
                       (wraps ui/achievement_dialog.ui)

Each class loads its compiled Ui_* class (generated from the .ui file by
pyuic5) and wires up signals/slots and data binding in plain Python.
"""

import os
from PyQt5.QtWidgets import QDialog, QFileDialog, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt

from ui.game_dialog_ui import Ui_GameDialog
from ui.achievement_dialog_ui import Ui_AchievementDialog
from utils.cover_manager import copy_cover_image, load_cover_pixmap


class GameDialog(QDialog):
    """Dialog for adding a new game or editing an existing one."""

    def __init__(self, parent=None, game_row=None):
        super().__init__(parent)
        self.ui = Ui_GameDialog()
        self.ui.setupUi(self)

        self.game_row = game_row          # sqlite3.Row if editing, else None
        self.selected_cover_path = ""     # absolute path to chosen cover image

        self.ui.saveBtn.clicked.connect(self.on_save)
        self.ui.cancelBtn.clicked.connect(self.reject)
        self.ui.browseCoverBtn.clicked.connect(self.on_browse_cover)

        if self.game_row is not None:
            self._populate_from_row()
            self.setWindowTitle("Edit Game")
            self.ui.dialogTitleLabel.setText("Edit Game")
            self.ui.saveBtn.setText("Save Changes")
        else:
            self._show_cover_preview("", "")

    # ------------------------------------------------------------------ #
    def _populate_from_row(self):
        row = self.game_row
        self.ui.titleEdit.setText(row["title"])
        self.ui.developerEdit.setText(row["developer"] or "")
        self._set_combo_text(self.ui.genreCombo, row["genre"])
        self._set_combo_text(self.ui.platformCombo, row["platform"])
        self._set_combo_text(self.ui.statusCombo, row["status"])
        self.ui.releaseYearSpin.setValue(row["release_year"] or 2024)
        self.ui.playtimeSpin.setValue(row["playtime_hours"] or 0)
        self.ui.ratingSpin.setValue(row["rating"] or 0)
        self.ui.priceSpin.setValue(row["price"] or 0)
        self.ui.favoriteCheck.setChecked(bool(row["is_favorite"]))
        self.ui.wishlistCheck.setChecked(bool(row["is_wishlist"]))
        self.ui.reviewEdit.setPlainText(row["review"] or "")
        self.selected_cover_path = row["cover_path"] or ""
        self._show_cover_preview(self.selected_cover_path, row["title"])

    @staticmethod
    def _set_combo_text(combo, text):
        idx = combo.findText(text)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        else:
            combo.setEditText(text or "")

    def _show_cover_preview(self, cover_path, title):
        pixmap = load_cover_pixmap(cover_path, title or "?", 150, 210)
        self.ui.coverPreviewLabel.setPixmap(pixmap)

    # ------------------------------------------------------------------ #
    def on_browse_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Cover Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.selected_cover_path = path
            self._show_cover_preview(path, self.ui.titleEdit.text())

    def on_save(self):
        title = self.ui.titleEdit.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing Title",
                                 "Please enter a game title before saving.")
            self.ui.titleEdit.setFocus()
            return
        self.accept()

    def get_data(self) -> dict:
        """Collect form values into a dict ready for database.add_game/update_game."""
        cover_path = self.selected_cover_path
        title = self.ui.titleEdit.text().strip()

        # If the user picked a new image file (not already inside our
        # assets folder), copy it in now so it survives even if the
        # original file is moved or deleted later.
        if cover_path and "assets" + os.sep + "covers" not in cover_path:
            try:
                cover_path = copy_cover_image(cover_path, title)
            except OSError:
                pass  # fall back to no cover rather than crash

        return {
            "title": title,
            "developer": self.ui.developerEdit.text().strip(),
            "genre": self.ui.genreCombo.currentText().strip() or "Other",
            "platform": self.ui.platformCombo.currentText().strip() or "PC",
            "status": self.ui.statusCombo.currentText(),
            "release_year": self.ui.releaseYearSpin.value(),
            "playtime_hours": self.ui.playtimeSpin.value(),
            "rating": self.ui.ratingSpin.value(),
            "price": self.ui.priceSpin.value(),
            "is_favorite": self.ui.favoriteCheck.isChecked(),
            "is_wishlist": self.ui.wishlistCheck.isChecked(),
            "review": self.ui.reviewEdit.toPlainText().strip(),
            "cover_path": cover_path,
        }


class AchievementDialog(QDialog):
    """Dialog for viewing and managing a game's achievement list."""

    def __init__(self, parent, db, game_id, game_title):
        super().__init__(parent)
        self.ui = Ui_AchievementDialog()
        self.ui.setupUi(self)

        self.db = db
        self.game_id = game_id
        self.setWindowTitle(f"Achievements — {game_title}")
        self.ui.achGameTitleLabel.setText(f"🏆  Achievements — {game_title}")

        self.ui.addAchBtn.clicked.connect(self.on_add_achievement)
        self.ui.removeAchBtn.clicked.connect(self.on_remove_achievement)
        self.ui.closeAchBtn.clicked.connect(self.accept)
        self.ui.achListWidget.itemChanged.connect(self.on_item_toggled)

        self.refresh()

    # ------------------------------------------------------------------ #
    def refresh(self):
        self.ui.achListWidget.blockSignals(True)
        self.ui.achListWidget.clear()

        achievements = self.db.get_achievements(self.game_id)
        for ach in achievements:
            label = ach["name"]
            if ach["description"]:
                label += f"  —  {ach['description']}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, ach["id"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if ach["unlocked"] else Qt.Unchecked)
            self.ui.achListWidget.addItem(item)

        self.ui.achListWidget.blockSignals(False)

        unlocked, total = self.db.achievement_progress(self.game_id)
        pct = int((unlocked / total) * 100) if total else 0
        self.ui.achProgressBar.setMaximum(100)
        self.ui.achProgressBar.setValue(pct)
        self.ui.achProgressBar.setFormat(f"{unlocked} / {total} unlocked ({pct}%)")

    # ------------------------------------------------------------------ #
    def on_add_achievement(self):
        name = self.ui.newAchNameEdit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name",
                                 "Please enter an achievement name.")
            return
        description = self.ui.newAchDescEdit.text().strip()
        self.db.add_achievement(self.game_id, name, description, unlocked=False)
        self.ui.newAchNameEdit.clear()
        self.ui.newAchDescEdit.clear()
        self.refresh()

    def on_remove_achievement(self):
        item = self.ui.achListWidget.currentItem()
        if not item:
            QMessageBox.information(self, "Nothing Selected",
                                     "Select an achievement to remove first.")
            return
        ach_id = item.data(Qt.UserRole)
        self.db.delete_achievement(ach_id)
        self.refresh()

    def on_item_toggled(self, item: QListWidgetItem):
        ach_id = item.data(Qt.UserRole)
        unlocked = item.checkState() == Qt.Checked
        self.db.toggle_achievement(ach_id, unlocked)
        self.refresh()
