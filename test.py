import radar
import cv2

img = cv2.imread('interface/1.jpg')
detector = radar.Detector('weights/car.pt',
                          'weights/armor.pt',
                          'interface/map.png',
                          img)
detector.detect(img)
detector.display()
detector.plot_cars(img)
cv2.imshow("trans", cv2.resize(detector.Transformer.transform_image(img), (0, 0), fx=0.5, fy=0.5))
cv2.imshow("image", cv2.resize(detector.plot_cars(img), (0, 0), fx=0.5, fy=0.5))
cv2.imshow("map", cv2.resize(detector.result_map_image, (0, 0), fx=0.25, fy=0.25))
cv2.waitKey(0)
