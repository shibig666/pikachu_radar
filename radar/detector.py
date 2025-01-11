from radar import types
from radar.transform import Transformer
from ultralytics import YOLO
import json
import logging
import numpy as np


# 装甲板检测器
class Detector:
    def __init__(self, car_path, armor_path, map_path, first_image,
                 car_iou=0.7, car_conf=0.25, car_half=False,
                 armor_iou=0.5, armor_conf=0.25, armor_half=False):
        self.armor_classes = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7']
        # 预测参数
        self.car_iou = car_iou
        self.car_conf = car_conf
        self.car_half = car_half
        self.armor_iou = armor_iou
        self.armor_conf = armor_conf
        self.armor_half = armor_half
        # 模型载入
        self.car_detector = YOLO(car_path)
        self.armor_detector = YOLO(armor_path)
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
                                                half=self.car_half)[0]
        cars_xyxy = result_cars.boxes.xyxy
        for i in range(len(cars_xyxy)):
            xyxy = list(map(int, cars_xyxy[i].cpu().tolist()))
            car = types.Car(xyxy, image[xyxy[1]:xyxy[3], xyxy[0]:xyxy[2]])

            result_armors = self.armor_detector.predict(car.image,
                                                        iou=self.armor_iou,
                                                        conf=self.armor_conf,
                                                        half=self.armor_half)[0]
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
