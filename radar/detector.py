from radar import types
from ultralytics import YOLO
import logging
import numpy as np


# 装甲板检测器
class Detector:
    def __init__(self, car_path, armor_path, map_path, threshold=0.8):
        self.armor_classes = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7']
        # 阈值
        self.threshold = threshold
        # 模型载入
        self.car_detector = YOLO(car_path)
        self.armor_detector = YOLO(armor_path)
        # 识别到的机器人
        self.cars = []
        # 载入地图
        self.map = types.Map(map_path)

    # 检测
    def detect(self, image):
        # 清空之前的识别结果
        self.cars = []
        # 识别机器人
        result_cars = self.car_detector.predict(image)[0]
        cars_xyxy = result_cars.boxes.xyxy
        for i in range(len(cars_xyxy)):
            xyxy = list(map(int, cars_xyxy[i].cpu().tolist()))
            car = types.Car(xyxy, image[xyxy[1]:xyxy[3], xyxy[0]:xyxy[2]])

            result_armors = self.armor_detector.predict(car.image)[0]
            armors_xyxy = result_armors.boxes.xyxy
            armors_cls = result_armors.boxes.cls
            for armor_xyxy, armor_cls in zip(armors_xyxy, armors_cls):
                armor_type = self.armor_classes[int(armor_cls)]
                armor_color = 'red' if armor_type[0] == 'R' else 'blue'
                armor_xyxy = list(map(int, armor_xyxy))
                armor = types.Armor(armor_type, armor_color, armor_xyxy)
                car.add_armor(armor)

            car.calculate_type()
            car.calculate_id()
            self.cars.append(car)

        print(f"Detected {len(self.cars)} cars")

    def plot_cars(self, image):
        for car in self.cars:
            image = car.plot(image)
        return image

    def display(self):
        for car in self.cars:
            print(f"Car ID: {car.id}, Type: {car.type},Armors:{len(car.armors)}")
