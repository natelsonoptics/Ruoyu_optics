import matplotlib
matplotlib.use('TkAgg')
from optics import setup_constants, sr7270, conversions
import matplotlib.pyplot as plt
import time
import csv
import matplotlib.gridspec as gridspec
import os
from os import path

def write_header(w):
    w.writerow(['gain:', args.gain])
    w.writerow(['notes:', args.notes])
    w.writerow(['end:', 'end of header'])
    w.writerow(['time', 'x_raw', 'y_raw', 'x_v', 'y_v'])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='thermovoltage vs time. press CTRL+C to quit')
    parser.add_argument("-f", metavar='data filepath', type=str, help='path for data folder', default='C:\\Users\\Ruoyu\\Desktop\\data')
    parser.add_argument("-rate", metavar='rate', type=float, help='optional. samples/second. do not exceed 50')
    parser.add_argument("-max", metavar='max', type=float, help='max time (seconds)', default=600)
    parser.add_argument("-gain",metavar='gain', type=float, help="gain of amplifier", default=1000)
    parser.add_argument("-device", metavar='device', type=str, help='device name')
    parser.add_argument("-scan", metavar='scan number', type=int, help='scan number, optional', default=0)
    parser.add_argument("-notes", metavar='notes', type=str, help='notes must be in double quotation marks', default="no notes")
    args = parser.parse_args()

    os.makedirs(args.f, exist_ok=True)
    index = args.scan
    file = path.join(args.f, '{}_{}{}'.format(args.device, index, '.csv'))
    imagefile = path.join(args.f, '{}_{}{}'.format(args.device, index, '.png'))

    while path.exists(file):
        index += 1
        file = path.join(args.f, '{}_{}{}'.format(args.device, index, '.csv'))
        imagefile = path.join(args.f, '{}_{}{}'.format(args.device, index, '.png'))

    with sr7270.create_endpoints_single(setup_constants.vendor, setup_constants.product) as lock_in, \
        open(file, 'w', newline='') as fn:
        try:
            start_time = time.time()
            w = csv.writer(fn)
            write_header(w)
            fig = plt.figure()
            gs = gridspec.GridSpec(2, 1)
            ax1 = plt.subplot(gs[0, 0])
            ax2 = plt.subplot(gs[1, 0])
            ax1.title.set_text('X_1')
            ax2.title.set_text('Y_1')
            ax1.set_ylabel('voltage (uV)')
            ax2.set_ylabel('voltage (uV)')
            ax1.set_xlabel('time (s)')
            ax2.set_xlabel('time (s)')
            fig.show()
            max_voltage_x = 0
            min_voltage_x = 0
            max_voltage_y = 0
            min_voltage_y = 0
            if not args.rate:
                sleep = 3 * lock_in.read_tc()[0]
            else:
                sleep = 1/args.rate
            while time.time()-start_time < args.max:
                raw = lock_in.read_xy()
                voltages = [conversions.convert_x_to_iphoto(x, args.gain) for x in raw]
                time.sleep(sleep)
                time_now = time.time() - start_time
                w.writerow([time_now, raw[0], raw[1],  voltages[0], voltages[1]])
                ax1.scatter(time_now, voltages[0] * 1000000, c='c', s=2)
                ax2.scatter(time_now, voltages[1] * 1000000, c='c', s=2)

                if voltages[0] > max_voltage_x:
                    max_voltage_x = voltages[0]
                if voltages[0] < min_voltage_x:
                    min_voltage_x = voltages[0]

                if 0 < min_voltage_x < max_voltage_x:
                    ax1.set_ylim(min_voltage_x * 1000000 / 2, max_voltage_x * 2 * 1000000)
                if min_voltage_x < 0 < max_voltage_x:
                    ax1.set_ylim(min_voltage_x * 2 * 1000000, max_voltage_x * 2 * 1000000)
                if min_voltage_x < max_voltage_x < 0:
                    ax1.set_ylim(min_voltage_x * 2 * 1000000, max_voltage_x * 1 / 2 * 1000000)

                if voltages[1] > max_voltage_y:
                    max_voltage_y = voltages[1]
                if voltages[1] < min_voltage_y:
                    min_voltage_y = voltages[1]

                if min_voltage_y > 0 < max_voltage_y:
                    ax2.set_ylim(min_voltage_y * 1000000 / 2, max_voltage_y * 2 * 1000000)
                if min_voltage_y < 0 < max_voltage_y:
                    ax2.set_ylim(min_voltage_y * 2 * 1000000, max_voltage_y * 2 * 1000000)
                if min_voltage_y > max_voltage_y > 0:
                    ax2.set_ylim(min_voltage_y * 2 * 1000000, max_voltage_y * 1 / 2 * 1000000)

                plt.tight_layout()
                ax1.get_yaxis().get_major_formatter().set_useOffset(False)
                ax2.get_yaxis().get_major_formatter().set_useOffset(False)
                fig.canvas.draw()
            plt.savefig(imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
        except KeyboardInterrupt:
            plt.savefig(imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
            exit