import customtkinter
from tkinter import *
from datetime import datetime
from datetime import timedelta
import fastf1
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg)
import fastf1.plotting
from fastf1 import utils
import requests
import os
import pandas as pd

# Fast F1
fastf1.Cache.enable_cache("./cache")

drivers = []
races = []


def get_drivers():
    if os.path.exists("drivers.txt"):
        date_created = os.path.getctime("drivers.txt")

        if datetime.fromtimestamp(date_created).year != datetime.today().year:
            DriverAPI()
        else:
            with open(file="drivers.txt", mode='r') as f:
                for line in f:
                    drivers.append(line)
    else:
        DriverAPI()


def get_races():
    if os.path.exists("races.txt"):
        date_created = os.path.getctime("races.txt")

        if datetime.fromtimestamp(date_created).year != datetime.today().year:
            RaceAPI()
        else:
            with open(file="races.txt", mode='r') as f:
                for line in f:
                    races.append(line)
    else:
        RaceAPI()


def DriverAPI():
    url = "http://ergast.com/api/f1/2022/2/drivers.json"

    headers = {}

    response = requests.request("GET", url, headers=headers)
    data = response.json()
    for i in data["MRData"]["DriverTable"]["Drivers"]:
        drivers.append(i['code'])

    with open(file="drivers.txt", mode='w') as f:
        for line in drivers:
            f.write(f"{line}\n")


def RaceAPI():
    schedule = fastf1.get_event_schedule(datetime.today().year)

    df = pd.DataFrame(schedule)
    for i in df["Country"]:
        races.append(i + " " + "Grand Prix")

    with open(file="races.txt", mode='w') as f:
        for line in races:
            f.write(line)
            f.write('\n')


get_drivers()
get_races()
print("Races and Drivers for Current Year Loaded")

# Colors
text_color = "#F5F3F4"
button_color = "#660708"
hover_color = "#E5383B"
main_bg = "#0B090A"
secondary_bg = "#161A1D"
fastest_lap = "#ED00FF"

# Appearance settings
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme('green')

# Main App code


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Form settings
        self.title("F1 Analysis Application")
        self.geometry(f'{1600}x{800}')
        self.resizable(0, 0)

        # Functions
        def DeletePages():
            for frame in self.mainframe.winfo_children():
                frame.destroy()

        def Exit():
            self.quit()

        def UpdateYear(year):

            print(year)
            races.clear()

            schedule = fastf1.get_event_schedule(int(year))
            df = pd.DataFrame(schedule)

            for i in df["Country"] + " " + "Grand Prix":
                races.append(i)

            self.gpSelector.configure(values=races)

            drivers.clear()

            url = f"http://ergast.com/api/f1/{year}/2/drivers.json"

            headers = {}

            response = requests.request("GET", url, headers=headers)
            data = response.json()
            for i in data["MRData"]["DriverTable"]["Drivers"]:
                drivers.append(i['code'])

            print(drivers)
            self.driverSelector.configure(values=drivers)

            self.sessionSelector.set("Session...")
            self.gpSelector.set("GP...")
            self.driverSelector.set("Driver...")

        def GetPracticeData(year, gp):
            try:
                practice1 = fastf1.get_session(year, gp, 'Practice 1')
                prac1 = pd.DataFrame(practice1.load_laps(with_telemetry=True))
            except:
                prac1 = pd.DataFrame()

            try:
                practice2 = fastf1.get_session(year, gp, 'Practice 2')
                prac2 = pd.DataFrame(practice2.load_laps(with_telemetry=True))
            except:
                prac2 = pd.DataFrame()

            try:
                practice3 = fastf1.get_session(year, gp, 'Practice 3')
                prac3 = pd.DataFrame(practice3.load_laps(with_telemetry=True))
            except:
                prac3 = pd.DataFrame()

            return prac1, prac2, prac3

        def LoadTelemetryFrame():

            # Telemetry Frame Functions
            def RemovePlots():
                FigureCanvas = Canvas()
                for plot in self.telemetryFrame.winfo_children():
                    if type(plot) == type(FigureCanvas):
                        print("Removed canvas")
                        plot.destroy()

            def LoadTelemetryPlot(driver):
                RemovePlots()
                # determine Driver's code
                driverCode = driver[str(driver).find(" ") +
                                    1:str(driver).find(" ")+4].upper()

                # Get the selected session
                session = fastf1.get_session(
                    int(self.yearSelector.get()), self.gpSelector.get(), self.sessionSelector.get())
                session.load()

                # fid the required information for plots
                driverFastestLap = session.laps.pick_driver(
                    driverCode).pick_fastest()
                driverTelemetry = driverFastestLap.get_car_data().add_distance()
                driverColor = fastf1.plotting.driver_color(driverCode)

                fastestLap = session.laps.pick_fastest()
                deltaTime, ref_tel, compare_tel = utils.delta_time(
                    driverFastestLap, fastestLap)

                # Create delta plot
                deltaFigure = plt.figure(figsize=(12, 3), dpi=100)
                deltaFigure.patch.set_facecolor(secondary_bg)

                # delta axis
                deltaAX = deltaFigure.add_subplot(1, 1, 1)
                deltaAX.plot(ref_tel['Distance'], ref_tel['Speed'],
                             color=driverColor)
                deltaAX.plot(compare_tel['Distance'], compare_tel['Speed'],
                             color=fastest_lap)
                # secondary axis for delta plot
                twin = deltaAX.twinx()
                twin.plot(ref_tel['Distance'], deltaTime, '--', color='white')
                twin.set_ylabel(
                    f"<-- Fastest ahead | {driverCode} ahead -->")
                twin.yaxis.label.set_color(text_color)

                # create main speed plot
                figure = plt.figure(figsize=(12, 4), dpi=100)
                figure.patch.set_facecolor(secondary_bg)

                # Add axis for main speed plot
                ax = figure.add_subplot(1, 1, 1)
                ax.plot(driverTelemetry['Distance'], driverTelemetry['Speed'],
                        color=driverColor, label=driverCode)
                ax.set_xlabel("Distance in m")
                ax.set_ylabel("Speed in km/h")
                ax.legend()

                # color adjustment main plot
                ax.set_facecolor(secondary_bg)
                ax.spines['bottom'].set_color(text_color)
                ax.spines['top'].set_color(text_color)
                ax.spines['left'].set_color(text_color)
                ax.spines['right'].set_color(text_color)

                ax.tick_params(axis='x', colors=text_color)
                ax.tick_params(axis='y', colors=text_color)

                ax.yaxis.label.set_color(text_color)
                ax.xaxis.label.set_color(text_color)
                # color adjustment main plot ends

                # color adjustment delta plot
                deltaAX.set_facecolor(secondary_bg)
                deltaAX.spines['bottom'].set_color(text_color)
                deltaAX.spines['top'].set_color(text_color)
                deltaAX.spines['left'].set_color(text_color)
                deltaAX.spines['right'].set_color(text_color)

                # twin.tick_params(axis='x', colors=text_color)
                twin.tick_params(axis='y', colors=text_color)
                deltaAX.tick_params(axis='x', colors=text_color)
                deltaAX.tick_params(axis='y', colors=text_color)

                deltaAX.yaxis.label.set_color(text_color)
                deltaAX.xaxis.label.set_color(text_color)
                # color adjustment delta plot

                # Display main plot
                figureCanvas = FigureCanvasTkAgg(figure, self.telemetryFrame)
                figureCanvas.get_tk_widget().grid(
                    row=2, rowspan=3, column=0, columnspan=5, padx=20, pady=10)

                # Display delta plot
                deltaFigureCanvas = FigureCanvasTkAgg(
                    deltaFigure, self.telemetryFrame)
                deltaFigureCanvas.get_tk_widget().grid(
                    row=5, rowspan=3, column=0, columnspan=5, padx=20, pady=10)

            DeletePages()
            self.telemetryFrame = customtkinter.CTkFrame(
                self.mainframe)

            # Year Selector
            self.yearSelector = customtkinter.CTkComboBox(self.telemetryFrame,
                                                          border_color=button_color, text_color=text_color, dropdown_hover_color=hover_color, corner_radius=5, dropdown_text_color=text_color, width=200,
                                                          command=UpdateYear)
            self.yearSelector.set(value="2023")
            years = []

            for x in reversed(range(2003, datetime.today().year+1)):
                years.append(str(x))

            self.yearSelector.configure(values=years)
            self.yearSelector.grid(row=0, column=0, padx=10, pady=10)
            # GP Selector
            self.gpSelector = customtkinter.CTkComboBox(self.telemetryFrame,
                                                        border_color=button_color, text_color=text_color, dropdown_hover_color=hover_color, corner_radius=5, dropdown_text_color=text_color, width=200,
                                                        values=races)
            self.gpSelector.set("GP...")
            self.gpSelector.grid(row=0, column=1, padx=10, pady=10)
            # Session Selector
            self.sessionSelector = customtkinter.CTkComboBox(self.telemetryFrame,
                                                             border_color=button_color, text_color=text_color, dropdown_hover_color=hover_color, corner_radius=5, dropdown_text_color=text_color, width=200,
                                                             values=["Race", "Qualifying", "Practice 3", "Practice 2", "Practice 1"])
            self.sessionSelector.set("Session...")
            self.sessionSelector.grid(row=0, column=2, padx=10, pady=10)
            # Driver Selector
            self.driverSelector = customtkinter.CTkComboBox(self.telemetryFrame,
                                                            border_color=button_color, text_color=text_color, dropdown_hover_color=hover_color, corner_radius=5, dropdown_text_color=text_color, width=200,
                                                            values=drivers, command=LoadTelemetryPlot)
            self.driverSelector.set("Driver...")
            self.driverSelector.grid(row=0, column=3, padx=10, pady=10)
            # Pack Telemetry Frame
            self.telemetryFrame.pack(
                side="top", fill="both", expand=True)

        def LoadQualiPrediction():
            DeletePages()
            # function variables
            qualiPredictionsDictionary = {}

            # frame functions
            def Predict():
                qualiPredictionsDictionary.clear()

                self.msgToUser = customtkinter.CTkLabel(
                    self.qualityPredictionFrame, text="Running Algorithm...This might take a while...", font=customtkinter.CTkFont(size=12, weight="bold"), text_color=hover_color)
                self.msgToUser.grid(row=0, column=3)
                self.qualityPredictionFrame.update()

                prac1, prac2, prac3 = GetPracticeData(
                    int(self.yearSelector.get()), self.gpSelector.get())

                for driver in drivers:
                    s1Times = []
                    s2Times = []
                    s3Times = []

                    for i in prac1.index:
                        if prac1['Driver'][i] == driver:
                            if prac1['IsAccurate'][i] == True:
                                s1Times.append(prac1['Sector1Time'][i])
                                s2Times.append(prac1['Sector2Time'][i])
                                s3Times.append(prac1['Sector3Time'][i])
                    for i in prac2.index:
                        if prac2['Driver'][i] == driver:
                            if prac2['IsAccurate'][i] == True:
                                s1Times.append(prac2['Sector1Time'][i])
                                s2Times.append(prac2['Sector2Time'][i])
                                s3Times.append(prac2['Sector3Time'][i])
                    for i in prac3.index:
                        if prac3['Driver'][i] == driver:
                            if prac3['IsAccurate'][i] == True:
                                s1Times.append(prac3['Sector1Time'][i])
                                s2Times.append(prac3['Sector2Time'][i])
                                s3Times.append(prac3['Sector3Time'][i])

                    s1Times.sort()
                    s2Times.sort()
                    s3Times.sort()

                    if len(s1Times) > 0 and len(s2Times) > 0 and len(s3Times) > 0:
                        laptime = s1Times[0] + s2Times[0] + s3Times[0]
                        qualiPredictionsDictionary[driver] = laptime
                    else:
                        pass

                self.msgToUser.destroy()
                self.qualityPredictionFrame.update()

                sortedDict = sorted(
                    qualiPredictionsDictionary.items(), key=lambda x: x[1])

                colCount = 0
                rowCount = 1
                count = 1

                self.frame = customtkinter.CTkFrame(
                    self.qualityPredictionFrame, corner_radius=5)
                self.frame.grid(
                    row=1, rowspan=10, column=0, columnspan=2, padx=25, pady=2)

                for key, value in sortedDict:
                    color = text_color
                    x = str(value).split(":")
                    final = f"{x[1][-1:]}:{x[2][:-3]}"

                    print(f"#{count}\t{key}\t{final}")
                    if colCount < 2:
                        try:
                            color = fastf1.plotting.driver_color(key)
                        except:
                            pass

                        self.gridSlot = customtkinter.CTkFrame(
                            self.frame, border_color=text_color, border_width=1, corner_radius=2)
                        self.gridSlot.grid(
                            row=count, column=colCount, padx=50, pady=1)

                        self.Driver = customtkinter.CTkLabel(
                            self.gridSlot, text=f"#{count}\t{key}\t{final}", font=customtkinter.CTkFont(size=12, weight="bold"), text_color=color)
                        self.Driver.pack(padx=(2, 0), pady=(0, 2))
                    else:
                        colCount = 0
                        rowCount += 1
                        try:
                            color = fastf1.plotting.driver_color(key)
                        except:
                            pass

                        self.gridSlot = customtkinter.CTkFrame(
                            self.frame, border_color=text_color, border_width=1, corner_radius=2)
                        self.gridSlot.grid(
                            row=count, column=colCount, padx=50, pady=1)

                        self.Driver = customtkinter.CTkLabel(
                            self.gridSlot, text=f"#{count}\t{key}\t{final}", font=customtkinter.CTkFont(size=12, weight="bold"), text_color=color)
                        self.Driver.pack(padx=(2, 0), pady=(0, 2))

                    colCount += 1
                    count += 1

            self.qualityPredictionFrame = customtkinter.CTkFrame(
                self.mainframe)
            # Year Selector
            self.yearSelector = customtkinter.CTkComboBox(self.qualityPredictionFrame,
                                                          border_color=button_color, text_color=text_color, dropdown_hover_color=hover_color, corner_radius=5, dropdown_text_color=text_color, width=200,
                                                          command=UpdateYear)
            self.yearSelector.set(value="2023")
            years = []

            for x in reversed(range(2003, datetime.today().year+1)):
                years.append(str(x))

            self.yearSelector.configure(values=years)
            self.yearSelector.grid(row=0, column=0, padx=10, pady=10)

            # GP Selector
            self.gpSelector = customtkinter.CTkComboBox(self.qualityPredictionFrame,
                                                        border_color=button_color, text_color=text_color, dropdown_hover_color=hover_color, corner_radius=5, dropdown_text_color=text_color, width=200,
                                                        values=races)
            self.gpSelector.set("GP...")
            self.gpSelector.grid(row=0, column=1, padx=10, pady=10)

            # Get prediction button
            self.predictionButton = customtkinter.CTkButton(self.qualityPredictionFrame,
                                                            text="Predict", command=Predict, text_color=text_color, fg_color=button_color, hover_color=hover_color,)
            self.predictionButton.grid(row=0, column=2, padx=10, pady=10)

            # Pack predictor frame
            self.qualityPredictionFrame.pack(
                side="top", fill="both", expand=True)

        def LoadTyreDegradationFrame():
            DeletePages()
            # frame functions

            self.tyreDegradationFrame = customtkinter.CTkFrame(
                self.mainframe)
            # Year Selector
            self.yearSelector = customtkinter.CTkComboBox(self.tyreDegradationFrame,
                                                          border_color=button_color, text_color=text_color, dropdown_hover_color=hover_color, corner_radius=5, dropdown_text_color=text_color, width=200,
                                                          command=UpdateYear)
            self.yearSelector.set(value="2023")
            years = []

            for x in reversed(range(2003, datetime.today().year+1)):
                years.append(str(x))

            self.yearSelector.configure(values=years)
            self.yearSelector.grid(row=0, column=0, padx=10, pady=10)
            # Drivers
            self.driverSelector = customtkinter.CTkComboBox(self.tyreDegradationFrame,
                                                            border_color=button_color, text_color=text_color, dropdown_hover_color=hover_color, corner_radius=5, dropdown_text_color=text_color, width=200,
                                                            values=drivers)
            self.driverSelector.set("Driver...")
            self.driverSelector.grid(row=0, column=3, padx=10, pady=10)
            # GP Selector
            self.gpSelector = customtkinter.CTkComboBox(self.tyreDegradationFrame,
                                                        border_color=button_color, text_color=text_color, dropdown_hover_color=hover_color, corner_radius=5, dropdown_text_color=text_color, width=200,
                                                        values=races)
            self.gpSelector.set("GP...")
            self.gpSelector.grid(row=0, column=1, padx=10, pady=10)

            # Pack frame
            self.tyreDegradationFrame.pack(
                side="top", fill="both", expand=True)
        # Functions end

        # Side bar section
        self.sidebar = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color=secondary_bg)
        self.sidebar.pack(side=LEFT)
        self.sidebar.pack_propagate(False)
        self.sidebar.configure(width=250, height=800)

        self.logo_label = customtkinter.CTkLabel(
            self.sidebar, text="Select Section", font=customtkinter.CTkFont(size=20, weight="bold"), text_color=text_color)
        self.logo_label.place(x=50, y=10)

        self.graph = customtkinter.CTkButton(
            self.sidebar, text="Telemetry Graphs", width=200, text_color=text_color, fg_color=button_color, hover_color=hover_color, command=LoadTelemetryFrame)
        self.graph.place(x=25, y=50)

        self.degradation = customtkinter.CTkButton(
            self.sidebar, text="Tyre Degradation", width=200, text_color=text_color, fg_color=button_color, hover_color=hover_color, command=LoadTyreDegradationFrame)
        self.degradation.place(x=25, y=100)

        self.quali = customtkinter.CTkButton(
            self.sidebar, text="Qualifying Predictor", width=200, text_color=text_color, fg_color=button_color, hover_color=hover_color, command=LoadQualiPrediction)
        self.quali.place(x=25, y=150)

        self.exit = customtkinter.CTkButton(
            self.sidebar, text="Exit Program", width=200, text_color=text_color, fg_color=button_color, hover_color=hover_color, command=Exit)
        self.exit.place(x=25, y=750)
        # Side bar section ends

        # Main Frame Section
        self.mainframe = customtkinter.CTkFrame(
            self, corner_radius=2, fg_color=main_bg)
        self.mainframe.pack(side=LEFT)
        self.mainframe.pack_propagate(False)
        self.mainframe.configure(width=1600, height=800)
        # Main Frame Section Ends


if __name__ == "__main__":
    app = App()
    app.mainloop()
