# Postmortem plotting function support

import numpy
import pylab

PLOT_TITLE = "Interlock trigger times\n (X=blue Y=green ADC=red)"


def plot_offsets(ids, x, y, adc, title=PLOT_TITLE, xlabel="Turns"):
    min_t, max_t = -300, +500

    def clip(x):
        return numpy.maximum(min_t, numpy.minimum(max_t, x))

    pylab.plot(clip(x), ids, "b.")
    pylab.plot(clip(y), ids, "g.")
    pylab.plot(clip(adc), ids, "r.")

    a24 = numpy.arange(24) + 1
    for p in a24:
        pylab.axhline(y=float(p), color="grey", ls="--", alpha=0.5)
    pylab.axvline(x=0, color="grey")
    pylab.axis((min_t, max_t, 0.9, 24.9))
    pylab.yticks(a24, [str(i) for i in a24])

    pylab.xlabel("Turns")
    pylab.ylabel("Cell number")
    pylab.title(title)


def plot_positions(
    axis, units, colours, t_x, x, t_s, s, show_mps=False, label_mps=False
):
    x_lines = pylab.plot(t_x, x)
    for line, c in zip(x_lines, colours, strict=True):
        line.set_color(c)
    pylab.plot(t_s, s, "b--")
    pylab.axvline(0, color="g")
    if show_mps:
        pylab.axhline(y=1, color="r", ls="--")
        pylab.axhline(y=-1, color="r", ls="--")
    pylab.axis((t_x[0], t_x[len(t_x) - 1], -5, 5))
    pylab.annotate(
        "Current",
        xy=(t_x[50], 4),
        xytext=(t_x[2], 4.5),
        arrowprops={
            "facecolor": "black",
            "shrinkA": 0,
            "shrinkB": 2,
            "arrowstyle": "->",
        },
    )
    if label_mps:
        pylab.annotate(
            "MPS\nlimit",
            xy=(t_x[50], 1),
            xytext=(t_x[10], 1.4),
            arrowprops={
                "facecolor": "black",
                "shrinkA": 1,
                "shrinkB": 2,
                "arrowstyle": "->",
            },
        )
        pylab.annotate(
            "MPS\nlimit",
            xy=(t_x[50], -1),
            xytext=(t_x[10], -2.5),
            arrowprops={
                "facecolor": "black",
                "shrinkA": 1,
                "shrinkB": 2,
                "arrowstyle": "->",
            },
        )
    pylab.xlabel(f"{units} relative to post mortem event")
    pylab.ylabel(f"{axis} [mm]")


def plot_limits(axis, colour, ids, min, max, pos, ilk):
    pylab.plot(ids, max, color="r")
    pylab.plot(ids, min, color="r")
    pylab.plot(ids, pos, color=colour)
    if ilk.any():
        pylab.plot(
            ids[ilk],
            pos[ilk],
            color="r",
            marker="o",
            markersize=6,
            linestyle="",
            markeredgewidth=0,
        )

    pylab.axis((1, 24.7, -1.5, 1.5))
    pylab.xlabel("Cell number")
    pylab.ylabel(f"{axis} [mm]")
