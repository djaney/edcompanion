import tkinter as tk
from tkinter import ttk, filedialog
from overlays.constants import TITLE
from scripts import edcompanion
from data.config import Config
import json


def open_companion(*args, options=None):
    args = list(args)
    def open_window():
        if options is not None:
            if 'is_overlay' in options and options['is_overlay'].get() == 1:
                args.append('--overlay')
        final_args = []
        for a in args:
            if callable(a):
                final_args.append(a())
            else:
                final_args.append(a)
        edcompanion.main(*final_args)

    return open_window


def select_race(setter):
    def execute():
        conf = Config()
        filename = filedialog.askopenfilename(
            initialdir=conf.dir,
            title="Select file",
            filetypes=(
                ("Race JSON", "*.json"),
            )
        )
        setter(filename)

    return execute


def main():
    root = tk.Tk()
    root.title(TITLE)
    root.geometry("300x300")

    layout_ltr = dict(side='left', expand="yes", fill="x")

    # overlay checkbox
    is_overlay = tk.IntVar(value=1)
    tk.Checkbutton(root, text="Overlay", variable=is_overlay).pack(fill="x")

    def layout_common(parent):
        tk.Button(
            parent, text="Exploration",
            command=open_companion(
                'exploration',
                options={"is_overlay": is_overlay}
            )
        ).pack(fill="x")

    def layout_race(parent):
        race_name_text = tk.StringVar()

        race_name = tk.Label(parent, textvariable=race_name_text)
        race_name.pack()
        race_filename = tk.StringVar()

        def set_race_filename(filename):
            if not filename:
                return None
            race_filename.set(filename)
            with open(race_filename.get(), 'r') as fp:
                try:
                    data = json.load(fp)
                    race_name_text.set(data.get("name", "NO NAME"))
                except json.JSONDecodeError:
                    race_filename.set("")

        tk.Button(
            parent, text="Select",
            command=select_race(set_race_filename)
        ).pack(fill="x")
        tk.Button(
            parent, text="Run",
            command=open_companion(
                'race',
                '--arg1',
                lambda: race_filename.get(),
                options={"is_overlay": is_overlay}
            )
        ).pack(fill="x")

        tk.Button(
            parent, text="Create",
            command=open_companion(
                'create-race',
                options={"is_overlay": is_overlay}
            )
        ).pack(fill="x")

    tab_parent = ttk.Notebook(root)

    tab_common = ttk.Frame(tab_parent)
    tab_parent.add(tab_common, text='Common')
    layout_common(tab_common)

    tab_race = ttk.Frame(tab_parent)
    tab_parent.add(tab_race, text='Race')
    layout_race(tab_race)

    tab_parent.pack(expand="yes", fill="both")

    # main loop
    root.mainloop()


if __name__ == "__main__":
    main()
