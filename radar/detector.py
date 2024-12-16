from radar import type
from ultralytics import YOLO
import logging


class Detector:
    def __init__(self, car_path, armor_path, map_path):
        self.armor_classes = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7']
        self.car_detector = YOLO(car_path)
        self.armor_detector = YOLO(armor_path)
        self.cars = []
        self.type_map = type.Map(map_path)
        self.map = self.type_map

    def detect(self, image):
        self.cars = []
        result_cars = self.car_detector(image)
        for cr in result_cars:
            car_box = cr["box"]
            car = type.Car(car_box, image[car_box[1]:car_box[3], car_box[0]:car_box[2]])
            result_armors = self.armor_detector(car.image)
            for ar in result_armors:
                armor_box = ar["box"]
                armor_type = self.armor_classes[ar.Probs.top1]
                armor_color = 'red' if armor_type[0] == 'R' else 'blue'
                armor = type.Armor(armor_type, armor_color, armor_box)
                car.add_armor(armor)
            car.calculate_type()
            car.calculate_id()
            self.cars.append(car)

        logging.info(f"Detected {len(self.cars)} cars")

    def display(self):
        for car in self.cars:
            logging.info(f"Car ID: {car.id}, Type: {car.type}")
