import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer
from ui.RadarChoiceWidget import *
from ui.RadarMainWindow import *
from radar.detector import Detector
import cv2
import threading

video_file = None


class ChoiceWidget(QMainWindow, Ui_RadarChoiceWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.VideoButton.clicked.connect(self.select_video)
        self.CameraButton.clicked.connect(self.select_camera)

    def select_video(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter('视频文件 (*.mp4 *.avi *.mkv *.mov *.flv)')

        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            global video_file
            video_file = selected_file
            main_window.show()
            main_window.init(video_file)
            main_window.start_video()
            self.close()


    def select_camera(self):
        QMessageBox.information(self, "提示", "摄像头功能暂未开放")


class MainWindow(QMainWindow, Ui_RadarMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.video_file = None
        self.detector = None
        self.first_image = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

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

    def init(self, video_file):
        self.video_file = video_file
        cap = self.open_video(video_file)
        if not cap:
            self.close()
        ret, frame = cap.read()
        if not ret:
            QMessageBox.warning(self, "警告", "视频文件读取失败")
            self.close()
            return
        self.first_image = frame
        cap.release()
        self.detector = Detector("weights/car.pt",
                                 "weights/armor.pt",
                                 "interface/map.png",
                                 self.first_image)

    def start_video(self):
        self.cap = self.open_video(self.video_file)
        if not self.cap:
            self.close()
            return
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            print("无法获取视频帧率")
            self.close()
            return
        frame_interval = int(1000 / fps)
        self.timer.start(frame_interval)

    def update_frame(self):
        # 读取下一帧
        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            self.cap.release()
            return

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
        self.MapLabel.setPixmap(QPixmap.fromImage(result_map_qimg))
        self.VideoLabel.setPixmap(QPixmap.fromImage(result_img_qimg))

        # 获取当前帧数（可选，用于调试或显示）
        current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        print(f"当前帧数: {current_frame}")






if __name__ == "__main__":
    app = QApplication(sys.argv)
    choice_widget = ChoiceWidget()
    main_window = MainWindow()
    choice_widget.show()
    sys.exit(app.exec())
