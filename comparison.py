import cv2
import numpy as np

img_1 = cv2.imread('wikipedia-without-text.png')
img_2 = cv2.imread('wikipedia-without-text-2.png')

rows_1, cols, _ = img_1.shape
rows_2, _, _ = img_2.shape

if rows_1 >= rows_2:
    result = img_1.copy()
    rows = rows_2
else:
    result = img_2.copy()
    rows = rows_1


for i in range(rows):
    for j in range(cols):
        pixel_1 = img_1[i][j]
        pixel_2 = img_2[i][j]

        if not np.array_equal(pixel_1, pixel_2):
            result[i][j] = [203, 192, 255]

cv2.imshow('comparison', result)
cv2.waitKey(0)