import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox

from CameraPlayer import CameraMainWindow  # 引入摄像头播放窗口
from VideoPlayer import PlayerMainWindow
from ui.RadarChoiceWidget import Ui_RadarChoiceWidget


class ChoiceWidget(QMainWindow, Ui_RadarChoiceWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.VideoButton.clicked.connect(self.select_video)
        self.CameraButton.clicked.connect(self.select_camera)
        self.player_window = None  # 存储播放器窗口
        self.camera_window = None  # 存储摄像头窗口

    def select_video(self):
        """选择视频文件并打开视频播放器"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter('视频文件 (*.mp4 *.avi *.mkv *.mov *.flv)')

        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            use_tensorrt = self.checkBoxTensorrt.isChecked()
            use_serial = self.checkBoxSerial.isChecked()

            if self.radioButtonRed.isChecked() == self.radioButtonBlue.isChecked():
                QMessageBox.warning(self, "警告", "请选择敌方颜色")
                return

            enemy_color = "R" if self.radioButtonRed.isChecked() else "B"

            self.hide()  # 仅隐藏主窗口，不关闭
            self.player_window = PlayerMainWindow()  # 赋值给实例变量
            self.player_window.show()
            self.player_window.init(selected_file, use_tensorrt, use_serial, enemy_color)
            self.player_window.start_video()

    def select_camera(self):
        """打开 USB 摄像头"""
        use_tensorrt = self.checkBoxTensorrt.isChecked()
        use_serial = self.checkBoxSerial.isChecked()

        if self.radioButtonRed.isChecked() == self.radioButtonBlue.isChecked():
            QMessageBox.warning(self, "警告", "请选择敌方颜色")
            return

        enemy_color = "R" if self.radioButtonRed.isChecked() else "B"

        self.hide()
        self.camera_window = CameraMainWindow()  # 赋值给实例变量
        self.camera_window.show()
        self.camera_window.init(use_tensorrt, use_serial, enemy_color)
        self.camera_window.start_camera()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    choice_widget = ChoiceWidget()
    choice_widget.show()
    sys.exit(app.exec())  # 保证应用程序持续运行
