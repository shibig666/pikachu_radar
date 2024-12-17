import cv2


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
        self.armors = []    # 内含装甲板
        self.image = image  # ROI图像
        self.box = box  # YOLO识别的机器人框位置
        self.id = "-1"  # 机器人ID
        self.type = "unknown"   # 机器人类型

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
        cv2.putText(image, f"ID:{self.id}", (self.box[0], self.box[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        for armor in self.armors:
            cv2.rectangle(image, (self.box[0]+armor.box[0], self.box[1]+armor.box[1]),
                          (self.box[0]+armor.box[2], self.box[1]+armor.box[3]), color, 2)
        return image


class Map:
    def __init__(self, image_path):
        self.image = cv2.imread(image_path)
        self.shape = self.image.shape
        self.cars = []
