import tkinter as tk
from tkinter import ttk, filedialog
from overlays.constants import TITLE
from data.config import Config
import argparse
import os
from pipes import quote


def open_companion(*args, options=None, cmd=None):
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

        command_string = "{} {}".format(cmd, " ".join(quote(a) for a in final_args))
        print(command_string)
        os.system(command_string)

    return open_window


def select_race(is_overlay, cmd=None):
    def execute():
        conf = Config()
        filename = filedialog.askopenfilename(
            initialdir=os.path.join(conf.dir, conf.RACES_DIR),
            title="Select file",
            filetypes=(
                ("Race JSON", "*.json"),
            )
        )
        if filename:
            if is_overlay.get() == 1:
                open_companion(
                    'race',
                    '--arg1',
                    filename,
                    options={"is_overlay": is_overlay},
                    cmd=cmd
                )()
            else:
                open_companion(
                    'race',
                    '--size',
                    '800x900',
                    '--arg1',
                    filename,
                    options={"is_overlay": is_overlay},
                    cmd=cmd
                )()

    return execute


def main():
    parser = argparse.ArgumentParser(description='Launcher')
    parser.add_argument('--cmd', default="edcompanion", type=str)
    args = parser.parse_args()

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
                options={"is_overlay": is_overlay},
                cmd=args.cmd
            )
        ).pack(fill="x")

    def layout_race(parent):
        race_name_text = tk.StringVar()

        race_name = tk.Label(parent, textvariable=race_name_text)
        race_name.pack()

        tk.Button(
            parent, text="Select",
            command=select_race(is_overlay, cmd=args.cmd)
        ).pack(fill="x")

        tk.Button(
            parent, text="Create",
            command=open_companion(
                'create-race',
                options={"is_overlay": is_overlay},
                cmd=args.cmd
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
