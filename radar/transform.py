import cv2
from radar.types import Map
import json
import numpy as np


class Transformer(Map):
    def __init__(self, map_path, config_path, first_image, scale=None):
        super().__init__(map_path)
        self.M = None
        if scale is None:
            self.scale = [0.5, 0.3]  # video,map
        else:
            self.scale = scale
        self.config_path = config_path
        self.config = self.load_config()
        self.init_map(first_image, self.scale)  # 选取点
        self.calculate_M()

    def calculate_M(self):
        src_points = np.float32(self.src_points)
        dst_points = np.float32(self.dst_points)
        self.M = cv2.getPerspectiveTransform(src_points, dst_points)

    def transform_image(self, image):
        """显示变换后的图像"""
        if self.M is None:
            print("Please transform first")
            return
        transformed_image = cv2.warpPerspective(image, self.M, (self.shape[1], self.shape[0]))
        return transformed_image

    def transform(self, car):
        if self.M is None:
            print("Please transform first")
            return
        car_xy = np.array(car.center).reshape(1, 1, 2).astype(np.float32)
        xy_in_map = cv2.perspectiveTransform(car_xy, self.M)
        result = [int(xy_in_map[0][0][0]), int(xy_in_map[0][0][1])]
        for coord in self.config:
            rangex_min, rangex_max = coord["rangex"]
            rangey_min, rangey_max = coord["rangey"]

            if rangex_min <= result[0] < rangex_max and rangey_min <= result[1] < rangey_max:
                result[0] += coord["transformx"]
                result[1] += coord["transformy"]
                break

        car.xy_in_map = result

    def show_plotted_car(self, cars):
        cv2.imshow("Plotted Cars", self.plot_cars(cars))
        cv2.waitKey(0)

    def load_config(self):
        with open(self.config_path, 'r') as f:
            data = json.load(f)
            if data["type"] == "transform":
                return data["data"]
            else:
                raise ValueError("Invalid config file")
