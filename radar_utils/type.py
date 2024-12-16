import cv2


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


class Armor:
    def __init__(self,id,color,box):
        self.id = id
        self.color = color
        self.box = box

class Car:
    def __init__(self, box, image):
        self.armors = []
        self.image=image
        self.box = box
        self.id = "-1"
        self.type = "unknown"

    def add_armor(self, armor):
        self.armors.append(armor)

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

    def calculate_id(self):
        if len(self.armors) == 0:
            return False
        ids={}
        for armor in self.armors:
            if armor.id in ids:
                ids[armor.id] += 1
            else:
                ids[armor.id] = 1
        self.id = max(ids, key=ids.get)
        return True


class Map:
    def __init__(self, image_path):
        self.image = cv2.imread(image_path)
        self.shape = self.image.shape
        self.cars = []
