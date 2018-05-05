import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import time
import csv
from optics import conversions
import os
from os import path


class ThermovoltageTime:
    def __init__(self, filepath, notes, device, scan, gain, rate, maxtime, lockin):
        self._filepath = filepath
        self._notes = notes
        self._device = device
        self._scan = scan
        self._gain = gain
        self._rate = rate
        self._maxtime = maxtime
        self._lockin = lockin
        self._writer = None
        self._fig, (self._ax1, self._ax2) = plt.subplots(2)
        self._max_voltage_x = 0
        self._max_voltage_y = 0
        self._min_voltage_x = 0
        self._min_voltage_y = 0
        self._file = None
        self._imagefile = None
        self._start_time = None
        self._voltages = None
        self._sleep = 1 / self._rate

    def write_header(self):
        self._writer.writerow(['device:', self._device])
        self._writer.writerow(['scan:', self._scan])
        self._writer.writerow(['gain:', self._gain])
        self._writer.writerow(['rate:', self._rate])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['time', 'x_raw', 'y_raw', 'x_v', 'y_v'])
        
    def makefile(self):
        os.makedirs(self._filepath, exist_ok=True)
        index = self._scan
        self._file = path.join(self._filepath, '{}_{}{}'.format(self._device, index, '.csv'))
        self._imagefile = path.join(self._filepath, '{}_{}{}'.format(self._device, index, '.png'))
        while path.exists(self._file):
            index += 1
            self._file = path.join(self._filepath, '{}_{}{}'.format(self._device, index, '.csv'))
            self._imagefile = path.join(self._filepath, '{}_{}{}'.format(self._device, index, '.png'))
            
    def setup_plots(self):
        self._ax1.title.set_text('X_1')
        self._ax2.title.set_text('Y_1')
        self._ax1.set_ylabel('voltage (uV)')
        self._ax2.set_ylabel('voltage (uV)')
        self._ax1.set_xlabel('time (s)')
        self._ax2.set_xlabel('time (s)')
        self._fig.show()
        
    def set_limits(self):
        if self._voltages[0] > self._max_voltage_x:
            self._max_voltage_x = self._voltages[0]
        if self._voltages[0] < self._min_voltage_x:
            self._min_voltage_x = self._voltages[0]
        if 0 < self._min_voltage_x < self._max_voltage_x:
            self._ax1.set_ylim(self._min_voltage_x * 1000000 / 2, self._max_voltage_x * 2 * 1000000)
        if self._min_voltage_x < 0 < self._max_voltage_x:
            self._ax1.set_ylim(self._min_voltage_x * 2 * 1000000, self._max_voltage_x * 2 * 1000000)
        if self._min_voltage_x < self._max_voltage_x < 0:
            self._ax1.set_ylim(self._min_voltage_x * 2 * 1000000, self._max_voltage_x * 1 / 2 * 1000000)
        if self._voltages[1] > self._max_voltage_y:
            self._max_voltage_y = self._voltages[1]
        if self._voltages[1] < self._min_voltage_y:
            self._min_voltage_y = self._voltages[1]
        if self._min_voltage_y > 0 < self._max_voltage_y:
            self._ax2.set_ylim(self._min_voltage_y * 1000000 / 2, self._max_voltage_y * 2 * 1000000)
        if self._min_voltage_y < 0 < self._max_voltage_y:
            self._ax2.set_ylim(self._min_voltage_y * 2 * 1000000, self._max_voltage_y * 2 * 1000000)
        if self._min_voltage_y > self._max_voltage_y > 0:
            self._ax2.set_ylim(self._min_voltage_y * 2 * 1000000, self._max_voltage_y * 1 / 2 * 1000000)

    def measure(self):
        raw = self._lockin.read_xy()
        self._voltages = [conversions.convert_x_to_iphoto(x, self._gain) for x in raw]
        time.sleep(self._sleep)
        time_now = time.time() - self._start_time
        self._writer.writerow([time_now, raw[0], raw[1], self._voltages[0], self._voltages[1]])
        self._ax1.scatter(time_now, self._voltages[0] * 1000000, c='c', s=2)
        self._ax2.scatter(time_now, self._voltages[1] * 1000000, c='c', s=2)
        self.set_limits()
        plt.tight_layout()
        self._fig.canvas.draw()

    def main(self):
        self.makefile()
        with open(self._file, 'w', newline='') as inputfile:
            try:
                self._start_time = time.time()
                self._writer = csv.writer(inputfile)
                self.write_header()
                self.setup_plots()
                while time.time() - self._start_time < self._maxtime:
                    self.measure()
                plt.savefig(self._imagefile, format='png', bbox_inches='tight')
            except KeyboardInterrupt:
                plt.savefig(self._imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data