import radar
import cv2

img=cv2.imread('interface/1.jpg')
detector=radar.Detector('weights/car.pt','weights/armor.pt','interface/map.png')
detector.detect(img)
detector.display()
img=detector.plot_cars(img)
cv2.imshow('result',img)
cv2.waitKey(0)