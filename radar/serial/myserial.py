# rx 0x020c 0x020E  tx 0x0305
import time
import serial
from radar.serial.crc import *
import struct
import serial.tools.list_ports
import multiprocessing as mp
import threading as td
import queue as qu
import binascii


# 串口通信类
class SerialPort:
    def __init__(self, COM, team, queues, event):
        # 初始化串口
        self.SOF = 0xA5
        self.queues = queues
        self.queue_from_yolo = queues[0]
        self.update_txdata_flag = event
        is_open = False
        while not is_open:
            try:
                self.ser = serial.Serial(
                    port=COM,
                    baudrate=115200,
                    bytesize=serial.EIGHTBITS,
                    stopbits=serial.STOPBITS_ONE,
                    parity=serial.PARITY_NONE,
                    timeout=None,
                    write_timeout=None,
                )
            except Exception as e:
                print("串口打开失败。")
                send_console("串口打开失败。", self.queues[1])
                print(e)
            if self.ser.isOpen():
                print("串口打开成功。")
                send_console("串口打开成功。", self.queues[1])
                is_open = True
            else:
                print("串口打开失败。")
                send_console("串口打开失败。", self.queues[1])
                time.sleep(1)
        self.base_ids = {
            "B": [1, 2, 3, 4, 5, 7],
            "R": [101, 102, 103, 104, 105, 107],
        }
        self.enemy_team_ids = self.base_ids.get(team)
        if team == "B":
            self.my_id = 109
            self.plane_id = 106
        else:
            self.my_id = 9
            self.plane_id = 6

        class RefereeInfo:
            def __init__(self) -> None:
                self.double_flag = 0
                self.count = 0
                self.mark_data = {}
                self.double_state = 0
                self.info_dict = {}
                self.enemy_team_ids= None

        self.SEQ = 0x0  # 序列号
        self.send_count = 0x0  # 发送双倍易伤计数
        self.referee_info = RefereeInfo()
        self.txdouble_flag = td.Event()  # 由接收线程设置，发送线程清除
        self.show_info_flag = td.Event()  # 由接收线程设置，发送线程清除
        self.hardware_lock = td.Lock()
        self.queue_from_rx = qu.Queue()

    def close(self):
        # 关闭串口
        if self.ser.isOpen():
            self.ser.close()
            print("串口关闭成功。")
        else:
            print("串口关闭失败。")

    def reset_seq(self):
        if self.SEQ > 0xFF:
            self.SEQ = 0

    def tx_pos_thread(self):
        # 发送数据
        while 1:
            with self.hardware_lock:
                # 构建消息
                message = bytes([self.SOF, 24, 0x00, self.SEQ])
                message += append_crc8(message[:4])
                message += bytes([0x05, 0x03])
                for id in self.enemy_team_ids:
                    if id not in self.referee_info.info_dict:
                        self.referee_info.info_dict[id] = {"position": (0, 0)}
                    # print(str(id)+str(self.referee_info.info_dict[id]))
                    message += struct.pack(
                        "<HH",
                        self.referee_info.info_dict[id]["position"][0],
                        self.referee_info.info_dict[id]["position"][1],
                    )
                    self.referee_info.info_dict[id]["position"] = (0, 0)
                message += append_crc16(message)
                self.SEQ += 1
                if self.SEQ > 0xFF:
                    self.SEQ = 0
                self.ser.write(message)
                print_bytes(message, self.queues[1])
                time.sleep(0.2)  #  发送频率为5Hz

    def tx_double_thread(self):
        while 1:
            self.txdouble_flag.wait()
            with self.hardware_lock:
                message = bytes([self.SOF, 0x07, 0x00, self.SEQ])
                message += append_crc8(message[:4])
                message += bytes(
                    [0x01, 0x03, 0x21, 0x01, self.my_id >> 8, self.my_id & 0xFF, 0x80, 0x80]
                )
                if self.referee_info.double_state != 1 and self.referee_info.count > 0:
                    self.send_count += 1
                    if self.send_count == 1:
                        message += bytes([1])
                    elif self.send_count >= 2:
                        message += bytes([2])
                else:
                    message += bytes([0])
                message += append_crc16(message)
                self.SEQ += 1
                self.reset_seq()
                self.ser.write(message)
                self.txdouble_flag.clear()
                print("send double data")
                send_console("send double data", self.queues[1])

    def tx_show_info_thread(self):  # 走机间通信给云台手发数据
        while 1:
            self.show_info_flag.wait()
            with self.hardware_lock:
                message = bytes([self.SOF, 0x05, 0x00, self.SEQ])
                message += append_crc8(message[:4])
                message += bytes(
                    [
                        0x01,
                        0x03,
                        self.my_id >> 8,
                        self.my_id & 0xFF,
                        self.plane_id >> 8,
                        self.plane_id & 0xFF,
                        self.referee_info.count,
                        self.referee_info.double_state,
                    ]
                )
                message += append_crc16(message)
                self.SEQ += 1
                self.reset_seq()
                self.ser.write(message)
                self.show_info_flag.clear()
                print("send show info data")
                send_console("send show info data", self.queues[1])

    def update_txdata_thread(self):
        while 1:
            self.update_txdata_flag.wait()
            if not self.queue_from_yolo.empty():
                data = self.queue_from_yolo.get()
                # print(data)
                for i in range(len(data)):
                    try:
                        if data[i]["ID"] in self.enemy_team_ids:
                            self.referee_info.info_dict[data[i]["ID"]]["position"] = data[i]["position"]
                    except KeyError:
                        print("未找到ID"+data[i]["ID"])
            # if not self.queue_from_rx.empty():
            #     data = self.queue_from_rx.get()
            #     for id in enemy_team_ids:
            #         self.referee_info.info_dict[id]["position"] = data[id]
            self.update_txdata_flag.clear()

    def tx_task(self):
        th1 = td.Thread(target=self.tx_pos_thread)
        th1.start()
        th2 = td.Thread(target=self.tx_double_thread)
        th2.start()
        th3 = td.Thread(target=self.tx_show_info_thread)
        th3.start()
        th4 = td.Thread(target=self.update_txdata_thread)
        th4.start()

    def rx(self):
        while 1:
            if self.ser.read(1) != b"\xA5":
                continue

            frame_header = bytes([0xA5]) + self.ser.read(4)
            if not verify_crc8(frame_header):
                continue

            data_length = struct.unpack("<H", frame_header[1:3])[0]
            data = frame_header + self.ser.read(data_length + 4)
            if not verify_crc16(data):
                continue

            cmd_id = struct.unpack("<H", data[5:7])[0]

            if cmd_id == 0x020C:
                for i in range(6):
                    self.referee_info.mark_data[self.enemy_team_ids[i]] = data[7] & (
                            0b1 << i
                    )
                print("mark data: ", self.referee_info.mark_data)
                send_console("mark data: " + str(self.referee_info.mark_data), self.queues[1])

            elif cmd_id == 0x020E:
                if self.referee_info.count == (
                        data[7] & 0b11
                ) and self.referee_info.double_state == (data[7] & 0b100):
                    continue
                self.referee_info.count = data[7] & 0b11
                self.referee_info.double_state = data[7] & 0b100
                self.show_info_flag.set()
                print("count: ", self.referee_info.count)
                send_console("count: " + str(self.referee_info.count), self.queues[1])
                print("double state: ", self.referee_info.double_state)
                send_console("double state: " + str(self.referee_info.double_state), self.queues[1])

            elif cmd_id == 0x0105:
                if self.referee_info.double_flag == ((data[8] & 0b11000000) >> 6):
                    continue
                self.referee_info.double_flag = (data[8] & 0b11000000) >> 6
                self.txdouble_flag.set()

            elif cmd_id == 0x0305:
                self.update_txdata_flag.set()

            else:
                print("未知命令")
                send_console("未知命令", self.queues[1])

    def rx_task(self):
        rx_thread = td.Thread(target=self.rx)
        rx_thread.start()

    def serial_task(self):
        self.tx_task()
        self.rx_task()


# 列出可用端口
def list_available_ports():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "CH34" in port.description:
            return port.device
    return None


# 打印字节数据
def print_bytes(data, queue):
    hex_data = binascii.hexlify(data)
    hex_str = hex_data.decode("utf-8")
    hex_str_with_spaces = " ".join(
        hex_str[i: i + 2] for i in range(0, len(hex_str), 2)
    )
    # print("Bytes: " + hex_str_with_spaces)
    send_console("Bytes: " + hex_str_with_spaces, queue)

def send_console(data, queue):
    if queue is not None:
        queue.put(data)

# if __name__ == "__main__":
#     sp = SerialPort("COM1", "B")
#     serial_process = mp.Process(target=sp.serial_task())
#     serial_process.start()
