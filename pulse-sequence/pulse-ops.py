#!/home/esther/.local/venvs/python-epics/bin/python3
#
#!/usr/bin/env python3
"""
https://stackoverflow.com/questions/8241099/executing-tasks-in-parallel-in-python

"""

import argparse
import serial
import io
import signal
import time
import subprocess
from threading import Thread
from epics import caget, caput  # , cainfo

MFC_ST_FSETPOINT = 9.0  # Esther:MFC-ST:FSetpoint.HOPR
MFC_CT_FSETPOINT = 10.0  # Esther:MFC-CT:FSetpoint.HOPR


class GracefulKiller:
    keep_run = True

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        print('Got SIGNAL')
        self.keep_run = False


killer = GracefulKiller()


class kistlerCom():
    """
    Serial connection to Kistler 5015 on CC
    """

    # def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=115200,
    def __init__(self, serial_port='/dev/ttyKistler', baud_rate=115200,
                 read_timeout=1):
        """
        Initializes the serial connection to the Kistler Charge Meter
        """
        self.ser = serial.Serial(serial_port, baud_rate, timeout=read_timeout)
        print(self.ser.name)         # check which port was really used
        # command = "CT0:CV\r".encode('utf-8')  # query firmware
        command = b"CT0:CV\r"  # .encode('utf-8')  # query firmware
        self.ser.write(command)
        # time.sleep(0.1)
        line = self.ser.readline()   # read a terminated line
        print(f"Kistler FW: {line}")
        self.sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser),
                                    newline="\r")

    def setRange(self, range=300):
        """
        """
        command = f"CH1:CT0:18,{range:d}\r".encode('utf-8')  # Command reply : define Reply Terminator <CR><LF>
        self.ser.write(command)
        # time.sleep(0.1)
        line = self.ser.readline()   # read a terminated line
        return line

    def measureReset(self, range=300):
        """
        """
# Command reply : define Reply Terminator <CR><LF>
        command = "CH1:CT0:RO0:RO1\r".encode('utf-8')
        self.ser.write(command)
#        command = "RO1\r".encode('utf-8')
#        self.ser.write(command)
        line = self.ser.readline()   # read a terminated line
        return line

    def measureReset0(self):
        """
        """
        # command = "RO0\r"
        # self.sio.write(unicode(command))
        self.sio.write("RO0\n")
        self.sio.flush()  # it is buffering. required to get the data out *now*
        time.sleep(0.1)
        command = "RO1\r"
        self.sio.write("RO1\n")
        self.sio.write(command)
        self.sio.flush()  # it is buffering. required to get the data out *now*
        time.sleep(0.1)
        line = self.sio.readline()   # read a '\n' terminated line
        print(f"Kistler reply: {line}")
        return line

    def measureActive(self, active=False):
        """
        Unicode strings must be encoded (e.g. 'hello'.encode('utf-8').
        """
        if active:
            # command = "RO1\r".encode('utf-8')
            command = "RO1\r".encode('utf-8')
        else:
            command = "RO0\r".encode('utf-8')
        # print(command)
        self.sio.write(command)
        self.sio.flush()  # it is buffering. required to get the data out *now*
        time.sleep(0.5)
        line = self.sio.readline()   # read a '\n' terminated line
        print(f"reply: {line}")
        return line

    def close(self):
        """
        To ensure we are properly closing our connection to the
        Arduino device.
        """
        self.ser.close()


class quantel():
    """
    Models an  Serial connection
    """

    def __init__(self, serial_port='/dev/ttyS0', baud_rate=9600,
                 read_timeout=2):
        """
        Initializes the serial connection to the Arduino board
        """
        self.ser = serial.Serial(serial_port, baud_rate, timeout=read_timeout)
        # self.ser.timeout = read_timeout  # Timeout for readline()
        self.sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser),
                                    newline="\r\n")

    def standBy(self):
        """
        Unicode strings must be encoded (e.g. 'hello'.encode('utf-8').
        """
        command = "S\r\n".encode('utf-8')
        # print(command)
        self.ser.write(command)
        time.sleep(0.5)
        line = self.ser.readline()   # read a '\n' terminated line
        print(f"reply: {line}")
        return line

    def armLaser(self):
        """
        """
        command = "S\r\n".encode('utf-8')
        self.ser.write(command)
        time.sleep(0.1)
        command = "Q010101\r\n".encode('utf-8')
        self.ser.write(command)
        time.sleep(0.1)
        command = "A\r\n".encode('utf-8')
        self.ser.write(command)
        time.sleep(0.1)
        command = "QI\r\n".encode('utf-8')
        self.ser.write(command)
        time.sleep(0.1)
        line = self.ser.readline()   # read a '\n' terminated line
        print(f"Quantel reply: {line}")
        return line

    def triggerQSwitch(self):
        """
        Unicode strings must be encoded (e.g. 'hello'.encode('utf-8').
        """
        command = "CC\r\n".encode('utf-8')
        self.ser.write(command)
        time.sleep(0.5)
        line = self.ser.readline()   # read a '\n' terminated line
        print(f"Quantel reply: {line}")
        return line

    def close(self):
        """
        To ensure we are properly closing our connection to the
        Arduino device.
        """
        self.ser.close()
        # print('Connection to Quantel Laser closed')


def parse_args():
    parser = argparse.ArgumentParser(
            description='Script to start ESTHER Operation Pulse')

    parser.add_argument('-r', '--host_rp', default='10.10.136.229',
                        help='Red Pitay IP address')
    parser.add_argument('-a', '--laserArm',
                        action='store_true', help='Arm Quantel Laser')
    parser.add_argument('-s', '--laserStandby',
                        action='store_true', help='Set Quantel in Standby')
    parser.add_argument('-c', '--redpitayaConfig',
                        action='store_true', help='Check Red Pitaya Config')
    parser.add_argument('-f', '--fire', action='store_true',
                        help='Fire ESTHER Pulse and acquisition')
    parser.add_argument('-t', '--trigger',
                        action='store_true',
                        help='Trigger Quantel Laser Q-Switch')
    parser.add_argument('-k', '--kistlerReset',
                        action='store_true', help='Reset Kistler')
    parser.add_argument('-g', '--kistlerRange',
                        type=int, default=0, help='Set Kistler Range')
    parser.add_argument('-m', '--mfcEpics', action='store_true',
                        help='Start Test Gases MFCs')
    return parser.parse_args()


def taskResetKistler():
    kt = kistlerCom()
    reply = kt.measureReset()
    kt.close()
    time.sleep(2)
    print("Task Reset Kistler Finished")


def task1():
    time.sleep(2)
    print("Task 1 Finished")


def taskRPitayaStart(host="10.10.136.233"):
    # list_files = subprocess.run(["ls", "-l"])
    # list_files = subprocess.run(["ls", "-l"], stdout=subprocess.DEVNULL)
    # print("The exit code was: %d" % list_files.returncode)
    time.sleep(0.5)
    rp_query = subprocess.run(["/home/esther/.local/bin/rpsa_client",
                               "--remote",
                               "--mode=start",
                               f"--hosts={host:s}"])
    print("RP Start %s  exit code was: %d" % (host, rp_query.returncode))


def taskFireQuantel():
    qt = quantel()
    time.sleep(1.0)
    reply = qt.triggerQSwitch()
    qt.close()
    print(reply)
    print("Trigger Quantel Finished")


def taskEpics():
    pt901 = caget("Esther:gas:PT901")
    print(f"PT901: {pt901:e}")
    flow_sp = caget("Esther:MFC-ST:FSetpoint")
    print(f"Flow SP: {flow_sp}")
    caput('Esther:MFC-CT:Reset', 1)
    caput('Esther:MFC-ST:Reset', 1)
    time.sleep(1.0)
    caput('Esther:MFC-CT:Reset', 0)
    caput('Esther:MFC-ST:Reset', 0)
    gvc = 1
    gvs = 0
    while killer.keep_run and (gvc == 0 or gvs == 0):
        gvc = caget('Esther:HVA:CTST-Valve')
        gvs = caget('Esther:HVA:STDT-Valve')
        print(f'GV-CTST: {gvc},  GV-STDT: {gvs}')
        time.sleep(1)  # Sleep seconds
    # caput("Esther:MFC-CT:FSetpoint", MFC_CT_FSETPOINT)
    # caput("Esther:MFC-ST:FSetpoint", MFC_ST_FSETPOINT)


def checkRPitayaConfig(host="10.10.136.232"):
    # list_files = subprocess.run(["ls", "-l"], stdout=subprocess.DEVNULL)
    # print("The exit code was: %d" % list_files.returncode)
    rp_query = subprocess.run(["/home/esther/.local/bin/rpsa_client",
                               "--config",
                               f"--hosts={host:s}",
                               "--get=VV"])
    print("RP exit code was: %d" % rp_query.returncode)
    # The subprocess.run() facilitates this by its input argument:


def task5():
    pass


def firePulse(host="10.10.136.223"):
    print("Firing Esther Pulse")
    t0 = Thread(target=taskResetKistler)
    t1 = Thread(target=taskRPitayaStart, args=(host,))
    t2 = Thread(target=taskFireQuantel)

    t0.start()
    t1.start()
    t2.start()

    t0.join()
    t1.join()
    t2.join()


if __name__ == '__main__':
    args = parse_args()

    if args.laserStandby:
        qt = quantel()
        reply = qt.standBy()
        qt.close()
        print(reply)
        exit()

    if args.laserArm:
        qt = quantel()
        reply = qt.armLaser()
        qt.close()
        print(reply)
        exit()

    if args.kistlerReset:
        kt = kistlerCom()
        reply = kt.measureReset()
        kt.close()
        print(reply)
        exit()

    if args.kistlerRange > 0:
        kt = kistlerCom()
        reply = kt.setRange(args.kistlerRange)
        kt.close()
        print(reply)
        exit()

    if args.trigger:
        qt = quantel()
        reply = qt.triggerQSwitch()
        qt.close()
        print(reply)
        print("Trigger Quantel Finished")
        exit()

    if args.redpitayaConfig:
        checkRPitayaConfig(args.host_rp)
        exit()

    if args.fire:
        firePulse(args.host_rp)

    if args.mfcEpics:
        t1 = Thread(target=taskEpics)
        t1.start()
        t1.join()

    print("Program Finished")
    # if your arduino was running on a serial port other than '/dev/ttyACM0/'
    # declare: qt = quantel(serial_port='/dev/ttyXXXX')


"""
    def moveTo(self, motor_number, value):
        Internally sends b'WD{pin_number}:{digital_value}' over the serial
        connection
        Unicode strings must be encoded (e.g. 'hello'.encode('utf-8').
        command = f'M{motor_number} {value}\r\n'.encode('utf-8')
        print(command)
        self.ser.write(command)
        return line
"""

# vim: syntax=python ts=4 sw=4 sts=4 sr et
