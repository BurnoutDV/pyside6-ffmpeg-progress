#!/usr/bin/env python
# coding: utf-8

# Copyright 2022 by BurnoutDV, <development@burnoutdv.com>
#
# This file is part of ffmpeg_progress.
#
# ffmpeg_progress is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# ffmpeg_progress is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# @license GPL-3.0-only <https://www.gnu.org/licenses/gpl-3.0.en.html>

import ffmpeg
from datetime import datetime

from PySide6.QtWidgets import *
from PySide6 import QtCore
from toolbox import *

logger = logging.getLogger(__name__)

i18n = {
    'drop_hint': "Drop any video file"
}

class ProgressWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # class vars
        self.proc = None
        self.file_info = None
        self.file_path = None
        # Window setup
        self.setWindowTitle("ProgressBar?")
        self.setMinimumSize(400, 240)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint & QtCore.Qt.WindowMaximizeButtonHint)
        self.setAcceptDrops(True)
        # Widgets
        lay_dia = QFormLayout()
        self.status_bar = QProgressBar(Maximum=1000)
        self.status_time = QLineEdit(ReadOnly=True)
        self.frames = QLineEdit(ReadOnly=True)
        self.filesize = QLineEdit(ReadOnly=True)
        self.process_rate = QLineEdit(ReadOnly=True)
        self.time_elapsed = QLineEdit(ReadOnly=True)
        self.time_estimated = QLineEdit(ReadOnly=True)
        self.message = QLineEdit(i18n['drop_hint'], ReadOnly=True)
        lay_dia.addRow("Position in clip / Total Length:", self.status_time)
        lay_dia.addRow("Current / Total Frames:", self.frames)
        lay_dia.addRow("Current / Projected filesize:", self.filesize)
        lay_dia.addRow("Processing rate:", self.process_rate)
        lay_dia.addRow("Time elapsed:", self.time_elapsed)
        lay_dia.addRow("Time remaining:", self.time_estimated)
        lay_dia.addRow(self.status_bar)
        lay_dia.addRow(self.message)
        lay_2 = QHBoxLayout()
        self.btn_quit = QPushButton("Quit")
        self.btn_start = QPushButton("Start", Disabled=True)
        lay_2.addWidget(self.btn_start)
        lay_2.addWidget(self.btn_quit)
        lay_1 = QVBoxLayout()
        lay_1.addLayout(lay_dia)
        lay_1.addLayout(lay_2)

        central_container = QWidget()
        central_container.setLayout(lay_1)
        self.setCentralWidget(central_container)

        self.btn_quit.clicked.connect(self.close)
        self.btn_start.clicked.connect(self.start_process)

    def start_process(self):
        if self.proc is None:
            self.file_info = extract_probe(ffmpeg.probe(self.file_path))
            self.file_info['start_time'] = datetime.now()
            self.proc = QtCore.QProcess()
            self.proc.finished.connect(self.regular_end_process)
            self.proc.readyReadStandardError.connect(self.stderr_out_process)
            self.proc.readyReadStandardOutput.connect(self.stdout_process)
            self.proc.start("ffmpeg", ["-y", "-i", self.file_path, "-c:v", "libx264", "-crf", "22.5", "output.mkv"])
            self.btn_quit.setDisabled(True)

    def stderr_out_process(self):
        data = self.proc.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        if stderr[0:5] == "frame":
            if status := regex_ffmpeg_encoding(stderr):
                fps_delta = self.file_info['est_frames'] - status['frames']
                self.status_time.setText(f"{format_timedelta(status['elapsed'])} / {format_timedelta(self.file_info['time_length'])}")
                self.frames.setText(f"{status['frames']} / {self.file_info['est_frames']}")
                self.filesize.setText(f"{sizeof_fmt(status['file_size']*1024)}")  # TODO: math for file size that might be
                self.process_rate.setText(f"{status['fps']}fps ({status['enc_rate']}{status['enc_unit']})")
                self.time_elapsed.setText(f"{format_timedelta(datetime.now()-self.file_info['start_time'])}")
                self.time_estimated.setText(format_timedelta(timedelta(seconds=fps_delta/status['fps'])))
                self.status_bar.setValue(round(status['frames']/self.file_info['est_frames']*1000))

    def stdout_process(self):
        print(f"{'='*10}STD OUt{'='*10}")
        data = self.proc.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        print(stdout)

    def regular_end_process(self):
        self.proc = None
        # i am cheating here and just set everything to 100% without actually having anything
        self.status_time.setText(f"{format_timedelta(self.file_info['time_length'])} / {format_timedelta(self.file_info['time_length'])}")
        self.frames.setText(f"{self.file_info['est_frames']} / {self.file_info['est_frames']}")
        self.process_rate.setText(f"0fps (0kbyte/s)")
        self.time_elapsed.setText(f"{format_timedelta(datetime.now() - self.file_info['start_time'])}")
        self.time_estimated.setText(format_timedelta(timedelta(seconds=0)))
        self.status_bar.setValue(1000)
        # reset interface
        self.file_path = None
        self.btn_start.setDisabled(True)
        self.btn_quit.setDisabled(False)
        self.message.setText(i18n['drop_hint'])

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            file_name = url.toLocalFile()
            if file_name.strip:  # TODO: proper check for real file here
                self.message.setText(file_name)
                self.file_path = file_name
                self.btn_start.setDisabled(False)