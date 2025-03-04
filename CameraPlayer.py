import sys
import cv2
import time
import multiprocessing as mp
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt6.QtGui import QImage, QPixmap, QColor
from PyQt6.QtCore import QTimer
from ui.RadarPlayerMainWindow import Ui_RadarPlayerMainWindow
from radar.detector import Detector
from radar.serial.myserial import SerialPort
from radar.types import get_armor_type


class CameraMainWindow(QMainWindow, Ui_RadarPlayerMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # 变量初始化
        self.enemy_color = None
        self.use_serial = None
        self.use_tensorrt = None
        self.cap = None  # 相机捕获
        self.detector = None
        self.queues = None
        self.event = None
        self.time = 0
        self.paused = False  # 是否暂停
        self.timer = QTimer()  # 视频帧定时器
        self.timer.timeout.connect(self.update_frame)
        self.console_timer = QTimer()  # 串口定时器
        self.console_timer.timeout.connect(self.update_console)

        # 绑定按钮事件
        self.PauseButton.clicked.connect(self.toggle_pause)

    def init(self, use_tensorrt, use_serial, enemy_color):
        self.use_tensorrt = use_tensorrt
        self.use_serial = use_serial
        self.enemy_color = enemy_color

        # 设置敌方颜色
        self.enemyColorLabel.setText(f"敌方颜色: {enemy_color}")
        palette = self.enemyColorLabel.palette()
        palette.setColor(self.enemyColorLabel.foregroundRole(), QColor("red") if enemy_color == "R" else QColor("blue"))
        self.enemyColorLabel.setPalette(palette)

        # 打开 USB 端相机
        self.cap = cv2.VideoCapture(1)  # 0 表示默认相机
        if not self.cap.isOpened():
            QMessageBox.warning(self, "警告", "无法打开相机")
            return

        # 获取 FPS
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps == 0:
            self.fps = 30  # 设置默认值

        # 读取第一帧作为初始化
        ret, frame = self.cap.read()
        if not ret:
            QMessageBox.warning(self, "警告", "无法读取相机画面")
            self.close()
            return

        # 如果使用串口通信
        if use_serial:
            self.queues = [mp.Queue(), mp.Queue()]
            self.event = mp.Event()
            self.console_timer.start(10)
            sp = SerialPort("COM1", enemy_color, self.queues, self.event)
            serial_process = mp.Process(target=sp.serial_task)
            serial_process.start()

        # 初始化检测器
        self.detector = Detector("weights", "interface/map.png", frame, config_path="config/predict.json",
                                 tensorRT=self.use_tensorrt)

    def start_camera(self):
        """开始从 USB 端相机获取视频流"""
        if self.cap is None:
            return
        self.timer.start(int(1000 / self.fps))

    def update_console(self):
        """更新串口数据"""
        if not self.queues[1].empty():
            byte_data = self.queues[1].get()
            self.ConsoleText.appendPlainText(byte_data)

    def update_frame(self):
        """更新相机画面"""
        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            return

        # 处理检测和绘制
        result_map = cv2.cvtColor(self.detector.detect(frame), cv2.COLOR_RGB2BGR)
        result_img = cv2.cvtColor(self.detector.plot_cars(frame), cv2.COLOR_RGB2BGR)

        # 缩放图像
        result_img = cv2.resize(result_img, (960, 540))
        result_map = cv2.resize(result_map, (700, 375))

        # 转换为 QImage
        result_map_qimg = QImage(result_map.data, result_map.shape[1], result_map.shape[0], QImage.Format.Format_RGB888)
        result_img_qimg = QImage(result_img.data, result_img.shape[1], result_img.shape[0], QImage.Format.Format_RGB888)

        # 更新 UI 界面
        fps = int(1 / (time.time() - self.time))
        self.time = time.time()
        self.fpsLabel.setText(f"FPS: {fps}")
        self.MapLabel.setPixmap(QPixmap.fromImage(result_map_qimg))
        self.VideoLabel.setPixmap(QPixmap.fromImage(result_img_qimg))

        # 串口发送数据
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

    def toggle_pause(self):
        """暂停/播放相机画面"""
        if self.paused:
            self.paused = False
            self.PauseButton.setText("暂停")
            self.timer.start(int(1000 / self.fps))
        else:
            self.paused = True
            self.PauseButton.setText("播放")
            self.timer.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    camera_window = CameraMainWindow()
    camera_window.init(use_tensorrt=False, use_serial=False, enemy_color="R")
    camera_window.start_camera()
    camera_window.show()
    sys.exit(app.exec())
