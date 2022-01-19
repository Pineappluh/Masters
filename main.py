from testing import *
from os.path import exists
from gui import project_reopen
import shutil

if not exists("config.json"):
    print("No project detected. Setting up...")
    config = create_config()

    create_baseline(config['URL'], config['startingPath'], config)
else:
    print("Project detected. Loading config.")
    config = read_config()

    command = project_reopen(config)

    if command == "Run regression":
        crawled = dict(json.load(open("crawled.json")))
        regression(crawled, config)
    elif command == "Recreate baseline":
        shutil.rmtree(config['domain'])  # delete folder with data
        create_baseline(config['URL'], config['startingPath'], config)
    elif command == "Delete project":
        shutil.rmtree(config['domain'])  # delete folder with data
        os.remove("config.json")
        os.remove("crawled.json")
