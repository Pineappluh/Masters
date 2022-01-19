import cv2
import numpy as np
import matplotlib.pyplot as plt


def simple_edge_detection(image):
    # image = cv2.medianBlur(image, 13)
    edges_detected = cv2.Canny(image, 200/3, 200)
    images = [image, edges_detected]
    location = [121, 122]
    for loc, edge_image in zip(location, images):
        plt.subplot(loc)
        plt.imshow(edge_image, cmap='gray')
    cv2.imwrite('edge_detected.png', edges_detected)
    # plt.savefig('edge_plot.png')
    plt.show()
    return edges_detected


img = cv2.imread('wikipedia-without-text.png')
edges_detected = simple_edge_detection(img)
height, width = edges_detected.shape
print(f"{np.count_nonzero(edges_detected) / (height * width) * 100}%")
