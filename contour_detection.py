import cv2
import numpy as np
from tree_node import TreeNode


def construct_contour_tree(contours, hierarchy):
    root = TreeNode(None)
    node_list = []

    if hierarchy is not None:
        for i, el in enumerate(hierarchy[0]):
            parent = el[3]

            node = TreeNode(contours[i])
            node_list.append(node)

            _, _, w, h = node.bounding_box

            if w < 4 or h < 4:
                continue

            if parent == -1:
                node.parent = root
                root.add_child(node)
            else:
                node.parent = node_list[parent]
                node_list[parent].add_child(node)

        # TODO: add comparison for node objects based on contour
        # removed redundant nodes (replace node with its child), a lot of times there's a double border
        for parent in node_list:
            if len(parent.children) == 1:
                child = parent.children[0]

                x_p, y_p, w_p, h_p = parent.bounding_box
                x_c, y_c, w_c, h_c = child.bounding_box

                if abs(x_p - x_c) < 5 and abs(y_p - y_c) < 5 and abs(w_p - w_c) < 5 and abs(h_p - h_c) < 5:
                    if len(child.children) == 1:
                        grandchild = child.children[0]
                        x_gc, y_gc, w_gc, h_gc = grandchild.bounding_box

                        if abs(x_c - x_gc) < 5 and abs(y_c - y_gc) < 5 and abs(w_c - w_gc) < 5 and abs(h_c - h_gc) < 5:
                            grandparent = parent.parent
                            grandparent.remove_child(parent)
                            grandparent.add_child(grandchild)
                            grandchild.parent = grandparent
                            continue

                    grandparent = parent.parent
                    grandparent.remove_child(parent)
                    grandparent.add_child(child)
                    child.parent = grandparent

    return root, node_list


def color_tree(image, root):
    color = np.random.random(size=3) * 256

    for child in root.children:
        x, y, w, h = child.bounding_box
        cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

        color_tree(image, child)


def find_bounding_boxes_tree(image_name):
    original = cv2.imread(image_name)
    height, width, _ = original.shape
    img_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    # edges_detected = cv2.Canny(img_gray, 100/3, 100)
    # make_edges_white(img_gray)
    laplacian = cv2.Laplacian(img_gray, cv2.CV_16S)
    laplacian = cv2.convertScaleAbs(laplacian)
    _, laplacian = cv2.threshold(laplacian, 15, 255, cv2.THRESH_BINARY)

    contours, hier = cv2.findContours(laplacian, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    root, node_list = construct_contour_tree(contours, hier)

    # uncomment to debug
    color_tree(original, root)
    cv2.imwrite(image_name, original)
    # cv2.waitKey()

    root.bounding_box = 0, 0, width, height

    return root, node_list, height, width


def make_edges_white(img):
    height, width = img.shape
    img[0, :] = 255
    img[height - 1, :] = 255
    img[:, 0] = 255
    img[:, width - 1] = 255


def compare_layout(tree_1, tree_2, comparison_level="Strict", level=0):
    # Strict level doesn't limit how deep comparison goes
    if comparison_level == "Basic" and level >= 1 or comparison_level == "Medium" and level >= 2:
        return [], []

    print("Comparing layout of:\n> {}\n> {}".format(tree_1, tree_2))
    mismatch = []
    match = []
    elements_1 = tree_1.children
    elements_2 = tree_2.children

    if len(elements_1) == len(elements_2):
        print("Element count matches, comparing children...")

        for el_1, el_2 in zip(elements_1, elements_2):
            if el_1.comparison_score(el_2) < 0.85:
                print("Mismatch: {} {} {}".format(el_1.compare(el_2), el_1.get_coordinates(), el_2.get_coordinates()))
                mismatch.append((el_1, el_2))
            else:
                match.append((el_1, el_2))

        for el_1, el_2 in zip(elements_1, elements_2):
            returned_mismatch, returned_match = compare_layout(el_1, el_2, comparison_level, level + 1)
            mismatch += returned_mismatch
            match += returned_match
    else:
        print("Layout doesn't match, finding difference...")

        base = elements_1.copy()
        comparison = elements_2.copy()
        matched = dict()
        while True:
            for el_1 in base.copy():
                best_match = None
                best_score = -1
                for el_2 in comparison.copy():
                    score = el_1.comparison_score(el_2)
                    if score > best_score:
                        best_match = el_2
                        best_score = score

                if best_score < 0.85:
                    base.remove(el_1)
                    mismatch.append((el_1, None))
                    continue

                if best_match not in matched or best_match in matched and matched[best_match][1] > 0:
                    matched[best_match] = (el_1, best_score)

            if not matched:
                break
            else:
                for (el_2, (el_1, _)) in matched.items():
                    base.remove(el_1)
                    comparison.remove(el_2)
                    match.append((el_1, el_2))
                    returned_mismatch, returned_match = compare_layout(el_1, el_2, comparison_level, level + 1)
                    mismatch += returned_mismatch
                    match += returned_match

                matched.clear()

        for el_1 in base:
            mismatch.append((el_1, None))

        for el_2 in comparison:
            mismatch.append((None, el_2))

    return mismatch, match


def calculate_distance(point_1, point_2):
    return ((point_1[0] - point_2[0]) ** 2 + (point_1[1] - point_2[1]) ** 2) ** 0.5
