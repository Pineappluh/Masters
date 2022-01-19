import pickle
from javascript_interaction import *
from contour_detection import *
import re
from urllib.parse import urlparse
from gui import get_base_config, prompt_change_baseline, prompt_add_to_baseline, prompt_record_initial_state
from PIL import Image


def create_config():
    new_config = get_base_config()
    parsed_url = urlparse(new_config['URL'])
    new_config['domain'] = parsed_url.netloc
    new_config['startingPath'] = parsed_url.path
    # convert http://example.com to http://example.com/
    TreeNode.weights = new_config['comparisonWeights']

    if prompt_record_initial_state():
        print("Opening URL and recording initial state...")
        set_initial_state(new_config['URL'], 1920, 1080)

    with open("config.json", 'w') as outfile:
        json.dump(new_config, outfile, indent=4)

    return new_config


def read_config():
    stored_json_config = open("config.json")
    stored_config = json.load(stored_json_config)
    TreeNode.weights = stored_config['comparisonWeights']
    return stored_config


class Page:
    def __init__(self, url, domain, path, resolutions, browsers, depth):
        self.url = url
        self.path = path
        self.domain = domain
        self.depth = depth
        self.configs = dict()

        for browser in browsers:
            self.configs[browser] = []

            for resolution in resolutions:
                self.configs[browser].append(PageConfig(domain, path, resolution, browser))


class PageConfig:
    def __init__(self, domain, path, resolution, browser):
        self.resolution = resolution
        self.path = path
        resolution_data = resolution.split("x")
        self.width = int(resolution_data[0])
        self.height = int(resolution_data[1])
        self.browser = browser
        self.data_storage_path = "{}/{}/{}{}".format(domain, browser, resolution,  path + ("" if path == "/" else "/"))
        self.baseline_image_path = "{}screenshot.png".format(self.data_storage_path)
        self.baseline_image_layout_path = "{}layout.png".format(self.data_storage_path)
        self.comparison_image_path = "{}screenshot-comparison.png".format(self.data_storage_path)
        self.comparison_image_layout_path = "{}layout-comparison.png".format(self.data_storage_path)
        self.pickled_tree_path = "{}tree.p".format(self.data_storage_path)
        self.temporary_data_path = "{}data.json".format(self.data_storage_path)


class ScreenshotInfo:
    def __init__(self, url, page_configs, browser, depth, baseline=True):
        self.webpage = url
        self.browser = browser
        self.depth = depth
        self.configs = []

        for page_config in page_configs:
            config = dict()

            config['width'] = page_config.width
            config['height'] = page_config.height
            if baseline:
                config['name'] = page_config.baseline_image_path
                config['layout'] = page_config.baseline_image_layout_path
            else:
                config['name'] = page_config.comparison_image_path
                config['layout'] = page_config.comparison_image_layout_path

            self.configs.append(config)

    def encode(self):
        return self.__dict__


class BoundingBoxesInfo:
    def __init__(self, url, page_configs, browser, inputs, max_heights):
        self.webpage = url
        self.browser = browser
        self.configs = []

        for page_config, input, page_max_height in zip(page_configs, inputs, max_heights):
            config = dict()

            config['width'] = page_config.width
            config['height'] = page_max_height
            config['json'] = page_config.temporary_data_path
            config['input'] = input

            self.configs.append(config)

    def encode(self):
        return self.__dict__


def create_layout_tree(page_batch, baseline=True):
    bounding_boxes_info_batch = []
    bounding_boxes_trees, bounding_boxes_lists = [], []
    all_page_configs = []
    for page in page_batch:
        for browser, page_configs in page.configs.items():
            inputs = []
            max_heights = []

            for page_config in page_configs:
                print(
                    "Extracting element borders for '{}' at {} in {}...".format(page_config.path, page_config.resolution,
                                                                              page_config.browser))
                if baseline:
                    bounding_boxes_tree, bounding_boxes_list, page_height, page_width = find_bounding_boxes_tree(
                        page_config.baseline_image_layout_path)
                else:
                    bounding_boxes_tree, bounding_boxes_list, page_height, page_width = find_bounding_boxes_tree(
                        page_config.comparison_image_layout_path)
                bounding_boxes_trees.append(bounding_boxes_tree)
                bounding_boxes_lists.append(bounding_boxes_list)
                max_heights.append(page_height)

                formatted_coordinates = []
                for box in bounding_boxes_list:
                    (x, y, w, h) = box.bounding_box
                    formatted_coordinates.append({"x": x, "y": y, "width": w, "height": h})
                inputs.append(formatted_coordinates)

            bounding_boxes_info_batch.append(BoundingBoxesInfo(page.url, page_configs, browser, inputs, max_heights))
            all_page_configs += page_configs

    print("Extracting info from HTML in batch...")
    elements_batch = get_bounding_box_info_batch(bounding_boxes_info_batch)

    for bounding_boxes_tree, bounding_boxes_list, elements, page_config in zip(bounding_boxes_trees,
                                                                               bounding_boxes_lists, elements_batch,
                                                                               all_page_configs):
        for node, element in zip(bounding_boxes_list, elements):
            node.type = element['type']
            node.class_name = element['className']

        if baseline:
            pickle.dump(bounding_boxes_tree, open(page_config.pickled_tree_path, "wb"))

    return bounding_boxes_trees, all_page_configs


def filter_batch(unfiltered_batch, found, visited_paths, config):
    filtered_batch = []
    limits = config['limits']
    exclusions = config['exclusions']

    for path, (link, depth) in unfiltered_batch.items():
        if 'maxCrawlDepth' in config and depth >= config['maxCrawlDepth']:
            continue

        if path not in visited_paths:
            exclusion_match = next((exclusion for exclusion in exclusions if re.match(exclusion, path)), None)
            if exclusion_match:
                print("'{}' is excluded by {}".format(path, exclusion_match))
                continue

            limit_match = next((limit for limit in limits if re.match(limit, path)), None)
            if limit_match:
                print("Matched '{}' with {}".format(path, str(limit_match)))
                if found[limit_match] >= config['limitAmount']:
                    print("Limit already matched!")
                    continue
                found[limit_match] += 1

            if path.endswith("/"):
                path = path[:-1]

            filtered_batch.append(Page(link, config['domain'], path, config['resolutions'], config['browsers'], depth))

    return filtered_batch


def add_new_pages(new_pages, visited_paths):
    screenshot_info_batch = []
    for page in new_pages:
        print("Visiting {} for path '{}'".format(page.url, page.path))
        visited_paths[page.path] = (page.url, page.depth)

        for browser, page_configs in page.configs.items():
            screenshot_info_batch.append(ScreenshotInfo(page.url, page_configs, browser, page.depth, baseline=True))

    print("Generating screenshots in batch...")
    next_batch_unfiltered = generate_screenshot_batch(screenshot_info_batch)

    create_layout_tree(new_pages)

    return next_batch_unfiltered


def batch_crawl(start_batch, config, baseline_exists):
    if not baseline_exists:
        visited_paths = dict()
        found = dict()
        for limit in config['limits']:
            found[limit] = 0
    else:
        found = pickle.load(open("found.p", "rb"))
        visited_paths = dict(json.load(open("crawled.json")))

    current_batch = start_batch
    while current_batch:
        current_batch_filtered = filter_batch(current_batch, found, visited_paths, config)

        if baseline_exists:
            for new_page in current_batch_filtered.copy():
                print(new_page.__dict__)
                if not prompt_add_to_baseline(new_page.url):
                    current_batch_filtered.remove(new_page)
                    config['exclusions'].append(new_page.path)

        if current_batch:
            current_batch = add_new_pages(current_batch_filtered, visited_paths)

    pickle.dump(found, open("found.p", "wb"))
    with open("crawled.json", 'w') as outfile:
        json.dump(visited_paths, outfile, indent=4)
    with open("config.json", 'w') as outfile:
        json.dump(config, outfile, indent=4)


def check_baseline_difference(bounding_boxes_tree, page_config, config):
    baseline_tree = pickle.load(open(page_config.pickled_tree_path, "rb"))

    print("Comparing baseline and current state for {} at {} in {}".format(page_config.path, page_config.resolution,
                                                                           page_config.browser))
    mismatch, match = compare_layout(baseline_tree, bounding_boxes_tree, config['comparisonLevel'])

    print("Found {} total differences".format(len(mismatch)))

    image_1 = cv2.imread(page_config.baseline_image_path)
    image_2 = cv2.imread(page_config.comparison_image_path)

    if len(mismatch) > 0:
        visualize_image_differences_for_mismatch(mismatch, image_1, image_2)

        compatible_image_1 = Image.fromarray(cv2.cvtColor(image_1, cv2.COLOR_BGR2RGB))
        compatible_image_2 = Image.fromarray(cv2.cvtColor(image_2, cv2.COLOR_BGR2RGB))
        wants_baseline_change = prompt_change_baseline(compatible_image_1, compatible_image_2, len(mismatch),
                                                       page_config)

        if wants_baseline_change:
            os.remove(page_config.baseline_image_path)
            os.remove(page_config.baseline_image_layout_path)
            os.remove(page_config.pickled_tree_path)

            os.rename(page_config.comparison_image_path, page_config.baseline_image_path)
            os.rename(page_config.comparison_image_layout_path, page_config.baseline_image_layout_path)
            pickle.dump(bounding_boxes_tree, open(page_config.pickled_tree_path, "wb"))
            return

    os.remove(page_config.comparison_image_path)
    os.remove(page_config.comparison_image_layout_path)


def visualize_image_differences_for_mismatch(mismatch, image_1, image_2):
    for el_1, el_2 in mismatch:
        if el_1 is None:
            color = list(np.random.random(size=3) * 256)
            (x_2, y_2, w_2, h_2) = el_2.bounding_box
            cv2.rectangle(image_2, (x_2, y_2), (x_2 + w_2, y_2 + h_2), color, 5)
        elif el_2 is None:
            color = list(np.random.random(size=3) * 256)
            (x_1, y_1, w_1, h_1) = el_1.bounding_box
            cv2.rectangle(image_1, (x_1, y_1), (x_1 + w_1, y_1 + h_1), color, 5)
        else:
            (x_1, y_1, w_1, h_1), (x_2, y_2, w_2, h_2) = el_1.bounding_box, el_2.bounding_box
            color = list(np.random.random(size=3) * 256)
            cv2.rectangle(image_1, (x_1, y_1), (x_1 + w_1, y_1 + h_1), color, 5)
            cv2.rectangle(image_2, (x_2, y_2), (x_2 + w_2, y_2 + h_2), color, 5)


def create_baseline(start_url, start_path, config):
    start_batch = {start_path: (start_url, 0)}

    batch_crawl(start_batch, config, baseline_exists=False)


def regression(crawled, config):
    batch = []
    screenshot_info_batch = []
    for path, (url, depth) in crawled.items():
        page = Page(url, config['domain'], path, config['resolutions'], config['browsers'], depth)
        batch.append(page)
        for browser, page_configs in page.configs.items():
            screenshot_info_batch.append(ScreenshotInfo(page.url, page_configs, browser, depth, baseline=False))

    # Checking if new URLs exist in application
    print("Generating comparison screenshots in batch...")
    all_available_links = generate_screenshot_batch(screenshot_info_batch)
    batch_crawl(all_available_links, config, baseline_exists=True)

    bounding_boxes_trees, page_configs = create_layout_tree(batch, baseline=False)

    for bounding_boxes_tree, page_config in zip(bounding_boxes_trees, page_configs):
        check_baseline_difference(bounding_boxes_tree, page_config, config)
