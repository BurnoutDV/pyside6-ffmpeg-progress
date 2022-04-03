# Pyside6-QProcess-ffmpg process bar example

For a project i had in my head for a while i was pondering back and forth how to achieve an ffmpeg call and get a process report at the same time. The program of my dreams works headless / cli based and and in a gui mode, this solution only achieves the GUI mode and actually heavily leverages the signal abilities of the QT Library stuff. Starting point of my excursion was this blog post:
https://geoffsamuel.com/2020/03/16/the-qpower-of-qprocess/

To make it short, the magic is this:

```python
self.proc = QtCore.QProcess()
...
data = self.proc.readAllStandardError()
stderr = bytes(data).decode("utf8")
```

and the knowledge that the progress information of the ffmpeg library is on stderr. Everything else is fluff.

## Requirements

For its simple design this leverages quite some heavy libraries, namely `PySide6`, if you replace it 1:1 by `PySide2` it should work exactly the same as i did not utilize any new features. Further i use the handy [ffmpeg-python](https://github.com/kkroening/ffmpeg-python) hooks just to completely ignore the ffmpeg part and only take the tiny part that is `ffprobe` because i did not saw any reason to do my own handling of that output to achieve what others did before me.

## Installation

1. clone repo `git clone https://github.com/BurnoutDV/pyside6-ffmpeg-progress`
2. setup venv `cd pyside6-ffmpeg-progress` && `python -m venv .venv`
3. install local package `python -m pip install .`
4. run `python -m pyside6-ffmpeg-progress.main`

## How it works

Upon pushing the start button `ffprobe` is used to get the basic data and then the actual program begins to work, *QProcess* is doing almost all of the work as the signaling system of *QT* does almost everything for us. We bind some functions some functions to *stdOUT* and *stdERR*, for this specific instance of *ffmpeg* only the *stdERR* pipe is actually of relevance. For this simple example we need to transform the content of the *ffmpeg* output, usually this is first the *ffprobe* data once more, some other statistics we don't care at all about. There we filter for lines that start with `frame` which describes the statistic data we get around all three seconds. I use *regex* to extract some data by capturing-groups (*i am quite unsure if it would be better to use separate regex searches for each value*):
```regex
^(frame=\s*)([0-9]+)\s+
(fps=)\s*([0-9]+)\s+
(q=)\s*([0-9]*[.]?[0-9]+)\s+
(size=)\s*([0-9]+)..\s+
(time=)\s*([0-9][0-9]:[0-9][0-9]:[0-9][0-9][.][0-9][0-9])\s+
(bitrate=)\s*([0-9]*[.]?[0-9]+)(kbits\/s)\s+
(speed=)\s*([0-9]*[.]?[0-9]+)x\s*
```

With this in mind we have almost everything we need, unfortunatly we don't know how many frames the video actually has and frames is what we use to calculate the progress bar (opposed to the time). Apparently its not entirely trivial to get the number of frames in a given video track therefore we do a good estimate: `fps*lenght_in_seconds`. All this gives us the following display (design stolen from MeGUI):

![progress](./README/progress.png)

Some caveats:

* the file size *ffmpeg* gives is in kbyte not in byte -> `*1024`
* i decided to use timedelta for the storage of time units..that class has some problems with the access of its time (it stores time only as days and seconds, nothing inbetween)
* our estimated file size is highly dependent on the content, my typical content is gameplay, if the first 5 minutes are static menus followed by fast actions scenes you might as well ignore that projection.
* same is true for the remaining time, here i just use the current fps rate and the remaining frames, although we could use historical average data for that..and i did that, still, only a rough approximation
