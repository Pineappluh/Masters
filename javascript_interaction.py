import os
import json
import subprocess


def set_initial_state(webpage, width, height):
    os.system("node js/record-initial-state.js --webpage='{}' --height='{}' --width='{}'".format(webpage, height, width))


def get_bounding_box_info_batch(batch):
    with open("classification-batch.json", 'w') as outfile:
        json.dump(batch, outfile, default=lambda o: o.encode())
    subprocess.run("node js/element-classificator-batch.js", shell=True, check=True)
    os.remove("classification-batch.json")

    elements_batch = []
    for bounding_boxes_info in batch:
        for config in bounding_boxes_info.configs:
            elements_json = open(config['json'])
            elements = json.load(elements_json)
            os.remove(config['json'])
            elements_batch.append(elements)

    return elements_batch


def generate_screenshot_batch(batch):
    with open("layout-batch.json", 'w') as outfile:
        json.dump(batch, outfile, default=lambda o: o.encode())
    subprocess.run("node js/layout-generator-batch.js", shell=True, check=True)
    os.remove("layout-batch.json")

    links_json = open('links.json')
    links = json.load(links_json)

    return links
