import tkinter as tk
from overlays.constants import TITLE
from scripts import edcompanion


def open_companion(*args, options=None):
    args = list(args)
    if options is not None:
        if 'is_overlay' in options and options['is_overlay'].get() == 1:
            args.append('--overlay')

    def open_window():
        edcompanion.main(*args)

    return open_window


def main():
    root = tk.Tk()
    root.title(TITLE)
    root.geometry("300x50")

    mode_frame = tk.LabelFrame(text="Modes")
    mode_frame.pack(side="top", expand="yes", fill="x")

    layout_ltr = dict(side='left', expand="yes", fill="x")

    # overlay checkbox
    is_overlay = tk.IntVar(value=1)
    tk.Checkbutton(mode_frame, text="Overlay", variable=is_overlay).pack(side='left')

    # exploration button
    tk.Button(
        mode_frame, text="Exploration",
        command=open_companion(
            'exploration',
            options={"is_overlay": is_overlay}
        )
    ).pack(**layout_ltr)

    # exploration button
    tk.Button(
        mode_frame, text="Race",
        command=open_companion('race')
    ).pack(**layout_ltr)

    # main loop
    root.mainloop()


if __name__ == "__main__":
    main()
