import cv2
from scipy import spatial


class TreeNode:
    weights = [0.75, 0.5, 0.75, 1, 0.25, 0.25]

    def __init__(self, contour, parent=None):
        self.bounding_box = cv2.boundingRect(contour)
        self.parent = parent
        self.children = []
        self.type = "UNKNOWN"
        self.class_name = "UNKNOWN"

    def add_child(self, node):
        self.children.append(node)
        node.index = len(self.children) - 1

    def remove_child(self, node):
        self.children.remove(node)

    def get_relative_center(self):
        x, y, w, h = self.bounding_box
        x_p, y_p, _, _ = self.parent.bounding_box

        x_center = abs(x - x_p) + w / 2
        y_center = abs(y - y_p) + h / 2

        return x_center, y_center

    def get_center(self):
        x, y, w, h = self.bounding_box

        x_center = x + w / 2
        y_center = y + h / 2

        return int(x_center), int(y_center)

    def get_coordinates(self):
        x, y, w, h = self.bounding_box

        return x, y

    def get_relative_coordinates(self):
        x, y, _, _ = self.bounding_box
        if self.parent is not None:
            x_p, y_p, _, _ = self.parent.bounding_box
        else:
            x_p, y_p = 0, 0

        x_rel = abs(x - x_p)
        y_rel = abs(y - y_p)

        return x_rel, y_rel

    def get_area(self):
        _, _, w, h = self.bounding_box
        return w * h

    def get_features(self):
        x_rel, y_rel = self.get_relative_coordinates()
        _, _, width, height = self.bounding_box
        children_count = len(self.children)

        return x_rel, y_rel, width, height, children_count

    def compare(self, other):
        return 1 - spatial.distance.cosine(self.get_features(), other.get_features())

    def comparison_score(self, other):
        x_rel, y_rel, width, height, children_count = self.get_features()
        x_rel_2, y_rel_2, width_2, height_2, children_count_2 = other.get_features()
        vertically_aligned = 1 if abs(x_rel - x_rel_2) < 2 else 0
        y_location_similarity = 1 - abs(y_rel - y_rel_2) / self.parent.bounding_box[3]
        area_similarity = min(self.get_area(), other.get_area()) / max(self.get_area(), other.get_area())
        equal_children = 1 if children_count == children_count_2 else 0
        equal_class_name = 1 if self.class_name == other.class_name and self.class_name != "{}" else 0
        equal_type = 1 if self.type == other.type else 0

        features = [vertically_aligned, y_location_similarity, area_similarity, equal_children, equal_type,
                    equal_class_name]

        return sum([feature * weight for feature, weight in zip(features, self.weights)]) / sum(self.weights)

    def similar(self, other):
        return self.type == other.type and self.compare(other) > 0.9

    def __str__(self):
        x, y, w, h = self.bounding_box
        return "x: {}, y: {}, width: {}, height: {}, type: {}, class: {}, children: {}".format(x, y, w, h, self.type,
                                                                                               self.class_name,
                                                                                               len(self.children))
