from radar import type
from ultralytics import YOLO
import logging
import numpy as np


# 装甲板检测器
class Detector:
    def __init__(self, car_path, armor_path, map_path):
        self.armor_classes = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7']
        # 模型载入
        self.car_detector = YOLO(car_path)
        self.armor_detector = YOLO(armor_path)
        # 识别到的机器人
        self.cars = []
        # 载入地图
        self.map = type.Map(map_path)

    # 检测
    def detect(self, image):
        # 清空之前的识别结果
        self.cars = []
        # 识别机器人
        result_cars = self.car_detector(image)
        for cr in result_cars:
            # 获取机器人框
            car_box = cr["boxes"]
            xyxy = car_box.xyxy.cpu().numpy().astype(int)
            car_xyxy = type.Car(xyxy, image[xyxy[1]:xyxy[3], xyxy[0]:xyxy[2]])
            result_armors = self.armor_detector(car_xyxy.image)
            for ar in result_armors:
                armor_box = ar["boxes"]
                armor_type = self.armor_classes[ar.Probs.top1]
                armor_color = 'red' if armor_type[0] == 'R' else 'blue'
                armor = type.Armor(armor_type, armor_color, armor_box)
                car_xyxy.add_armor(armor)
            car_xyxy.calculate_type()
            car_xyxy.calculate_id()
            self.cars.append(car_xyxy)

        logging.info(f"Detected {len(self.cars)} cars")

    def display(self):
        for car in self.cars:
            logging.info(f"Car ID: {car.id}, Type: {car.type}")
