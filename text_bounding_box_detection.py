import cv2
import numpy as np

image = cv2.imread('text-github.png')
original = cv2.imread('text-github.png')
img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
cv2.imshow('gray', img_gray)
edges_detected = cv2.Canny(img_gray, 100/3, 100)

edges_detected = cv2.dilate(edges_detected, None, iterations=7)
edges_detected = cv2.erode(edges_detected, None, iterations=7)

cv2.imshow('canny', edges_detected)
# RETR_LIST for layout, RETR_EXTERNAL for text
contours, hier = cv2.findContours(edges_detected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w * h < 10 or w < 5 or h < 5:
        continue

    color = list(np.random.random(size=3) * 256)
    print(x, y, w, h)
    cv2.rectangle(original, (x, y), (x + w, y + h), color, 2)


cv2.imshow('image', original)
cv2.imwrite('image.png', original)
cv2.waitKey()