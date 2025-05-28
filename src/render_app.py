#!/usr/bin/env python3
from PySide6.QtWidgets import QWidget, QLabel, QTextEdit, QCalendarWidget, QApplication, QFrame
from PySide6.QtGui import QFont, QPainter, QPixmap, QPen, QTextCharFormat, QColor, QBrush
from PySide6.QtCore import Qt, QDateTime, QDate, QTimeZone
from PySide6.QtCharts import QChart, QChartView, QSplineSeries, QValueAxis, QDateTimeAxis
import sys
import time
import os
import json

# Data Providers (assuming these are in a 'providers' subdirectory)
# Make sure these provider files exist or adjust imports as needed.
# For demonstration, I'll assume they exist and have the necessary methods.
try:
    from providers.weather_provider import WeatherProvider
    from providers.events_provider import EventsProvider
    from providers.home_status_provider import HomeStatusProvider
    from providers.notes_provider import NotesProvider
    from providers.system_info_provider import SystemInfoProvider
except ImportError:
    print("Warning: Could not import one or more provider modules. Using dummy providers.")
    # Define dummy providers if the real ones are not available for testing
    class DummyProvider:
        def __init__(self, *args, **kwargs): pass
        def start(self): pass
        def get_weather_icon(self): return "❓"
        def get_current_temperature(self): return "N/A°C"
        def get_sun_times(self): return ("N/A", "N/A")
        def get_status(self): return "Home status: N/A"
        def get_info(self): return "System info: N/A"
        def get_events(self): return []
        def get_notes_markdown(self): return "# Notes\nN/A"
        def get_highs_and_lows(self): return ([0]*5, [0]*5)
        @staticmethod
        def extract_all_dates(events): return []

    WeatherProvider = DummyProvider
    EventsProvider = DummyProvider
    HomeStatusProvider = DummyProvider
    NotesProvider = DummyProvider
    SystemInfoProvider = DummyProvider


# --- Configuration Loading ---
CONFIG_FILE_PATH = "ui_config.json"
DEFAULT_CONFIG = { # Fallback values if config.json is missing or incomplete
    "global_settings": {
        "timezone": "Europe/Amsterdam",
        "font_family": "Bookerly, sans-serif",
        "main_window_width": 800,
        "main_window_height": 480,
        "default_background_color": "white",
        "default_text_color": "black"
    },
    "eink_calendar": {
        "font_size": 12, "font_bold": True, "header_font_size": 13, "header_font_bold": True,
        "background_color": "white", "text_color": "black", "grid_visible": False,
        "vertical_header_format_none": True, "navigation_bar_visible": False,
        "current_date_fill_color": "black", "current_date_text_color": "white",
        "event_indicator_line_color": "black", "event_indicator_line_width": 2
    },
    "dashboard_elements": {
        "weather_icon": {"font_size": 90, "font_bold": True, "geometry": [5, -50, 175, 160]},
        "sun_info": {"font_size": 11, "font_bold": True, "alignment_h": "AlignLeft", "alignment_v": "AlignVCenter", "geometry": [10, 170, 240, 20]},
        "clock_label": {"font_size": 85, "font_bold": True, "alignment_h": "AlignLeft", "alignment_v": "AlignVCenter", "geometry": [190, 1, 320, 160], "time_format": "HH:mm"},
        "date_label": {"font_size": 14, "font_bold": True, "alignment_h": "AlignCenter", "alignment_v": "AlignVCenter", "geometry": [250, 135, 220, 30], "date_format": "dddd dd/MM"},
        "home_status": {"font_size": 10, "font_bold": True, "alignment_h": "AlignCenter", "alignment_v": "AlignVCenter", "geometry": [280, 176, 200, 18]},
        "chart_view": {
            "geometry": [-20, 195, 500, 285], "antialiasing": False,
            "high_series_pen": {"color": "black", "width": 4, "style": "SolidLine"},
            "low_series_pen": {"color": "black", "width": 2, "style": "DashLine"},
            "axisX": {"format": "ddd", "tick_count": 5, "grid_line_visible": False, "labels_font_size": 12, "labels_font_bold": True},
            "axisY": {"range_min": -10, "range_max": 40, "label_format": "%d°C", "grid_line_visible": False, "labels_font_size": 12, "labels_font_bold": True}
        },
        "calendar_widget_instance": {"geometry": [450, 205, 350, 280]},
        "notes_text_edit": {"font_size": 10, "font_bold": False, "geometry": [550, 5, 240, 190], "vertical_scrollbar_policy": "ScrollBarAlwaysOff", "horizontal_scrollbar_policy": "ScrollBarAlwaysOff", "frame_shape": "NoFrame"},
        "sysinfo_label": {"font_size": 8, "font_bold": False, "geometry": [10, 460, 400, 20]}
    }
}

def load_config():
    """Loads configuration from JSON file."""
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config_from_file = json.load(f)
        # Basic merge with defaults to ensure all keys are present
        # More sophisticated merging might be needed for deeply nested structures if partial configs are expected
        merged_config = DEFAULT_CONFIG.copy()
        for key, value in config_from_file.items():
            if isinstance(value, dict) and key in merged_config:
                merged_config[key].update(value)
            else:
                merged_config[key] = value
        return merged_config
    except FileNotFoundError:
        print(f"Warning: Configuration file '{CONFIG_FILE_PATH}' not found. Using default settings.")
        return DEFAULT_CONFIG
    except json.JSONDecodeError:
        print(f"Error: Could not decode '{CONFIG_FILE_PATH}'. Using default settings.")
        return DEFAULT_CONFIG

APP_CONFIG = load_config()

# Helper to get config values safely
def get_config_value(path, default=None):
    """
    Retrieves a value from the APP_CONFIG dictionary using a path.
    Example: get_config_value(['dashboard_elements', 'clock_label', 'font_size'], 85)
    """
    current = APP_CONFIG
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            # print(f"Warning: Config path '{'/'.join(path)}' not found. Using default: {default}")
            return default
    return current

# Helper to map string names to Qt.AlignmentFlag values
def get_qt_alignment(h_align_str, v_align_str):
    """Converts string alignment to Qt.AlignmentFlag."""
    alignment = Qt.AlignmentFlag(0)
    h_map = {
        "AlignLeft": Qt.AlignLeft, "AlignRight": Qt.AlignRight, "AlignHCenter": Qt.AlignHCenter,
        "AlignJustify": Qt.AlignJustify, "AlignCenter": Qt.AlignCenter # AlignCenter is generic
    }
    v_map = {
        "AlignTop": Qt.AlignTop, "AlignBottom": Qt.AlignBottom, "AlignVCenter": Qt.AlignVCenter,
        "AlignCenter": Qt.AlignCenter # AlignCenter is generic
    }
    if h_align_str in h_map:
        alignment |= h_map[h_align_str]
    if v_align_str in v_map:
        alignment |= v_map[v_align_str]
    
    # If only one AlignCenter is provided, apply it to both if the other is not specified
    if h_align_str == "AlignCenter" and not v_align_str and not (alignment & Qt.AlignVCenter):
        alignment |= Qt.AlignVCenter
    if v_align_str == "AlignCenter" and not h_align_str and not (alignment & Qt.AlignHCenter):
        alignment |= Qt.AlignHCenter

    if alignment == Qt.AlignmentFlag(0): # if no valid flags found
        return Qt.AlignLeft | Qt.AlignVCenter # Default
    return alignment


# Helper to map string names to Qt.PenStyle values
def get_qt_pen_style(style_str):
    """Converts string pen style to Qt.PenStyle."""
    style_map = {
        "SolidLine": Qt.SolidLine, "DashLine": Qt.DashLine, "DotLine": Qt.DotLine,
        "DashDotLine": Qt.DashDotLine, "DashDotDotLine": Qt.DashDotDotLine, "NoPen": Qt.NoPen
    }
    return style_map.get(style_str, Qt.SolidLine)

# Helper to map string names to Qt.ScrollBarPolicy values
def get_qt_scrollbar_policy(policy_str):
    """Converts string scrollbar policy to Qt.ScrollBarPolicy."""
    policy_map = {
        "ScrollBarAsNeeded": Qt.ScrollBarAsNeeded,
        "ScrollBarAlwaysOff": Qt.ScrollBarAlwaysOff,
        "ScrollBarAlwaysOn": Qt.ScrollBarAlwaysOn
    }
    return policy_map.get(policy_str, Qt.ScrollBarAsNeeded)

# Helper to map string names to QFrame.Shape values
def get_qt_frame_shape(shape_str):
    """Converts string frame shape to QFrame.Shape."""
    shape_map = {
        "NoFrame": QFrame.NoFrame, "Box": QFrame.Box, "Panel": QFrame.Panel,
        "StyledPanel": QFrame.StyledPanel, "HLine": QFrame.HLine, "VLine": QFrame.VLine,
        "WinPanel": QFrame.WinPanel
    }
    return shape_map.get(shape_str, QFrame.NoFrame)


# --- Environment Variables & Global Settings ---
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_FONT_DPI"] = "96"

PROVIDERS_WAITING_TIME = int(os.getenv("PROVIDERS_WAITING_TIME", "5")) # Default to 5s
OUTPUT_FILE_NAME = os.getenv("OUTPUT_FILE_NAME", "dashboard.png") # Default output name

GLOBAL_CFG = get_config_value(['global_settings'])
TIMEZONE_STR = GLOBAL_CFG.get('timezone', 'Europe/Amsterdam')


class EInkCalendar(QCalendarWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or get_config_value(['eink_calendar'])
        self.setup_calendar_style()
        self.event_list = []

    def set_events(self, events):""
        self.event_list = [QDate(e.year, e.month, e.day) for e in events]
        self.updateCells() # Refresh cells to show new events

    def setup_calendar_style(self):
        cfg = self.config
        self.setGridVisible(cfg.get('grid_visible', False))
        if cfg.get('vertical_header_format_none', True):
            self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setNavigationBarVisible(cfg.get('navigation_bar_visible', False))
        self.setLocale(self.locale()) # Keep current locale

        style_sheet = f"background-color: {cfg.get('background_color', 'white')}; color: {cfg.get('text_color', 'black')};"
        self.setStyleSheet(style_sheet)

        font = QFont()
        font.setPointSize(cfg.get('font_size', 12))
        font.setBold(cfg.get('font_bold', True))
        self.setFont(font)

        header_fmt = QTextCharFormat()
        header_font = QFont()
        header_font.setBold(cfg.get('header_font_bold', True))
        header_font.setPointSize(cfg.get('header_font_size', 13))
        header_fmt.setFont(header_font)
        self.setHeaderTextFormat(header_fmt)

    def paintCell(self, painter, rect, date):
        cfg = self.config
        painter.save() # Save painter state

        # Default cell painting (background, etc.)
        # super().paintCell(painter, rect, date) # Calling super() first can overpaint custom background
        
        # Custom background based on date type
        if date == QDate.currentDate():
            painter.fillRect(rect, QColor(cfg.get('current_date_fill_color', 'black')))
            painter.setPen(QColor(cfg.get('current_date_text_color', 'white')))
        else:
            # For other dates, ensure the background is painted according to stylesheet if not drawing event indicators
            # If super().paintCell is not called, we might need to manually fill the background
            painter.fillRect(rect, QColor(cfg.get('background_color', 'white'))) # Ensure background
            painter.setPen(QColor(cfg.get('text_color', 'black')))


        # Draw event indicator if date is in event_list and not the current date (current date has its own style)
        if date in self.event_list and date != QDate.currentDate():
            pen = QPen(QColor(cfg.get('event_indicator_line_color', 'black')), 
                       cfg.get('event_indicator_line_width', 2))
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            # Draw a simple underline as event indicator
            y = rect.bottom() - (cfg.get('event_indicator_line_width', 2) + 2) # Position above bottom edge
            painter.drawLine(rect.left() + 4, y, rect.right() - 4, y)
            
            # Reset pen for drawing text if it was changed for event indicator
            painter.setPen(QColor(cfg.get('text_color', 'black')))


        # Draw the day number
        painter.setFont(self.font()) # Use the calendar's main font for day numbers
        painter.drawText(rect, Qt.AlignCenter, str(date.day()))
        
        painter.restore() # Restore painter state

class EInkDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_StaticContents, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        
        global_cfg = get_config_value(['global_settings'])
        self.setStyleSheet(f"background-color: {global_cfg.get('default_background_color', 'white')}; color: {global_cfg.get('default_text_color', 'black')};")
        self.setWindowTitle("Dashboard")
        self.setFixedSize(global_cfg.get('main_window_width', 800), global_cfg.get('main_window_height', 480))

        # Initialize providers
        self.weather_provider = WeatherProvider()
        self.home_status_provider = HomeStatusProvider()
        self.system_info_provider = SystemInfoProvider()
        self.event_list_provider = EventsProvider()
        self.notes_provider = NotesProvider(self.event_list_provider) # Assuming NotesProvider might use EventListProvider

        self.weather_provider.start()
        self.home_status_provider.start()

        time.sleep(PROVIDERS_WAITING_TIME)
        
        self.init_ui()

    def init_ui(self):
        """Initializes all UI components by calling their respective methods."""
        self.init_weather_ui()
        self.init_clock_ui()
        self.init_status_ui()
        self.init_chart_ui()
        self.init_calendar_ui()
        self.init_notes_ui()
        self.init_sysinfo_ui()

    def _setup_label(self, label_instance, config_path_prefix):
        """Helper to configure a QLabel based on config."""
        cfg = get_config_value(['dashboard_elements', config_path_prefix])
        if not cfg: return # Config not found for this element

        font = QFont()
        font.setPointSize(cfg.get('font_size', 12))
        font.setBold(cfg.get('font_bold', False))
        label_instance.setFont(font)
        
        geom = cfg.get('geometry', [0,0,100,30])
        label_instance.setGeometry(*geom)

        alignment = get_qt_alignment(cfg.get('alignment_h'), cfg.get('alignment_v'))
        label_instance.setAlignment(alignment)
        
        if 'text_color' in cfg:
            label_instance.setStyleSheet(f"color: {cfg['text_color']};")
        # Add more properties like background color if needed

    def init_weather_ui(self):
        icon_text = self.weather_provider.get_weather_icon()
        temp = self.weather_provider.get_current_temperature()
        sunrise, sunset = self.weather_provider.get_sun_times()

        self.weather_icon = QLabel(icon_text, self)
        self._setup_label(self.weather_icon, 'weather_icon')
        
        info_text = f"{temp}"
        self.sun_info = QLabel(info_text, self)
        self._setup_label(self.sun_info, 'sun_info')


    def init_clock_ui(self):
        cfg_clock = get_config_value(['dashboard_elements', 'clock_label'])
        cfg_date = get_config_value(['dashboard_elements', 'date_label'])
        
        qt_timezone = QTimeZone(TIMEZONE_STR.encode())
        current_dt = QDateTime.currentDateTime(qt_timezone)

        self.clock_label = QLabel(current_dt.toString(cfg_clock.get('time_format', "HH:mm")), self)
        self._setup_label(self.clock_label, 'clock_label')

        self.date_label = QLabel(current_dt.toString(cfg_date.get('date_format', "dddd dd/MM")), self)
        self._setup_label(self.date_label, 'date_label')


    def init_status_ui(self):
        status_text = self.home_status_provider.get_status()
        self.home_status = QLabel(status_text, self)
        self._setup_label(self.home_status, 'home_status')

    def init_chart_ui(self):
        cfg = get_config_value(['dashboard_elements', 'chart_view'])
        if not cfg: return

        chart = QChart()
        chart.legend().hide()
        # Set chart background to transparent or a specific color from config
        chart.setBackgroundBrush(QBrush(Qt.transparent)) # Or QColor(cfg.get('background_color', 'white'))

        highs, lows = self.weather_provider.get_highs_and_lows()
        qt_timezone = QTimeZone(TIMEZONE_STR.encode())
        start_dt = QDateTime.currentDateTime(qt_timezone)

        # High series
        cfg_high_pen = cfg.get('high_series_pen', {})
        high_series = QSplineSeries()
        pen_high = QPen(QColor(cfg_high_pen.get('color', 'black')), 
                        cfg_high_pen.get('width', 4))
        pen_high.setStyle(get_qt_pen_style(cfg_high_pen.get('style', 'SolidLine')))
        high_series.setPen(pen_high)
        for i, val in enumerate(highs):
            dt = start_dt.addDays(i)
            high_series.append(dt.toMSecsSinceEpoch(), val)
        
        # Low series
        cfg_low_pen = cfg.get('low_series_pen', {})
        low_series = QSplineSeries()
        pen_low = QPen(QColor(cfg_low_pen.get('color', 'black')), 
                       cfg_low_pen.get('width', 2))
        pen_low.setStyle(get_qt_pen_style(cfg_low_pen.get('style', 'DashLine')))
        low_series.setPen(pen_low)
        for i, val in enumerate(lows):
            dt = start_dt.addDays(i)
            low_series.append(dt.toMSecsSinceEpoch(), val)

        chart.addSeries(high_series)
        chart.addSeries(low_series)

        # Axis X
        cfg_axis_x = cfg.get('axisX', {})
        axis_font_x = QFont()
        axis_font_x.setPointSize(cfg_axis_x.get('labels_font_size', 12))
        axis_font_x.setBold(cfg_axis_x.get('labels_font_bold', True))
        
        axisX = QDateTimeAxis()
        axisX.setFormat(cfg_axis_x.get('format', "ddd"))
        axisX.setTickCount(cfg_axis_x.get('tick_count', 5))
        axisX.setGridLineVisible(cfg_axis_x.get('grid_line_visible', False))
        axisX.setLabelsFont(axis_font_x)
        if 'labels_color' in cfg_axis_x: axisX.setLabelsColor(QColor(cfg_axis_x['labels_color']))


        # Axis Y
        cfg_axis_y = cfg.get('axisY', {})
        axis_font_y = QFont()
        axis_font_y.setPointSize(cfg_axis_y.get('labels_font_size', 12))
        axis_font_y.setBold(cfg_axis_y.get('labels_font_bold', True))

        axisY = QValueAxis()
        axisY.setRange(cfg_axis_y.get('range_min', -10), cfg_axis_y.get('range_max', 40))
        axisY.setLabelFormat(cfg_axis_y.get('label_format', "%d'C"))
        axisY.setGridLineVisible(cfg_axis_y.get('grid_line_visible', False))
        axisY.setLabelsFont(axis_font_y)
        if 'labels_color' in cfg_axis_y: axisY.setLabelsColor(QColor(cfg_axis_y['labels_color']))


        chart.addAxis(axisX, Qt.AlignBottom)
        chart.addAxis(axisY, Qt.AlignLeft)
        high_series.attachAxis(axisX); high_series.attachAxis(axisY)
        low_series.attachAxis(axisX); low_series.attachAxis(axisY)
        
        self.chart_view = QChartView(chart, self)
        if cfg.get('antialiasing', False):
            self.chart_view.setRenderHint(QPainter.Antialiasing)
        else: # Ensure it's explicitly off if false
            self.chart_view.setRenderHint(QPainter.Antialiasing, False)

        geom_chart = cfg.get('geometry', [-20, 195, 500, 285])
        self.chart_view.setGeometry(*geom_chart)
        # Make chart view background transparent to see main window background
        self.chart_view.setStyleSheet("background: transparent;")


    def init_calendar_ui(self):
        cfg = get_config_value(['dashboard_elements', 'calendar_widget_instance'])
        calendar_config = get_config_value(['eink_calendar']) # Pass specific calendar config

        self.calendar = EInkCalendar(self, config=calendar_config)
        geom_cal = cfg.get('geometry', [450, 205, 350, 280])
        self.calendar.setGeometry(*geom_cal)
        
        events = self.event_list_provider.get_events()
        only_event_dates = EventsProvider.extract_all_dates(events)
        self.calendar.set_events(only_event_dates)

    def init_notes_ui(self):
        cfg = get_config_value(['dashboard_elements', 'notes_text_edit'])
        if not cfg: return

        notes_text = self.notes_provider.get_notes_markdown()
        self.notes = QTextEdit(self)
        
        notes_font = QFont()
        notes_font.setPointSize(cfg.get('font_size', 10))
        notes_font.setBold(cfg.get('font_bold', False))
        self.notes.setFont(notes_font)
        
        self.notes.setReadOnly(True)
        self.notes.setVerticalScrollBarPolicy(get_qt_scrollbar_policy(cfg.get('vertical_scrollbar_policy', 'ScrollBarAlwaysOff')))
        self.notes.setHorizontalScrollBarPolicy(get_qt_scrollbar_policy(cfg.get('horizontal_scrollbar_policy', 'ScrollBarAlwaysOff')))
        self.notes.setFrameShape(get_qt_frame_shape(cfg.get('frame_shape', 'NoFrame')))
        
        # For QTextEdit, colors are often better handled by stylesheet for consistency
        text_color = cfg.get('text_color', get_config_value(['global_settings', 'default_text_color'], 'black'))
        bg_color = cfg.get('background_color', 'transparent') # Default to transparent
        self.notes.setStyleSheet(f"QTextEdit {{ color: {text_color}; background-color: {bg_color}; border: none; }}")

        self.notes.setMarkdown(notes_text)
        geom_notes = cfg.get('geometry', [550, 5, 240, 190])
        self.notes.setGeometry(*geom_notes)

    def init_sysinfo_ui(self):
        info = self.system_info_provider.get_info()
        self.sysinfo_label = QLabel(info, self)
        self._setup_label(self.sysinfo_label, 'sysinfo_label')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    global_font_family = get_config_value(['global_settings', 'font_family'], "Bookerly, sans-serif")
    app.setStyleSheet(f"""
    * {{
        font-family: "{global_font_family}";
    }}
    """) # Apply global font family

    window = EInkDashboard()
    # The following lines are for rendering to an image, typical for e-ink displays
    # If you want to show the window on screen for testing, comment out WA_DontShowOnScreen and the rendering part
    window.setAttribute(Qt.WA_DontShowOnScreen, True) # Don't show on screen, render to pixmap
    window.show() # Required for layout and rendering to occur properly
    
    app.processEvents() # Ensure UI is fully constructed and laid out

    pixmap = QPixmap(window.size())
    pixmap.fill(QColor(get_config_value(['global_settings', 'default_background_color'], 'white'))) # Fill with configured background
    
    # Render the window contents to the pixmap
    # Using QWidget.render() is the correct way to capture its appearance
    window.render(pixmap) 
    
    # Save the pixmap to a file
    saved = pixmap.save(OUTPUT_FILE_NAME)
    if saved:
        print(f"Dashboard saved to {OUTPUT_FILE_NAME}")
    else:
        print(f"Error: Failed to save dashboard to {OUTPUT_FILE_NAME}")
        # Check QImageWriter.supportedImageFormats() if issues with format/permissions
    
    app.quit()
