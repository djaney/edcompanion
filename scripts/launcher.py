import tkinter as tk
from overlays.constants import TITLE
from scripts import edcompanion


def open_companion(window, *args, options=None):
    args = list(args)
    if options is not None:
        if 'is_overlay' in options and options['is_overlay'].get() == 1:
            args.append('--overlay')

    def open_window():
        window.destroy()
        edcompanion.main(*args)

    return open_window


def main():
    window = tk.Tk()

    window.title(TITLE)

    is_overlay = tk.IntVar(value=1)

    chk_overlay = tk.Checkbutton(window, text="Overlay", variable=is_overlay)

    options = dict(is_overlay=is_overlay)

    btn_exploration = tk.Button(window, text="Exploration", command=open_companion(window, 'exploration',
                                                                                   options=options))

    chk_overlay.pack()
    btn_exploration.pack()
    window.mainloop()


if __name__ == "__main__":
    main()
