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
import pandas as pd


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
    avg = []
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
        self.slider_text = wx.StaticText(self, -1, "Select reading interval (s)")

        self.slider = wx.Slider(self, 1, 1, 1, 10, pos=(10, 10), size=(250, -1),
                           style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        # slider.SetTickFreq(5, 1)
        print("slider value", self.slider.GetValue())

        self.btn = wx.Button(self, -1, label="Start")
        self.btn.Bind(wx.EVT_BUTTON, self.start)

        self.btn2 = wx.Button(self, -1, label="Quit")
        self.btn2.Bind(wx.EVT_BUTTON, self.do_quit)
        # self.btn.Bind(wx.EVT_BUTTON, self.do)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer.Add(self.sizer2, 1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 0)

        self.sizer2.Add(self.empty_txt, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        self.sizer.Add(self.canvas, 3, wx.ALIGN_CENTER)

        self.sizer3.Add(self.slider_text, 0, wx.ALIGN_CENTER | wx.RIGHT, 0)

        self.sizer3.Add(self.slider, 0, wx.ALIGN_CENTER | wx.RIGHT, 0)
        self.sizer3.Add(self.btn, 0, wx.ALIGN_CENTER | wx.RIGHT, 10)
        self.sizer3.Add(self.btn2, 1, wx.ALIGN_CENTER)
        self.sizer.Add(self.sizer3, 1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 0)
        self.SetSizer(self.sizer)

    def do_quit(self, event):
        self.Parent.Destroy()

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
        noise_pd = pd.DataFrame(self.noise)
        print("mean", noise_pd.mean(axis=0))

        if len(self.avg) != 0:
            self.avg.append((self.avg[-1] + noise_value)/2)
        else:
            self.avg.append(noise_value)
        # print(self.avg)
        # print("Signal \n", self.rssi, "\nNoise \n", self.noise)
        self.axes.clear()
        # self.axes2.clear()
        self.axes.plot(self.rssi, 'g', label='Signal')
        self.axes.plot(self.noise, 'r', label='Noise')
        # self.axes.plot(noise_pd.mean(axis=0), 'b-', label='Mean Noise')
        self.axes.set_ylabel('Signal Strength (% of Max)')
        self.axes.set_xlabel('Reading Number')
        self.axes.set_yticks([0,20,40,60,80,100])
        self.axes.legend()
        # self.axes.fill_between(self.noise,self.rssi,0, interpolate=True, color='cyan')
        self.figure.canvas.draw()

        self.figure.tight_layout()

    def start(self, event):
        intrvl = self.slider.GetValue()

        if self.btn.GetLabel() != "Stop":
            self.btn.SetLabel("Stop")
            self.slider.Disable()
            self.btn2.Disable()

            self.stop = 0
        else:
            self.btn.SetLabel("Start")
            self.stop = 1
            self.slider.Enable()
            self.btn2.Enable()
        # self.btn.SetFocus()

        i = 0
        while self.stop == 0:
            self.animate(i, event)
            i += 1
            wx.Yield()
            time.sleep(intrvl)

    def stop_animation(self, event):
        self.stop = 1

class MyGraphGUI(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, title="Graph Window", size=(800, 700))
        top = Top_panel(self)

        # attach the key bind event to accelerator table (to use cmd+q keys to close app)
        randomId = wx.Window.NewControlId()
        
        self.Bind(wx.EVT_MENU, self.onkeycombo, id=randomId)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('q'), randomId)])
        self.SetAcceleratorTable(accel_tbl)

    def onkeycombo(self, event):
        # print "You pressed CTRL+Q!"
        self.Destroy()


if __name__ == '__main__':
    app = wx.App()
    frame = MyGraphGUI()
    frame.Show()
    app.MainLoop()
