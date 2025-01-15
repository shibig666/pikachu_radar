from radar import types
from radar.transform import Transformer
from ultralytics import YOLO
import torch
import os
import json
from PyQt6.QtWidgets import QMessageBox



# 装甲板检测器
class Detector:
    def __init__(self, model_path, map_path, first_image, config_path, tensorRT=False):
        if tensorRT and not torch.cuda.is_available():
            QMessageBox.warning(None, "警告", "TensorRT需要CUDA支持")
            return
        self.tensorRT = tensorRT if torch.cuda.is_available() else False
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.armor_classes = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7']
        # 预测参数
        config = json.load(open(config_path))
        self.car_iou = config["data"]["car"]["iou"]
        self.car_conf = config["data"]["car"]["conf"]
        self.car_half = config["data"]["car"]["half"]
        self.armor_iou = config["data"]["armor"]["iou"]
        self.armor_conf = config["data"]["armor"]["conf"]
        self.armor_half = config["data"]["armor"]["half"]
        self.data_queue = None
        # 模型载入
        if tensorRT:
            self.car_detector = YOLO(os.path.join(model_path, 'car.engine'),task="detect")
            self.armor_detector = YOLO(os.path.join(model_path, 'armor.engine'),task="detect")
        else:
            self.car_detector = YOLO(os.path.join(model_path, 'car.pt'))
            self.armor_detector = YOLO(os.path.join(model_path, 'armor.pt'))
        # 识别到的机器人
        self.cars = []
        # 载入地图
        self.Transformer = Transformer(map_path, config_path="config/transform.json",
                                       first_image=first_image)
        self.result_map_image = None

    # 检测
    def detect(self, image):
        # 清空之前的识别结果
        self.cars = []
        # 识别机器人
        result_cars = self.car_detector.predict(image,
                                                iou=self.car_iou,
                                                conf=self.car_conf,
                                                half=self.car_half,
                                                device=self.device,
                                                verbose=False)[0]
        cars_xyxy = result_cars.boxes.xyxy
        for i in range(len(cars_xyxy)):
            xyxy = list(map(int, cars_xyxy[i].cpu().tolist()))
            car = types.Car(xyxy, image[xyxy[1]:xyxy[3], xyxy[0]:xyxy[2]])

            result_armors = self.armor_detector.predict(car.image,
                                                        iou=self.armor_iou,
                                                        conf=self.armor_conf,
                                                        half=self.armor_half,
                                                        device=self.device,
                                                        imgsz=320,
                                                        verbose=False)[0]
            armors_xyxy = result_armors.boxes.xyxy
            armors_cls = result_armors.boxes.cls
            for armor_xyxy, armor_cls in zip(armors_xyxy, armors_cls):
                armor_type = self.armor_classes[int(armor_cls)]
                armor_color = 'red' if armor_type[0] == 'R' else 'blue'
                armor_xyxy = list(map(int, armor_xyxy))
                armor = types.Armor(armor_type, armor_color, armor_xyxy)
                car.add_armor(armor)

            self.Transformer.transform(car)
            car.calculate_type()
            car.calculate_id()
            self.cars.append(car)

        # print(f"Detected {len(self.cars)} cars")
        self.result_map_image = self.Transformer.plot_cars(self.cars)

        return self.result_map_image

    def plot_cars(self, image):
        for car in self.cars:
            image = car.plot(image)
        return image

    def display(self):
        for car in self.cars:
            print(f"Car ID: {car.id}, Type: {car.type},Armors:{len(car.armors)}")
