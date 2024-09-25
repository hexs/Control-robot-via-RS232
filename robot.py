import time
from datetime import datetime, timedelta
import serial
from typing import Dict, Union, List


class Robot:
    def __init__(self, port: str, baudrate: int = 38400):
        self.ser = serial.Serial(port=port, baudrate=baudrate)
        print(f"Connected to: {self.ser.portstr}")

        self.current_position_vel: Dict[str, int] = {'01': 0, '02': 0, '03': 0, '04': 0}
        self.send_data_last_datetime = datetime.now()
        self.buffer = bytearray()

    @staticmethod
    def LRC_calculation(message: str) -> bytes:
        sum_of_bytes = sum(int(message[i:i + 2], 16) for i in range(0, len(message), 2))
        error_check = f'{(0x100 - sum_of_bytes) & 0xFF:02X}'
        return f':{message}{error_check}\r\n'.encode()

    def send_data_(self, slave_address: str, function_code: str, register_address: str, *args: str) -> None:
        while (datetime.now() - self.send_data_last_datetime) <= timedelta(milliseconds=20):
            time.sleep(0.001)

        self.send_data_last_datetime = datetime.now()
        message = f'{slave_address}{function_code}{register_address}{"".join(args)}'
        message = self.LRC_calculation(message)
        print(f"Sending: {message} len: {len(message)}")
        self.ser.write(message)

    def send_data(self, slave_address: Union[str, List[str]], function_code: str, register_address: str,
                  *args: str) -> None:
        if slave_address == 'all':
            for addr in ['01', '02', '03', '04']:
                self.send_data_(addr, function_code, register_address, *args)
        else:
            self.send_data_(slave_address, function_code, register_address, *args)

    def servo(self, on: bool = True) -> None:
        print('Servo ON' if on else 'Servo OFF')
        self.send_data('all', '05', '0403', 'FF00' if on else '0000')

    def alarm_reset(self) -> None:
        print('Alarm reset')
        self.send_data('all', '05', '0407', 'FF00')
        self.send_data('all', '05', '0407', '0000')

    def pause(self, pause=True) -> None:
        print('Pause' if pause else 'Un pause')
        self.send_data('all', '05', '040A', 'FF00' if pause else '0000')

    def home(self) -> None:
        print('Home')
        self.send_data('all', '05', '040B', 'FF00')
        self.send_data('all', '05', '040B', '0000')

    def jog(self, slave: str, positive_side: bool, move: bool) -> None:
        register = '0416' if positive_side else '0417'
        data = 'FF00' if move else '0000'
        self.send_data(slave, '05', register, data)
        self.current_position()

    def current_position(self) -> None:
        print('Read Current Position')
        self.send_data('all', '03', '9000', '0002')

    def move_to(self, row: int) -> None:
        self.send_data('all', '06', '9800', f'{row:04X}')

    def set_to(self, slave: str, row: int, position: float, speed: float, acc: float, dec: float) -> None:
        position = int(position * 100) & 0xFFFFFFFF
        speed = int(speed * 100)
        acc = int(acc * 100)
        dec = int(dec * 100)

        self.send_data(
            slave,
            '10',
            f'{0x100 + row:03X}0',  # start_address
            '000F',  # number_of_regis
            '1E',  # number_of_bytes
            f'{position:08X}',  # data 1,2 |target position = 100 (mm) x 100 = 10000 → 00002710
            '0000',
            '000A',
            f'{speed:08X}',  # data 5,6 |speed = 200 (mm/sec) x 100 = 20000 → 00004E20
            '0000',
            '1770',
            '0000',
            '0FA0',
            f'{acc:04X}',  # data 11 |acceleration =0.01 (G) x 100 = 1 → 0001
            f'{dec:04X}',  # data 12 |deceleration =0.3 (G) x 100 = 30 → 001E
            '0000',
            '0000',
            '0000',
        )
        time.sleep(0.5)

    def evens(self, string: str) -> None:
        if len(string) == 17 and string[3:7] == '0304':
            slave = string[1:3]
            vel = int(string[7:-2], 16)
            if vel > 0x7FFFFFFF:
                vel -= 0x100000000
            print(slave, vel, hex(vel))
            self.current_position_vel[slave] = vel

    def run(self) -> None:
        if self.ser.in_waiting:
            data_ = self.ser.read(self.ser.in_waiting)
            self.buffer.extend(data_)
            while b'\r\n' in self.buffer:
                message, self.buffer = self.buffer.split(b'\r\n', 1)
                if message.startswith(b':'):
                    print(f'receive: {message + b"\r\n"}')
                    self.evens(message.decode())


if __name__ == '__main__':
    robot = Robot('COM13', baudrate=38400)
    robot.move_to(0)
    time.sleep(2)
    robot.move_to(8)
    time.sleep(0.5)
    robot.pause()
