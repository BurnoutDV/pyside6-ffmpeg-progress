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

import sys

from ffmpeg_progress.gui import *

if __name__ == "__main__":
    thisApp = QApplication(sys.argv)
    window = ProgressWindow()
    window.show()
    try:
        sys.exit(thisApp.exec())
    except KeyboardInterrupt:
        sys.exit()

