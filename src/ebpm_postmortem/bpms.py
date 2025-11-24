# BPM definitions

# List of all BPMs in the storage ring.  This is slightly tricky as we alternate
# straights and arcs, but we only have a limited number of straights.  This list
# needs to match the corresponding list in CS-DI-IOC-01/monitor.py
STRAIGHTS = [9, 10, 13]


def flatten(ll):
    """Flattens a list of lists into a single list."""
    return [x for sublist in ll for x in sublist]


def cell_size(c):
    if c == 2:
        return 8
    else:
        return 7


def make_bpms(straight, cell):
    return flatten(
        [
            [straight(c + 1, n + 1) for n in range(2) if c + 1 in STRAIGHTS]
            + [cell(c + 1, n + 1) for n in range(cell_size(c + 1))]
            for c in range(24)
        ]
    )


BPMS = make_bpms(
    lambda c, n: f"SR{c:02d}S-DI-EBPM-{n:02d}",
    lambda c, n: f"SR{c:02d}C-DI-EBPM-{n:02d}",
)

BPM_ids = make_bpms(lambda c, n: c - 0.2 + 0.1 * n, lambda c, n: c + 0.1 * n)

BPM_colours = make_bpms(lambda c, n: "k", lambda c, n: "bgrcmykb"[n - 1])

BPM_count = len(BPMS)


# Converts a BPM specific PV into one PV per BPM.
def bpm_pvs(name):
    return [f"{bpm}:{name}" for bpm in BPMS]
