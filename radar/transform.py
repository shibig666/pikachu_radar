import json
import cv2
import numpy as np


class Transformer:
    def __init__(self, map_path, config_path, first_image, scale=None):
        self.map_image = cv2.imread(map_path)
        self.shape = self.map_image.shape
        self.src_points = []
        self.dst_points = []
        self.M = None
        if scale is None:
            self.scale = [0.5, 0.3]  # video,map
        else:
            self.scale = scale
        self.config_path = config_path
        self.config = self.load_config()
        self.init_map(first_image, self.scale)  # 选取点
        self.calculate_M()

    def init_map(self, src_image, scale=None):
        if scale is None:
            scale = [0.5, 0.3]  # video,map
        self.select_src_point(src_image, scale[0])
        self.select_dst_point(scale[1])
        cv2.destroyAllWindows()

    def _resize_image(self, image, scale):
        return cv2.resize(image, (0, 0), fx=scale, fy=scale)

    def _mouse_callback(self, event, x, y, flags, param):
        points, scale, image, num = param
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((int(x // scale), int(y // scale)))
            cv2.circle(image, (x, y), 5, (0, 0, 255), -1)
            cv2.putText(image, str(num[0]), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            num[0] += 1

    def _select_points(self, image, points, scale, window_name="Select Points"):
        points.clear()
        num = [1]
        resized_image = self._resize_image(image, scale)
        cv2.imshow(window_name, resized_image)
        param = (points, scale, resized_image, num)
        cv2.setMouseCallback(window_name, self._mouse_callback, param=param)

        while True:
            cv2.imshow(window_name, resized_image)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                if len(points) < 4:
                    print("Please select 4 points")
                    continue
                break

        print(f"Selected points: {points}")
        # cv2.destroyAllWindows()

    def select_src_point(self, src_image, scale=0.5):
        self._select_points(src_image, self.src_points, scale, window_name="Select Source Points")

    def select_dst_point(self, scale=0.5):
        self._select_points(self.map_image, self.dst_points, scale, window_name="Select Destination Points")

    # !>>>>>>>>>>>选取点<<<<<<<<<<!

    def show_map(self, scale=0.5):
        """显示地图"""
        image = self.map_image.copy()
        for dst_point in self.dst_points:
            cv2.circle(image, dst_point, 5, (0, 0, 255), -1)
        cv2.imshow("Map", cv2.resize(image, (0, 0), fx=scale, fy=scale))
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # 在地图中标出机器人
    def plot_cars(self, cars):
        image = self.map_image.copy()
        for car in cars:
            if car.xy_in_map is not None:
                text = f"{car.id}" if car.id != "-1" else ""
                if car.type == "red":
                    color = (0, 0, 255)
                elif car.type == "blue":
                    color = (255, 0, 0)
                else:
                    color = (0, 255, 0)
                cv2.circle(image, car.xy_in_map, 20, color, -1)
                cv2.putText(image, text, car.xy_in_map, cv2.FONT_HERSHEY_SIMPLEX, 5, color, 8)
        return image

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
