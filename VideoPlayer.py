# 播放器功能实现
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtGui import QImage, QPixmap, QStandardItemModel, QStandardItem
from PyQt6.QtCore import QTimer
from ui.RadarPlayerMainWindow import *
from radar.detector import Detector
import cv2
import time
import multiprocessing as mp

from radar.serial.myserial import SerialPort
from radar.types import get_armor_type


class PlayerMainWindow(QMainWindow, Ui_RadarPlayerMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_model = None
        self.current_frame = None  # 当前帧
        self.frame_count = None  # 总帧数
        self.fps = None  # 帧率
        self.event = None  # 串口事件
        self.queues = None  # 串口队列
        self.cap = None  # 视频捕获
        self.use_serial = None  # 是否使用串口
        self.use_tensorrt = None  # 是否使用tensorRT
        self.setupUi(self)  # 初始化UI
        self.video_file = None  # 视频文件
        self.detector = None  # 检测器对象
        self.first_image = None  # 第一帧图像
        self.timer = QTimer()  # 播放视频定时器
        self.timer.timeout.connect(self.update_frame)
        self.console_timer = QTimer()  # 串口终端定时器
        self.console_timer.timeout.connect(self.update_console)
        self.init_table()  # 初始化表格
        self.paused = False  # 是否暂停
        self.NextButton.clicked.connect(self.next_frame)
        self.PauseButton.clicked.connect(self.toggle_pause)
        self.horizontalSlider.valueChanged.connect(self.update_video_position)
        self.time = 0

    def open_video(self, video_file):
        cap = cv2.VideoCapture(video_file)
        if not cap.isOpened():
            QMessageBox.warning(self, "警告", "视频文件打开失败")
            return False
        ret, frame = cap.read()
        if not ret:
            QMessageBox.warning(self, "警告", "视频文件读取失败")
            return False
        return cap

    def init(self, video_file, use_tensorrt, use_serial):
        self.use_tensorrt = use_tensorrt
        self.use_serial = use_serial
        self.video_file = video_file
        self.cap = self.open_video(video_file)
        if not self.cap:
            self.close()
            return
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        self.first_image = None
        ret, frame = self.cap.read()
        if not ret:
            QMessageBox.warning(self, "警告", "视频文件读取失败")
            self.close()
            return
        if use_serial:
            self.queues = [mp.Queue(), mp.Queue()]
            self.event = mp.Event()
            self.console_timer.start(10)
            sp = SerialPort("COM1", "R", self.queues, self.event)
            serial_process = mp.Process(target=sp.serial_task())
            serial_process.start()
        self.first_image = frame
        self.detector = Detector("weights", "interface/map.png", self.first_image, config_path="config/predict.json",
                                 tensorRT=self.use_tensorrt)

    def init_table(self):
        # 创建标准项模型
        self.item_model = QStandardItemModel(self)
        self.item_model.setHorizontalHeaderLabels(["ID", "Type", "Center X", "Center Y", "Map X", "Map Y"])

        # 设置表格模型
        self.CarTableView.setModel(self.item_model)
        self.CarTableView.verticalHeader().setVisible(False)  # 隐藏行号
        # 设置每列的固定宽度
        self.CarTableView.setColumnWidth(0, 100)
        self.CarTableView.setColumnWidth(1, 150)
        self.CarTableView.setColumnWidth(2, 120)
        self.CarTableView.setColumnWidth(3, 120)
        self.CarTableView.setColumnWidth(4, 150)
        self.CarTableView.setColumnWidth(5, 150)

    def start_video(self):
        if self.cap is None:
            return
        self.timer.start(int(1000 / self.fps))

    def update_console(self):
        if not self.queues[1].empty():
            byte_data = self.queues[1].get()
            self.ConsoleText.appendPlainText(byte_data)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            self.cap.release()
            return

        self.current_frame += 1
        self.horizontalSlider.setValue(int(self.current_frame / self.frame_count * 100))

        # 处理检测和绘制
        result_map = cv2.cvtColor(self.detector.detect(frame), cv2.COLOR_RGB2BGR)
        result_img = cv2.cvtColor(self.detector.plot_cars(frame), cv2.COLOR_RGB2BGR)

        # 缩放图像到指定尺寸
        result_img = cv2.resize(result_img, (960, 540))
        result_map = cv2.resize(result_map, (700, 375))

        # 转换为 QImage
        result_map_qimg = QImage(result_map.data, result_map.shape[1], result_map.shape[0], QImage.Format.Format_RGB888)
        result_img_qimg = QImage(result_img.data, result_img.shape[1], result_img.shape[0], QImage.Format.Format_RGB888)

        # 更新显示内容
        fps = int(1 / (time.time() - self.time))
        self.time = time.time()
        self.fpsLabel.setText(f"FPS: {fps}")
        self.MapLabel.setPixmap(QPixmap.fromImage(result_map_qimg))
        self.VideoLabel.setPixmap(QPixmap.fromImage(result_img_qimg))
        self.update_table()

        # 串口发送
        if self.use_serial:
            send_data = []
            for car in self.detector.cars:
                if car.id == "-1":
                    continue
                send_data.append({
                    "ID": get_armor_type(car.id),
                    "position": car.xy_in_map,
                })
            self.queues[0].put(send_data)
            self.event.set()

    def update_table(self):
        self.item_model.removeRows(0, self.item_model.rowCount())
        cars = sorted(self.detector.cars, key=lambda x: x.id)
        for i, car in enumerate(cars):
            self.item_model.appendRow([
                QStandardItem(str(car.id)),
                QStandardItem(car.type),
                QStandardItem(str(car.center[0])),
                QStandardItem(str(car.center[1])),
                QStandardItem(str(car.xy_in_map[0])),
                QStandardItem(str(car.xy_in_map[1])),
            ])

    def next_frame(self):
        if self.cap is None:
            return
        self.current_frame += 1
        if self.current_frame >= self.frame_count:
            self.current_frame = 0
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        self.update_frame()

    def toggle_pause(self):
        if self.paused:
            self.paused = False
            self.PauseButton.setText("暂停")
            self.timer.start(1000 / self.fps)
        else:
            self.paused = True
            self.PauseButton.setText("播放")
            self.timer.stop()

    def update_video_position(self):
        if self.cap is None:
            return
        position = self.horizontalSlider.value()
        self.current_frame = int(position * self.frame_count / 100)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        self.update_frame()
