import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem, QTableWidget
from PyQt6.QtGui import QImage, QPixmap, QStandardItemModel, QStandardItem
from PyQt6.QtCore import QTimer
from ui.RadarChoiceWidget import *
from ui.RadarPlayerMainWindow import *
from radar.detector import Detector
import cv2
import time
import multiprocessing as mp

from radar.serial.myserial import SerialPort
from radar.types import get_armor_type
from VideoPlayer import PlayerMainWindow


# 实例化串口对象
# sp = SerialPort(list_available_ports())


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
            use_tensorrt = self.checkBoxTensorrt.isChecked()
            use_serial = self.checkBoxSerial.isChecked()
            self.close()
            player_main_window.show()
            player_main_window.init(selected_file, use_tensorrt, use_serial)
            player_main_window.start_video()

    def select_camera(self):
        QMessageBox.information(self, "提示", "摄像头功能暂未开放")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    choice_widget = ChoiceWidget()
    player_main_window = PlayerMainWindow()
    choice_widget.show()
    sys.exit(app.exec())
