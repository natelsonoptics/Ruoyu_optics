import numpy as np
import os
import tkinter as tk
import time
import csv
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class LockinBaseMeasurement:
    def __init__(self, master, filepath, device, npc3sg_input=None, npc3sg_x=None, npc3sg_y=None, sr7270_dual_harmonic=None,
                 sr7270_single_reference=None, powermeter=None, attenuator_wheel=None, waveplate=None, keithley=None,
                 daq_input=None, daq_switch_ai=None, daq_switch_ao=None, laser=None, gain=None, notes=None, mono=None,
                 ccd=None, scan=None, bsc102_x=None, bsc102_y=None):
        self._master = master
        self._filepath = filepath
        self._device = device
        self._gain = gain
        self._notes = notes
        self._npc3sg_input = npc3sg_input
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._bsc102_x = bsc102_x
        self._bsc102_y = bsc102_y
        self._sr7270_dual_harmonic = sr7270_dual_harmonic
        self._sr7270_single_reference = sr7270_single_reference
        self._powermeter = powermeter
        self._mono = mono
        self._ccd = ccd
        self._writer = None
        self._start_time = None
        self._scan = scan
        if self._powermeter:
            self._power = self._powermeter.read_power()
        else:
            self._power = ''
        self._attenuator_wheel = attenuator_wheel
        self._waveplate = waveplate
        self._keithley = keithley
        self._daq_input = daq_input
        self._daq_switch_ai = daq_switch_ai
        self._daq_switch_ao = daq_switch_ao
        self._laser = laser
        if self._waveplate:
            self._measuredpolarization = self._waveplate.read_polarization()
            self._polarization = int(round((np.round(self._measuredpolarization, 0) % 180) / 10) * 10)
        else:
            self._measuredpolarization = ''
            self._polarization = ''
        self._abort = False
        self._new_max = tk.StringVar()
        self._new_min = tk.StringVar()
        self._ax1 = None
        self._ax2 = None
        self._ax3 = None
        self._ax4 = None
        self._im1 = None
        self._im2 = None
        self._clb1 = None
        self._clb2 = None
        self._fig = Figure()
        self.load()
        self._fig.tight_layout()
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._master)  # A tk.DrawingArea.
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self._filename = None
        self._imagefile = None

    def load(self):
        self._ax1 = self._fig.add_subplot(211)
        self._ax2 = self._fig.add_subplot(212)

    def abort(self):
        self._abort = True

    def make_file(self, measurement_type, index, record_polarization=True):
        os.makedirs(self._filepath, exist_ok=True)
        filename = os.path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device, measurement_type,
                                                                       self._polarization if record_polarization else '',
                                                                       index, '.csv'))
        imagefile = os.path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device,  measurement_type,
                                                                        self._polarization if record_polarization else '',
                                                                        index, '.png'))
        while os.path.exists(filename):
            index += 1
            filename = os.path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device,  measurement_type,
                                                                           self._polarization if record_polarization else '',
                                                                           index, '.csv'))
            imagefile = os.path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device,  measurement_type,
                                                                            self._polarization if record_polarization else '',
                                                                            index, '.png'))
        return filename, imagefile, index

    def write_header(self, writer, record_position=True, record_power=True, record_polarization=True):
        if self._npc3sg_input and record_position:
            position = self._npc3sg_input.read()
            writer.writerow(['x laser position:', position[0]])
            writer.writerow(['y laser position:', position[1]])
        if self._sr7270_dual_harmonic:
            writer.writerow(['applied voltage (V):', self._sr7270_dual_harmonic.read_applied_voltage()])
            writer.writerow(['osc amplitude (V):', self._sr7270_dual_harmonic.read_oscillator_amplitude()])
            writer.writerow(['osc frequency:', self._sr7270_dual_harmonic.read_oscillator_frequency()])
            writer.writerow(['dual harmonic time constant 1:', self._sr7270_dual_harmonic.read_tc()])
            writer.writerow(['dual harmonic time constant 2:', self._sr7270_dual_harmonic.read_tc(channel=2)])
            writer.writerow(
                ['dual harmonic reference phase 1: ', self._sr7270_dual_harmonic.read_reference_phase()])
            writer.writerow(['dual harmonic reference phase 2: ',
                                   self._sr7270_dual_harmonic.read_reference_phase(channel=2)])
        if self._sr7270_single_reference:
            writer.writerow(['applied voltage (V):', self._sr7270_single_reference.read_applied_voltage()])
            writer.writerow(['osc amplitude (V):', self._sr7270_single_reference.read_oscillator_amplitude()])
            writer.writerow(['osc frequency:', self._sr7270_single_reference.read_oscillator_frequency()])
            writer.writerow(['single reference phase:', self._sr7270_single_reference.read_reference_phase()])
            writer.writerow(['single reference time constant:', self._sr7270_single_reference.read_tc()])
        if self._gain:
            writer.writerow(['gain:', self._gain])
        if record_power:
            writer.writerow(['power (W):', self._power])
        if record_polarization:
            writer.writerow(['polarization:', self._polarization])
        if self._notes:
            writer.writerow(['notes:', self._notes])
        self.end_header(writer)

    def end_header(self, writer):
        writer.writerow(['end:', 'end of header'])

    def rescale(self):
        pass

    def centerbeam(self):
        self._bsc102_y.move(4)
        self._bsc102_x.move(4)

    def pack_buttons(self, master, abort_button=True, colormap_rescale=False, center_beam=False):
        if colormap_rescale:
            row = tk.Frame(master)
            lab = tk.Label(row, text='max counts', anchor='w')
            ent = tk.Entry(row, textvariable=self._new_max)
            lab.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
            ent.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
            lab = tk.Label(row, text='min counts', anchor='w')
            ent = tk.Entry(row, textvariable=self._new_min)
            row.pack(side=tk.TOP)
            lab.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
            ent.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
            button = tk.Button(master=row, text="Change colormap range", command=self.rescale)
            button.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        if abort_button:
            button = tk.Button(master=master, text="Abort", command=self.abort)
            button.pack(side=tk.BOTTOM)
        if center_beam:
            button = tk.Button(master=self._master, text="Go to center", command=self.centerbeam)
            button.pack(side=tk.BOTTOM)

    def tk_sleep(self, ms):
        self._master.after(int(np.round(ms, 0)), self.do_nothing())

    def do_nothing(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def do_measurement(self):
        pass

    def setup_plots(self):
        pass

    def measure(self):
        pass

    def main2(self, scan_name, record_polarization=True, record_power=True, record_position=True, abort_button=True,
              center_beam=False, colormap_rescale=False):
        self.pack_buttons(self._master, abort_button=abort_button, center_beam=center_beam,
                          colormap_rescale=colormap_rescale)
        self._filename, self._imagefile, self._scan = self.make_file(scan_name, self._scan,
                                                                     record_polarization=record_polarization)
        with open(self._filename, 'w', newline='') as inputfile:
            self.start()
            self._start_time = time.time()
            self._writer = csv.writer(inputfile)
            self.write_header(self._writer, record_polarization=record_polarization, record_power=record_power,
                              record_position=record_position)
            self.setup_plots()
            self._canvas.draw()
            self.measure()
            self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')
            self.stop()
