#!/usr/bin/env python3
from PySide6.QtWidgets import QWidget, QLabel, QTextEdit, QCalendarWidget, QApplication, QFrame
from PySide6.QtGui import QFont, QPainter, QPixmap, QPen, QTextCharFormat, QPolygon
from PySide6.QtCore import Qt, QDateTime, QDate
from PySide6.QtCharts import QChart, QChartView, QSplineSeries, QValueAxis, QDateTimeAxis
import sys, time

# Data Providers
from providers.weather_provider import WeatherProvider
from providers.events_provider import EventsProvider
from providers.home_status_provider import HomeStatusProvider
from providers.notes_provider import NotesProvider
from providers.system_info_provider import SystemInfoProvider

class EInkCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_calendar_style()
        self.event_list = []

    def set_events(self, events):
        self.event_list = [ QDate(e.year, e.month, e.day ) for e in events]

    def setup_calendar_style(self):
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setNavigationBarVisible(False)
        self.setLocale(self.locale())
        self.setStyleSheet("background-color: white; color: black;")
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self.setFont(font)
        header_fmt = QTextCharFormat()
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(18)
        header_fmt.setFont(header_font)
        self.setHeaderTextFormat(header_fmt)

    def paintCell(self, painter, rect, date):
        
        if date == QDate.currentDate():
            painter.fillRect(rect, Qt.black)
            painter.setPen(Qt.white)
            painter.setFont(self.font())
            painter.drawText(rect, Qt.AlignCenter, str(date.day()))
        elif date in self.event_list:
            painter.save()

            # draw a filled black ellipse covering the entire cell
            painter.setPen(QPen(Qt.black, 2))
            painter.setBrush(Qt.NoBrush)
            y = rect.bottom() - 4
            painter.drawLine(rect.left()+4, y, rect.right()-4, y)
            
            # then draw the day-number on top
            painter.setPen(Qt.black)
            painter.setFont(self.font())
            painter.drawText(rect, Qt.AlignCenter, str(date.day()))

            painter.restore()
        else:
            super().paintCell(painter, rect, date)

class EInkDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_StaticContents, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setStyleSheet("background-color: white; color: black;")
        self.setWindowTitle("Dashboard")
        self.setFixedSize(800, 480)

        # Initialize providers
        self.weather_provider = WeatherProvider()
        self.home_status_provider = HomeStatusProvider()
        self.system_info_provider = SystemInfoProvider()
        self.event_list_provider = EventsProvider()
        self.notes_provider = NotesProvider(self.event_list_provider)

        self.weather_provider.start()
        self.home_status_provider.start()

        # give some time to receieve weather homeassistant 
        time.sleep(2)
        
        # Build UI
        self.init_weather_ui()
        self.init_clock_ui()
        self.init_status_ui()
        self.init_chart_ui()
        self.init_calendar_ui()
        self.init_notes_ui()
        self.init_sysinfo_ui()

    def init_weather_ui(self):
        icon = self.weather_provider.get_weather_icon()
        temp = self.weather_provider.get_current_temperature()
        sunrise, sunset = self.weather_provider.get_sun_times()
        self.weather_icon = QLabel(icon, self)
        font = QFont(); font.setPointSize(150); font.setBold(True)
        self.weather_icon.setFont(font)
        self.weather_icon.setGeometry(25, 1, 160, 160)
        info_text = f"{temp}  |  ↑  {sunrise}  |  ↓  {sunset}"
        self.sun_info = QLabel(info_text, self)
        info_font = QFont(); info_font.setPointSize(18); info_font.setBold(True)
        self.sun_info.setFont(info_font)
        self.sun_info.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.sun_info.setGeometry(10, 170, 300, 20)

    def init_clock_ui(self):
        self.clock_label = QLabel(QDateTime.currentDateTime().toString("HH:mm"), self)
        clock_font = QFont(); clock_font.setPointSize(130); clock_font.setBold(True)
        self.clock_label.setFont(clock_font)
        self.clock_label.setAlignment(Qt.AlignCenter)
        self.clock_label.setGeometry(200, 1, 350, 160)
        self.date_label = QLabel(QDateTime.currentDateTime().toString("dddd dd/MM"), self)
        date_font = QFont(); date_font.setPointSize(24); date_font.setBold(True)
        self.date_label.setFont(date_font)
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setGeometry(250, 135, 200, 40)

    def init_status_ui(self):
        status_text = self.home_status_provider.get_status()
        self.home_status = QLabel(status_text, self)
        status_font = QFont(); status_font.setPointSize(15); status_font.setBold(True)
        self.home_status.setFont(status_font)
        self.home_status.setAlignment(Qt.AlignCenter)
        self.home_status.setGeometry(280, 176, 200, 15)

    def init_chart_ui(self):
        chart = QChart(); chart.legend().hide()
        highs, lows = self.weather_provider.get_highs_and_lows()
        start = QDateTime.currentDateTime()
        high_series = QSplineSeries(); high_series.setPen(QPen(Qt.black, 5))
        low_series  = QSplineSeries(); low_series.setPen(QPen(Qt.black, 2, Qt.DashLine))
        for i, val in enumerate(highs):
            dt = start.addDays(i)
            high_series.append(dt.toMSecsSinceEpoch(), val)
        for i, val in enumerate(lows):
            dt = start.addDays(i)
            low_series.append(dt.toMSecsSinceEpoch(), val)
        chart.addSeries(high_series); chart.addSeries(low_series)
        axis_font = QFont(); axis_font.setPointSize(14); axis_font.setBold(True)
        axisX = QDateTimeAxis(); axisX.setFormat("ddd"); axisX.setTickCount(5)
        axisX.setGridLineVisible(False); axisX.setLabelsFont(axis_font)
        axisY = QValueAxis(); axisY.setRange(-10, 40)
        axisY.setLabelFormat("%d`C"); axisY.setGridLineVisible(False); axisY.setLabelsFont(axis_font)
        chart.addAxis(axisX, Qt.AlignBottom); chart.addAxis(axisY, Qt.AlignLeft)
        high_series.attachAxis(axisX); high_series.attachAxis(axisY)
        low_series.attachAxis(axisX); low_series.attachAxis(axisY)
        chart_view = QChartView(chart, self)
        chart_view.setRenderHint(QPainter.Antialiasing, False)
        chart_view.setGeometry(-20, 195, 500, 285)

    def init_calendar_ui(self):
        self.calendar = EInkCalendar(self)
        self.calendar.setGeometry(450, 205, 350, 280)
        events = self.event_list_provider.get_events()
        only_event_dates = EventsProvider.extract_all_dates(events)
        self.calendar.set_events(only_event_dates)

    def init_notes_ui(self):
        notes_text = self.notes_provider.get_notes_markdown()
        self.notes = QTextEdit(self)
        notes_font = QFont(); notes_font.setPointSize(16)
        self.notes.setFont(notes_font)
        self.notes.setReadOnly(True)
        self.notes.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.notes.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.notes.setFrameShape(QFrame.NoFrame)
        self.notes.setMarkdown(notes_text)
        self.notes.setGeometry(550, 5, 240, 190)

    def init_sysinfo_ui(self):
        info = self.system_info_provider.get_info()
        self.sysinfo_label = QLabel(info, self)
        sysinfo_font = QFont(); sysinfo_font.setPointSize(12)
        self.sysinfo_label.setFont(sysinfo_font)
        self.sysinfo_label.setGeometry(10, 460, 400, 20)

if __name__ == "__main__":
    def_font = QFont("Roboto Mono")
    app = QApplication(sys.argv)
    QApplication.setFont(def_font)
    window = EInkDashboard()
    window.setAttribute(Qt.WA_DontShowOnScreen)
    window.show()
    app.processEvents()
    pixmap = QPixmap(window.size())
    pixmap.fill(Qt.white)
    window.render(pixmap)
    pixmap.save("dashboard.png")
    app.quit()
