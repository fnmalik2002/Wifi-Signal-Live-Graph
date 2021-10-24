"""This module is an app in wx Python that shows live matplotlib graph on one of its panels."""

import subprocess
import time
import datetime
import wx
import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import style
import sqlite3


def update_database(rssi_value, noise_value):
    """Update sqlite3 database with the wifi data"""
    try:
        sql_connection = sqlite3.connect('wifi_db.db')
        cursor = sql_connection.cursor()
        print("Connected to database")
        qry = "INSERT INTO wifi_data (signal, shor, dated) VALUES (?, ?, ?)"
        val = (rssi_value, noise_value, get_timestamp())
        count = cursor.execute(qry, val)
        sql_connection.commit()
        print("Record updated successfully")
        cursor.close()
    except sqlite3.Error as error:
        print("Record update failure", error)
    finally:
        if sql_connection:
            sql_connection.close()
            print("Database connection closed")

def get_timestamp():
    return datetime.datetime.now()

def runcommand(aw):
    """this function runs terminal commands in the background, which are given to it as input when it is called."""
    getcore = subprocess.Popen(aw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = getcore.communicate()  # type: (str, str)
    return out


class Top_panel(wx.Panel):
    """This panel will act as graph canvas. """
    n = 0
    rssi = []
    noise = []
    strn = []
    stop = 0

    def __init__(self, parent):
        """Initialize this panel"""
        wx.Panel.__init__(self, parent=parent)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        # style.use('fivethirtyeight')
        style.use('bmh')
        self.figure = Figure(figsize=(6, 2))
        self.axes = self.figure.add_subplot(111)
        self.axes.set_ylabel('Signal Strength (% of Max)')
        self.axes.set_xlabel('Time interval (s)')
        # self.axes2 = self.axes.twinx()
        self.empty_txt = wx.StaticText(self, -1, "Wifi Signal Strength")
        self.axes.set_yticks([0,20, 40,60,80,100])

        font = wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.empty_txt.SetFont(font)

        self.canvas = FigureCanvas(self, -1, self.figure)

        self.btn = wx.Button(self, -1, label="Start")
        self.btn.Bind(wx.EVT_BUTTON, self.start)

        # self.btn2 = wx.Button(self, -1, label="Stop")
        # self.btn2.Bind(wx.EVT_BUTTON, self.stop_animation)
        # self.btn.Bind(wx.EVT_BUTTON, self.do)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer.Add(self.sizer2, 1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 0)

        self.sizer2.Add(self.empty_txt, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        self.sizer.Add(self.canvas, 3, wx.ALIGN_CENTER)
        self.sizer3.Add(self.btn, 1, wx.ALIGN_CENTER | wx.RIGHT, 0)
        # self.sizer3.Add(self.btn2, 1, wx.ALIGN_CENTER)
        self.sizer.Add(self.sizer3, 1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 0)
        self.SetSizer(self.sizer)

    def do(self, event):
        """method created for testing database insert function"""
        cmd = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | grep Ctl"
        rslt = list((str(runcommand(cmd), 'utf-8').lstrip()).split('\n'))
        sig_value = int(rslt[0].split(":")[1])
        noise_value = int(rslt[1].split(":")[1])
        print("Signal \n", sig_value, "\nNoise \n", noise_value)
        update_database(sig_value, noise_value)

    def animate(self, i, event):
        """This function will draw graph on the canvas using lists of data for x-axis every time it is called."""
        cmd = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | grep Ctl"
        rslt = list((str(runcommand(cmd), 'utf-8').lstrip()).split('\n'))
        sig_value = 100 -(((-30.0-(int(rslt[0].split(":")[1])))/70.0)*100)
        noise_value = 100 -(((-30.0-(int(rslt[1].split(":")[1])))/70.0)*100)
        update_database(sig_value, noise_value)
        self.rssi.append(sig_value)
        self.noise.append(noise_value)
        self.strn.append(sig_value - noise_value)
        # print(self.strn)
        # print("Signal \n", self.rssi, "\nNoise \n", self.noise)
        self.axes.clear()
        # self.axes2.clear()
        self.axes.plot(self.rssi, 'b', label='Signal')
        self.axes.plot(self.noise, 'r', label='Noise')
        # self.axes.plot(self.strn, 'g')
        self.axes.set_ylabel('Signal Strength (% of Max)')
        self.axes.set_xlabel('Time interval (s)')
        self.axes.set_yticks([0,20, 40,60,80,100])
        self.axes.legend()
        self.figure.canvas.draw()

        self.figure.tight_layout()

    def start(self, event, interval = 1):

        if self.btn.GetLabel() != "Stop":
            self.btn.SetLabel("Stop")

            self.stop = 0
        else:
            self.btn.SetLabel("Start")
            self.stop = 1
        # self.btn.SetFocus()

        i = 0
        while self.stop == 0:
            self.animate(i, event)
            i += 1
            wx.Yield()
            time.sleep(interval)

    def stop_animation(self, event):
        self.stop = 1

class MyGraphGUI(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, title="Graph Window", size=(800, 700))
        top = Top_panel(self)
        # wx.Yield()
        # top.start(event=wx.EVT_BUTTON)


if __name__ == '__main__':
    app = wx.App()
    frame = MyGraphGUI()
    frame.Show()
    app.MainLoop()
