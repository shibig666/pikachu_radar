import radar
import cv2

img = cv2.imread('interface/1.jpg')
detector=radar.Detector('weights/car.pt','weights/armor.pt','interface/map.png')
detector.map.select_src_point(img)
detector.map.select_dst_point()
detector.map.show_map()
# detector.detect(img)
# detector.display()
# img=detector.plot_cars(img)
# cv2.imshow('result',img)
# cv2.waitKey(0)