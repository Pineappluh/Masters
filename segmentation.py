import numpy as np
from sklearn.cluster import MeanShift, estimate_bandwidth
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import cv2
from collections import defaultdict


def segment_image(original_img, quantile, blur_strength):
    color_features = 1

    height, width, _ = original_img.shape

    cv2.imshow(f'Original-{quantile}-{blur_strength}', original_img)
    cv2.waitKey(30)

    # create (x, y) features
    X, Y = np.meshgrid(range(width), range(height))
    print(original_img.shape)

    # blur
    # img = cv2.blur(original_img, (0, 0))
    # cv2.imshow(f'Blurred-original-{quantile}-{blur_strength}', img)
    # cv2.waitKey(30)

    img = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)

    # flatten colors
    flat_img = img.reshape(-1, color_features)

    # add (x, y) features
    features = np.concatenate([flat_img, X.reshape(-1, 1), Y.reshape(-1, 1)], axis=1)
    print(features)

    # standardize
    scaler = StandardScaler()
    features = scaler.fit_transform(features)

    # get bandwidth
    bandwidth = estimate_bandwidth(features, quantile=quantile, n_samples=10000)

    # mean shift filter
    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
    ms.fit(features)

    # get model data
    labels = ms.labels_
    cluster_centers = ms.cluster_centers_
    segments = np.unique(labels)
    n_clusters_ = len(segments)
    print(n_clusters_)

    # get cluster centers, unstandardize
    cluster_centers = scaler.inverse_transform(cluster_centers)
    rgb_centers = np.uint8(cluster_centers)[:, :color_features]

    # color all clusters with center color
    res = np.array(list(map(lambda x: rgb_centers[x], labels)))
    result = res.reshape(img.shape)

    # result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    cv2.waitKey(30)

    # show colored clusters
    cmap = plt.cm.get_cmap("hsv", n_clusters_)
    res_colored = np.array(list(map(lambda x: cmap(x, bytes=True)[:3], labels)))
    result = res_colored.reshape(original_img.shape)
    cv2.imshow(f'Clusters-{quantile}-{blur_strength}', result)
    cv2.waitKey(30)

    label_bounding_boxes = sort_bounding_boxes(find_bounding_boxes_by_label(labels, X, Y))

    result = res.reshape(img.shape)
    for label, box in label_bounding_boxes.items():
        min_x, min_y, max_x, max_y = box[0][0], box[0][1], box[1][0], box[1][1]
        color = list(int(x) for x in rgb_centers[label])
        cv2.rectangle(original_img, (min_x, min_y), (max_x, max_y), color, 2)
    cv2.imshow(f'Bounding-boxes-{quantile}-{blur_strength}', original_img)

    return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)


def segment_image_without_blur(original_img, quantile):
    color_features = 3

    height, width, _ = original_img.shape

    cv2.imshow(f'Original-{quantile}', original_img)
    cv2.waitKey(30)

    # create (x, y) features
    X, Y = np.meshgrid(range(width), range(height))
    print(original_img.shape)

    img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)

    # flatten colors
    flat_img = img.reshape(-1, 3)

    # add (x, y) features
    features = np.concatenate([flat_img, X.reshape(-1, 1), Y.reshape(-1, 1)], axis=1)
    print(features)

    # standardize
    # scaler = StandardScaler()
    # features = scaler.fit_transform(features)

    # get bandwidth
    bandwidth = estimate_bandwidth(features, quantile=quantile, n_samples=10000)

    # mean shift filter
    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
    ms.fit(features)

    # get model data
    labels = ms.labels_
    cluster_centers = ms.cluster_centers_
    segments = np.unique(labels)
    n_clusters_ = len(segments)
    print(n_clusters_)

    # get cluster centers, unstandardize
    # cluster_centers = scaler.inverse_transform(cluster_centers)
    rgb_centers = np.uint8(cluster_centers)[:, :color_features]

    # color all clusters with center color
    res = np.array(list(map(lambda x: rgb_centers[x], labels)))
    result = res.reshape(img.shape)
    final_result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    cv2.imshow(f'Result-{quantile}-', final_result)
    cv2.waitKey(30)

    # show colored clusters
    cmap = plt.cm.get_cmap("hsv", n_clusters_)
    res_colored = np.array(list(map(lambda x: cmap(x, bytes=True)[:3], labels)))
    result = res_colored.reshape(img.shape)
    cv2.imshow(f'Clusters-{quantile}-', result)
    cv2.waitKey(30)

    label_bounding_boxes = find_bounding_boxes_by_label(labels, X, Y)

    result = res.reshape(img.shape)
    final_result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    for label, box in label_bounding_boxes.items():
        min_x, min_y, max_x, max_y = box[0][0], box[0][1], box[1][0], box[1][1]
        color = rgb_centers[label]
        cv2.rectangle(final_result, (min_x, min_y), (max_x, max_y), color, 4)

    cv2.imshow(f'Bounding-boxes-{quantile}', final_result)

    return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)


def segment_image_special(original_img, quantile, blur_strength):
    color_features = 3

    height, width, _ = original_img.shape

    cv2.imshow(f'Original-{quantile}-{blur_strength}', original_img)
    cv2.waitKey(30)

    # create (x, y) features
    X, Y = np.meshgrid(range(width), range(height))
    print(original_img.shape)

    # blur
    img = cv2.medianBlur(original_img, blur_strength)

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # flatten colors
    flat_img = img.reshape(-1, 3)

    # get bandwidth
    bandwidth = estimate_bandwidth(flat_img, quantile=quantile, n_samples=1000)

    # mean shift filter
    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
    ms.fit(flat_img)

    cluster_centers = ms.cluster_centers_
    print(len(cluster_centers))
    rgb_centers = np.uint8(cluster_centers)[:, :color_features]

    # color all clusters with center color
    res = np.array(list(map(lambda x: rgb_centers[x], ms.labels_)))
    result = res.reshape(img.shape)
    final_result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    cv2.imshow(f'Result-{quantile}-', final_result)
    cv2.waitKey(30)

    # get model data
    labels = ms.labels_
    features = np.concatenate([labels.reshape(-1, 1), X.reshape(-1, 1), Y.reshape(-1, 1)], axis=1)
    print(labels)
    print(features)

    x_y_by_label = defaultdict(list)

    for label, x, y in features:
        x_y_by_label[label].append((x, y))

    all_boxes = dict()
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    for label, coordinates in x_y_by_label.items():
        print(label, len(coordinates))
        # get bandwidth

        if len(coordinates) < 50:
            continue

        bandwidth = estimate_bandwidth(coordinates, quantile=0.1, n_samples=1000)

        # mean shift filter
        ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
        ms.fit(coordinates)

        # get model data
        labels = ms.labels_
        segments = np.unique(labels)
        print(segments)

        X, Y = zip(*coordinates)

        all_boxes[label] = find_bounding_box(X, Y)

    for xy_label, box in sort_bounding_boxes(all_boxes).items():
        color = list(int(x) for x in rgb_centers[xy_label])[::-1]
        min_x, min_y, max_x, max_y = box[0][0], box[0][1], box[1][0], box[1][1]
        cv2.rectangle(img, (min_x, min_y), (max_x, max_y), color, 2)

    cv2.imshow(f'Bounding-boxes-{quantile}', img)
    cv2.waitKey(0)

def find_bounding_boxes_by_label(labels, X, Y, ravel=True):
    if ravel:
        X = np.ravel(X)
        Y = np.ravel(Y)

    x_coordinates_by_label = defaultdict(list)
    y_coordinates_by_label = defaultdict(list)

    for label, x, y in zip(labels, X, Y):
        x_coordinates_by_label[label].append(x)
        y_coordinates_by_label[label].append(y)

    label_bounding_boxes = dict()

    for label in x_coordinates_by_label.keys():
        label_bounding_boxes[label] = find_bounding_box(x_coordinates_by_label[label], y_coordinates_by_label[label])

    return label_bounding_boxes

def sort_bounding_boxes(labeled_boxes):
    return {k: v for k, v in sorted(labeled_boxes.items(), key=lambda item: box_area(item[1]))}


def find_bounding_box(X, Y):
    return [(min(X), min(Y)), (max(X), max(Y))]

def box_area(box):
    return (box[1][0] - box[0][0]) * (box[1][1] - box[0][1])