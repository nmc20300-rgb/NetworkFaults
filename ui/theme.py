"""
Design System & Central Theme for Network Faults Management System
نظام إدارة الأجهزة والأعطال - الشبكة
Standardizes primary colors, branding tokens, typography, and stylesheets.
"""

class Theme:
    # ── Primary Branding Colors (Pro Cyan/Teal Tech Identity) ────────────────
    # Primary Action (Buttons, active tabs, progress bars, key accents)
    PRIMARY = "#0891b2"
    PRIMARY_HOVER = "#0e7490"
    PRIMARY_PRESSED = "#155e75"
    PRIMARY_LIGHT = "#e0f2fe"       # Soft tint for badges, selected rows
    PRIMARY_LIGHT_HOVER = "#bae6fd"
    PRIMARY_BORDER = "#38bdf8"      # Glow borders, focus rings
    PRIMARY_GLOW = "#26c6da"       # Vibrant accent matching sidebar & login

    # ── Navy Slate System (Authoritative Headers & Dark Surfaces) ────────────
    NAVY_DARK = "#0f2338"          # Page titles, primary dark text
    NAVY_SURFACE = "#152c42"       # Dialog headers, dark panels
    NAVY_SURFACE_HOVER = "#1d3a54"
    NAVY_BORDER = "#224364"        # Dark borders
    NAVY_SUBTLE = "#1e3a52"

    # ── Neutrals & Surfaces (Clean Light Enterprise Mode) ────────────────────
    BG_PAGE = "#f4f7fb"            # Base canvas background
    BG_CARD = "#ffffff"            # Card surfaces
    BG_INPUT = "#fbfdff"           # Inputs, selects
    BG_HOVER = "#f1f5f9"           # Hover on secondary elements
    BORDER_LIGHT = "#e2e8f0"       # Card / container borders
    BORDER_INPUT = "#cbd5e1"       # Input field borders
    BORDER_FOCUS = "#0891b2"       # Input active/focus border

    # ── Typography Colors ────────────────────────────────────────────────────
    TEXT_MAIN = "#0f2338"          # Headings & main text
    TEXT_BODY = "#334155"          # Body & table text
    TEXT_MUTED = "#64748b"         # Subtitles, labels, hints
    TEXT_LIGHT = "#94a3b8"         # Placeholders & timestamps
    TEXT_WHITE = "#ffffff"         # Contrast white

    # ── Functional Semantic Colors ───────────────────────────────────────────
    SUCCESS = "#10b981"
    SUCCESS_LIGHT = "#ecfdf5"
    SUCCESS_BORDER = "#a7f3d0"
    SUCCESS_TEXT = "#065f46"

    WARNING = "#f59e0b"
    WARNING_LIGHT = "#fffbeb"
    WARNING_BORDER = "#fde68a"
    WARNING_TEXT = "#92400e"

    DANGER = "#ef4444"
    DANGER_LIGHT = "#fef2f2"
    DANGER_BORDER = "#fecaca"
    DANGER_TEXT = "#991b1b"

    INFO = "#3b82f6"
    INFO_LIGHT = "#eff6ff"
    INFO_BORDER = "#bfdbfe"
    INFO_TEXT = "#1e40af"

    # ── Global Stylesheet ────────────────────────────────────────────────────
    @classmethod
    def get_global_stylesheet(cls) -> str:
        return f"""
        * {{
            font-family: 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, Arial;
        }}

        QWidget {{
            color: {cls.TEXT_BODY};
            font-size: 12px;
        }}

        /* ── Focus States ────────────────────────── */
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
        QDoubleSpinBox:focus, QDateTimeEdit:focus, QTextEdit:focus,
        QPlainTextEdit:focus {{
            border: 1.5px solid {cls.PRIMARY};
            background-color: #ffffff;
        }}

        /* ── Standard Primary Buttons ────────────── */
        QPushButton#primaryButton,
        QPushButton#primary,
        QPushButton[primary="true"] {{
            background-color: {cls.PRIMARY};
            color: #ffffff;
            border: none;
            border-radius: 9px;
            padding: 9px 18px;
            font-size: 13px;
            font-weight: 700;
        }}

        QPushButton#primaryButton:hover,
        QPushButton#primary:hover,
        QPushButton[primary="true"]:hover {{
            background-color: {cls.PRIMARY_HOVER};
        }}

        QPushButton#primaryButton:pressed,
        QPushButton#primary:pressed,
        QPushButton[primary="true"]:pressed {{
            background-color: {cls.PRIMARY_PRESSED};
        }}

        /* ── Standard Secondary Buttons ──────────── */
        QPushButton#secondaryButton,
        QPushButton#secondary {{
            background-color: #f1f5f9;
            color: {cls.TEXT_MAIN};
            border: 1px solid {cls.BORDER_LIGHT};
            border-radius: 9px;
            padding: 9px 16px;
            font-size: 13px;
            font-weight: 700;
        }}

        QPushButton#secondaryButton:hover,
        QPushButton#secondary:hover {{
            background-color: #e2e8f0;
        }}

        /* ── Standard Danger Buttons ─────────────── */
        QPushButton#dangerButton,
        QPushButton#danger {{
            background-color: {cls.DANGER_LIGHT};
            color: {cls.DANGER_TEXT};
            border: 1px solid {cls.DANGER_BORDER};
            border-radius: 9px;
            padding: 9px 16px;
            font-size: 13px;
            font-weight: 700;
        }}

        QPushButton#dangerButton:hover,
        QPushButton#danger:hover {{
            background-color: #fee2e2;
        }}

        /* ── Table Styling ───────────────────────── */
        QTableWidget {{
            background: #ffffff;
            border: 1px solid {cls.BORDER_LIGHT};
            gridline-color: #f1f5f9;
            selection-background-color: {cls.PRIMARY_LIGHT};
            selection-color: {cls.NAVY_DARK};
            alternate-background-color: #f8fafc;
        }}

        QHeaderView::section {{
            background: #f8fafc;
            color: {cls.NAVY_DARK};
            border: none;
            border-bottom: 2px solid {cls.PRIMARY};
            padding: 10px 8px;
            font-weight: 700;
        }}

        /* ── Scrollbars ──────────────────────────── */
        QScrollBar:vertical {{
            border: none;
            background: #f1f5f9;
            width: 8px;
            margin: 0;
            border-radius: 4px;
        }}

        QScrollBar::handle:vertical {{
            background: #cbd5e1;
            min-height: 25px;
            border-radius: 4px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {cls.PRIMARY};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            border: none;
            background: #f1f5f9;
            height: 8px;
            margin: 0;
            border-radius: 4px;
        }}

        QScrollBar::handle:horizontal {{
            background: #cbd5e1;
            min-width: 25px;
            border-radius: 4px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {cls.PRIMARY};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* ── Standard Dialogs & MessageBoxes ────── */
        QDialog, QMessageBox {{
            background-color: #ffffff;
            color: #0f2338;
        }}

        QMessageBox QLabel {{
            color: #0f2338;
            font-size: 13px;
            font-weight: 500;
            min-height: 38px;
        }}

        QDialogButtonBox QPushButton, QMessageBox QPushButton {{
            min-width: 80px;
            min-height: 34px;
            padding: 6px 16px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 12px;
            background-color: #f1f5f9;
            color: #0f2338;
            border: 1px solid #cbd5e1;
        }}

        QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover {{
            background-color: #e2e8f0;
            border-color: #94a3b8;
        }}

        QDialogButtonBox QPushButton:default, QMessageBox QPushButton:default {{
            background-color: {cls.PRIMARY};
            color: #ffffff;
            border: 1px solid {cls.PRIMARY};
        }}

        QDialogButtonBox QPushButton:default:hover, QMessageBox QPushButton:default:hover {{
            background-color: {cls.PRIMARY_HOVER};
        }}
        """
