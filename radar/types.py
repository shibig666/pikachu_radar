import cv2
import numpy as np


# 转换为串口发送的类型
def get_armor_type(armor_id):
    Ds = {
        "R1": 1,
        "R2": 2,
        "R3": 3,
        "R4": 4,
        "R5": 5,
        "R7": 7,
        "B1": 101,
        "B2": 102,
        "B3": 103,
        "B4": 104,
        "B5": 105,
        "B7": 107,
    }
    if armor_id in Ds:
        return Ds[armor_id]
    else:
        return 0


# 装甲板类
class Armor:
    def __init__(self, id, color, box):
        self.id = id  # 装甲板ID
        self.color = color  # 装甲板颜色
        self.box = box  # YOLO识别的装甲板框位置


# 机器人类
class Car:
    def __init__(self, box, image):
        self.armors = []  # 内含装甲板
        self.image = image  # ROI图像
        self.box = box  # YOLO识别的机器人框位置
        self.id = "-1"  # 机器人ID
        self.type = "unknown"  # 机器人类型
        self.center = ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)
        self.xy_in_map = None

    # 添加装甲板
    def add_armor(self, armor):
        self.armors.append(armor)

    # 计算机器人类型
    def calculate_type(self):
        if len(self.armors) == 0:
            return False
        red_count = 0
        blue_count = 0
        for armor in self.armors:
            if armor.color == "red":
                red_count += 1
            elif armor.color == "blue":
                blue_count += 1
        self.type = "red" if red_count > blue_count else "blue"
        return True

    # 计算机器人ID
    def calculate_id(self):
        if len(self.armors) == 0:
            return False
        ids = {}
        for armor in self.armors:
            if armor.id in ids:
                ids[armor.id] += 1
            else:
                ids[armor.id] = 1
        self.id = max(ids, key=ids.get)
        return True

    def plot(self, image):
        if self.type == "red":
            color = (0, 0, 255)
        elif self.type == "blue":
            color = (255, 0, 0)
        else:
            color = (0, 255, 0)
        cv2.rectangle(image, (self.box[0], self.box[1]), (self.box[2], self.box[3]), color, 2)
        cv2.putText(image, f"ID:{self.id}", (self.box[0], self.box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv2.circle(image, self.center, 5, color, -1)
        for armor in self.armors:
            cv2.rectangle(image, (self.box[0] + armor.box[0], self.box[1] + armor.box[1]),
                          (self.box[0] + armor.box[2], self.box[1] + armor.box[3]), color, 2)
        return image


class Map:
    def __init__(self, image_path):
        self.image = cv2.imread(image_path)
        self.result_map_image=self.image.copy()
        self.shape = self.image.shape
        self.src_points = []
        self.dst_points = []
        self.M = None

    def init_map(self, src_image):
        self.select_src_point(src_image)
        self.select_dst_point()
        self.transform()

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
        cv2.destroyAllWindows()

    def select_src_point(self, src_image, scale=0.5):
        self._select_points(src_image, self.src_points, scale, window_name="Select Source Points")

    def select_dst_point(self, scale=0.5):
        self._select_points(self.image, self.dst_points, scale, window_name="Select Destination Points")

    def show_map(self):
        """显示地图"""
        image = self.image.copy()
        for dst_point in self.dst_points:
            cv2.circle(image, dst_point, 5, (0, 0, 255), -1)
        cv2.imshow("Map", cv2.resize(image, (0, 0), fx=0.5, fy=0.5))
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def show_transform_image(self, image):
        """显示变换后的图像"""
        if self.M is None:
            print("Please transform first")
            return
        transformed_image = cv2.warpPerspective(image, self.M, (self.shape[1], self.shape[0]))
        cv2.imshow("Transformed Image", cv2.resize(transformed_image, (0, 0), fx=0.5, fy=0.5))
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def transform(self):
        src_points = np.float32(self.src_points)
        dst_points = np.float32(self.dst_points)
        self.M = cv2.getPerspectiveTransform(src_points, dst_points)

    def calculate_car_in_map(self,car):
        if self.M is None:
            print("Please transform first")
            return
        car_xy = np.array(car.center).reshape(1, 1, 2).astype(np.float32)
        xy_in_map = cv2.perspectiveTransform(car_xy, self.M)
        car.xy_in_map = (int(xy_in_map[0][0][0]), int(xy_in_map[0][0][1]))

    def plot_cars(self, cars):
        image = self.image.copy()
        for car in cars:
            if car.xy_in_map is not None:
                text=f"ID:{car.id} {car.type}"
                cv2.circle(image, car.xy_in_map, 10, (0, 255, 0), -1)
                cv2.putText(image, text, car.xy_in_map, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        self.result_map_image=image
        return image


