"""
utils/cover_manager.py
-----------------------
Handles copying user-picked cover images into the project's assets folder
and generating placeholder cover art (a colored tile with the game's
initial) when no cover image is provided.
"""

import os
import shutil
import hashlib
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "covers"
)

# A small palette of pleasant dark-mode tile colors used for placeholder
# covers, chosen to fit comfortably alongside the app's Steam-like theme.
PLACEHOLDER_COLORS = [
    "#3d5875", "#5c3d75", "#75503d", "#3d7558",
    "#75383d", "#39577e", "#6b3d75", "#3d6c75",
]


def ensure_assets_dir():
    os.makedirs(ASSETS_DIR, exist_ok=True)


def copy_cover_image(source_path: str, game_title: str) -> str:
    """
    Copy a user-selected image file into the assets/covers folder and
    return the new relative path to store in the database.
    """
    ensure_assets_dir()
    ext = os.path.splitext(source_path)[1].lower() or ".png"
    safe_name = "".join(c for c in game_title if c.isalnum() or c in (" ", "_")).strip()
    safe_name = safe_name.replace(" ", "_") or "game"
    dest_filename = f"{safe_name}_{abs(hash(source_path)) % 10000}{ext}"
    dest_path = os.path.join(ASSETS_DIR, dest_filename)
    shutil.copyfile(source_path, dest_path)
    return dest_path


def _color_for_title(title: str) -> str:
    """Deterministically pick a placeholder color based on the title text."""
    idx = int(hashlib.md5(title.encode("utf-8")).hexdigest(), 16) % len(PLACEHOLDER_COLORS)
    return PLACEHOLDER_COLORS[idx]


def make_placeholder_pixmap(title: str, width: int = 200, height: int = 280) -> QPixmap:
    """Generate a placeholder cover: a colored tile with the game's initial."""
    pixmap = QPixmap(width, height)
    color = QColor(_color_for_title(title or "G"))
    pixmap.fill(color)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Initial letter, large and centered
    letter = (title.strip()[0].upper() if title.strip() else "G")
    painter.setPen(QColor(255, 255, 255, 235))
    font = QFont("Segoe UI", int(height * 0.32))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, letter)

    painter.end()
    return pixmap


def load_cover_pixmap(cover_path: str, title: str, width: int = 200, height: int = 280) -> QPixmap:
    """
    Load the stored cover image if it exists; otherwise generate a
    placeholder tile so the UI never shows a broken image.
    """
    if cover_path and os.path.exists(cover_path):
        pixmap = QPixmap(cover_path)
        if not pixmap.isNull():
            return pixmap.scaled(
                width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    return make_placeholder_pixmap(title, width, height)
