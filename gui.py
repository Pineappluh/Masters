import tkinter as tk
from PIL import ImageTk
from PIL import ImageOps


class EntryWithPlaceholder(tk.Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey'):
        super().__init__(master, width=50)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()

    def value_entered(self):
        return self.get() != self.placeholder


def save_and_quit(root, config, entries, weight_entries, resolution_selections, browser_selections):
    config['URL'] = entries['URL'].get()

    if entries['limits'].value_entered():
        config['limits'] = entries['limits'].get().split(", ")
    else:
        config['limits'] = []

    if entries['limitAmount'].value_entered():
        config['limitAmount'] = int(entries['limitAmount'].get())
    else:
        config['limitAmount'] = 1

    if entries['exclusions'].value_entered():
        config['exclusions'] = entries['exclusions'].get().split(", ")
    else:
        config['exclusions'] = []

    if entries['maxCrawlDepth'].value_entered():
        config['maxCrawlDepth'] = int(entries['maxCrawlDepth'].get())

    config['comparisonLevel'] = entries['comparisonLevel'].get()

    config['comparisonWeights'] = [float(entry.get()) for entry in weight_entries]

    selected_resolutions = []
    for resolution, selection in resolution_selections.items():
        if selection.get():
            selected_resolutions.append(resolution)
    config['resolutions'] = selected_resolutions

    selected_browsers = []
    for browser, selection in browser_selections.items():
        if selection.get():
            selected_browsers.append(browser.lower())
    config['browsers'] = selected_browsers

    root.quit()
    root.destroy()


def get_base_config():
    config = {}

    root = tk.Tk()

    entries, weight_entries, resolution_selections, browser_selections = make_form(root)
    quit_button = tk.Button(root, text='Start crawl',
                            command=lambda: save_and_quit(root, config, entries, weight_entries, resolution_selections,
                                                          browser_selections))
    quit_button.pack(side=tk.LEFT, padx=5, pady=5)

    root.mainloop()

    return config


def make_form(root):
    fields = ["URL", "limits", "limitAmount", "exclusions", "maxCrawlDepth"]
    fields_text = ["URL of website", "Dynamic paths to view X times (optional)",
                   "X - limit amount (optional, defaults to 1)", "Paths to exclude (optional)",
                   "Maximum depth of crawling (optional)"]
    placeholders = ["https://www.example.com", "/user/*, /profile/*, ...", "1", "/user/*, /terms, ...", "5"]
    entries = {}
    for field, field_text, placeholder in zip(fields, fields_text, placeholders):
        row = tk.Frame(root)
        lab = tk.Label(row, width=35, text=field_text + ": ", anchor='e')
        ent = EntryWithPlaceholder(row, placeholder)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X, padx=(0, 15))
        entries[field] = ent

    level_options = ["Basic", "Medium", "Strict"]
    variable = tk.StringVar()
    variable.set(level_options[2])
    row = tk.Frame(root)
    lab = tk.Label(row, width=35, text="Level of comparison: ", anchor='e')
    ent = tk.OptionMenu(row, variable, *level_options)
    row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
    lab.pack(side=tk.LEFT)
    ent.pack(side=tk.LEFT, padx=(0, 15))
    entries['comparisonLevel'] = variable

    row = tk.Frame(root)
    lab = tk.Label(row, text="Which resolutions do you want to test?")
    lab.pack(side=tk.LEFT)
    row.pack(side=tk.TOP, pady=(15, 3))
    desktop_resolutions = [("1920x1080", 1), ("1366x768", 0), ("1440x900", 0), ("1536x864", 0), ("1280x720", 0)]
    phone_tablet_resolutions = [("360x640", 1), ("414x896", 0), ("360x800", 0), ("768x1024", 0), ("1280x800", 0)]
    resolution_selections = dict()
    for name, resolutions in zip(["Desktop", "Phone and tablet"], [desktop_resolutions, phone_tablet_resolutions]):
        row = tk.Frame(root)
        lab = tk.Label(row, text=name + ": ", width=20, anchor='e')
        lab.pack(side=tk.LEFT)
        for resolution, value in resolutions:
            selection = tk.IntVar(value=value)
            resolution_selections[resolution] = selection
            chk = tk.Checkbutton(row, text=resolution, variable=selection, width=10)
            chk.pack(side=tk.LEFT)
        row.pack(side=tk.TOP)

    row = tk.Frame(root)
    lab = tk.Label(row, text="Which browsers do you want to test?")
    lab.pack(side=tk.LEFT)
    row.pack(side=tk.TOP, pady=(15, 3))
    row = tk.Frame(root)
    browsers = [("Chromium", 1), ("Firefox", 0), ("Webkit", 0)]
    browser_selections = dict()
    for browser, value in browsers:
        selection = tk.IntVar(value=value)
        browser_selections[browser] = selection
        chk = tk.Checkbutton(row, text=browser, variable=selection)
        chk.pack(side=tk.LEFT)
    row.pack(side=tk.TOP)

    fields = ["Vertical alignment", "Y distance", "Area similarity", "Hierarchy", "HTML tag match", "HTML class match"]
    default_values = [0.75, 0.5, 0.75, 1, 0.25, 0.25]
    weight_entries = []
    row = tk.Frame(root)
    lab = tk.Label(row, text="You can edit the weights on which element comparison is based:")
    lab.pack(side=tk.LEFT)
    row.pack(side=tk.TOP, pady=(15, 3))
    row = None
    for i, (field, value) in enumerate(zip(fields, default_values)):
        if i % 3 == 0:
            row = tk.Frame(root)

        lab = tk.Label(row, text=field + ": ", width=20, anchor='e')
        ent = tk.Entry(row, width=5)
        ent.insert(0, str(value))
        weight_entries.append(ent)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.LEFT)

        if (i + 1) % 3 == 0:
            row.pack(side=tk.TOP, pady=3)

    return entries, weight_entries, resolution_selections, browser_selections


def save_choice_and_quit(root, result, accepted):
    result['accept'] = accepted
    root.quit()
    root.destroy()


def prompt_change_baseline(baseline_image, comparison_image, difference_count, page_config):
    result = {'accept': None}

    root = tk.Tk()

    image_row = tk.Frame(root)
    baseline = tk.Label(image_row, compound='top')
    baseline.lenna_image_png = ImageTk.PhotoImage(image=ImageOps.contain(baseline_image, (800, 800)))
    baseline['image'] = baseline.lenna_image_png
    baseline.pack(side=tk.LEFT, padx=5, pady=5)
    comparison = tk.Label(image_row, compound='top')
    comparison.lenna_image_png = ImageTk.PhotoImage(image=ImageOps.contain(comparison_image, (800, 800)))
    comparison['image'] = comparison.lenna_image_png
    comparison.pack(side=tk.LEFT, padx=5, pady=5)
    image_row.pack(side=tk.TOP)

    label = tk.Label(root, text="Page: {} | Browser: {} | Resolution: {}".format(page_config.path, page_config.browser,
                                                                                 page_config.resolution))
    label.pack(side=tk.TOP, pady=2)
    label = tk.Label(root, text="Detected {} difference(s) with baseline. What would you like to do?".format(
        difference_count))
    label.pack(side=tk.TOP, pady=5)

    button_row = tk.Frame(root)
    change_button = tk.Button(button_row, text="Change baseline",
                              command=lambda: save_choice_and_quit(root, result, True))
    change_button.pack(side=tk.LEFT, padx=10)
    no_change_button = tk.Button(button_row, text="Keep current baseline",
                                 command=lambda: save_choice_and_quit(root, result, False))
    no_change_button.pack(side=tk.LEFT, padx=10)
    button_row.pack(side=tk.TOP, pady=5)

    root.mainloop()

    return result['accept']


def save_command_and_quit(root, result, command):
    result['command'] = command
    root.quit()
    root.destroy()


def project_reopen(config):
    result = {'command': None}

    root = tk.Tk()

    row = tk.Frame(root)
    lab = tk.Label(row, text="What would you like to do for {}?".format(config['URL']))
    lab.pack(side=tk.LEFT)
    row.pack(side=tk.TOP, pady=(15, 3), padx=15)

    button_row = tk.Frame(root)
    run_test_button = tk.Button(button_row, text="Run regression test",
                                command=lambda: save_command_and_quit(root, result, "Run regression"))
    run_test_button.pack(side=tk.LEFT, padx=10)
    rerun_crawl_button = tk.Button(button_row, text="Recreate baseline",
                                   command=lambda: save_command_and_quit(root, result, "Recreate baseline"))
    rerun_crawl_button.pack(side=tk.LEFT, padx=10)
    rerun_crawl_button = tk.Button(button_row, text="Delete project",
                                   command=lambda: save_command_and_quit(root, result, "Delete project"))
    rerun_crawl_button.pack(side=tk.LEFT, padx=10)
    button_row.pack(side=tk.TOP, pady=5)

    root.mainloop()

    return result['command']


def prompt_add_to_baseline(new_path):
    result = {'accept': None}

    root = tk.Tk()

    label = tk.Label(root,
                     text="A new page has been detected in your application.\n"
                          "Would you like to add {} to the baseline?".format(new_path))
    label.pack(side=tk.TOP, pady=5, padx=10)

    button_row = tk.Frame(root)
    yes_button = tk.Button(button_row, text="Yes", command=lambda: save_choice_and_quit(root, result, True))
    yes_button.pack(side=tk.LEFT, padx=10)
    no_button = tk.Button(button_row, text="No", command=lambda: save_choice_and_quit(root, result, False))
    no_button.pack(side=tk.LEFT, padx=10)
    button_row.pack(side=tk.TOP, pady=5)

    root.mainloop()

    return result['accept']


def prompt_record_initial_state():
    result = {'accept': None}

    root = tk.Tk()

    label = tk.Label(root, text="Would you like to record an initial state for the web application?\n"
                                "For example: close the 'Accept cookies' popup or "
                                "log in (will only work if authentication is based on stored cookies)")
    label.pack(side=tk.TOP, pady=5, padx=10)

    button_row = tk.Frame(root)
    yes_button = tk.Button(button_row, text="Yes", command=lambda: save_choice_and_quit(root, result, True))
    yes_button.pack(side=tk.LEFT, padx=10)
    no_button = tk.Button(button_row, text="No", command=lambda: save_choice_and_quit(root, result, False))
    no_button.pack(side=tk.LEFT, padx=10)
    button_row.pack(side=tk.TOP, pady=5)

    root.mainloop()

    return result['accept']
