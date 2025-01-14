import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from ui.RadarChoiceWidget import *
from VideoPlayer import PlayerMainWindow


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
            selected_file = file_dialog.selectedFiles()[0]  # 选择的文件
            use_tensorrt = self.checkBoxTensorrt.isChecked()  # 是否使用tensorRT
            use_serial = self.checkBoxSerial.isChecked()  # 是否使用串口
            enemy_color = "R" if self.radioButtonRed.isChecked() else "B"  # 敌方颜色
            self.close()
            player_main_window.show()
            player_main_window.init(selected_file, use_tensorrt, use_serial, enemy_color)
            player_main_window.start_video()

    def select_camera(self):
        QMessageBox.information(self, "提示", "摄像头功能暂未开放")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    choice_widget = ChoiceWidget()
    player_main_window = PlayerMainWindow()
    choice_widget.show()
    sys.exit(app.exec())
