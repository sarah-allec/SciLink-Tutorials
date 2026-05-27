"""
Generate the synthetic sample data used by Lesson 3.

It writes two files into the data/ folder:

  data/nanoparticles.png  -- a microscopy-style image: bright round particles
                             scattered on a dark background
  data/eds_spectrum.csv   -- an EDS X-ray spectrum (energy in keV vs counts),
                             with peaks at real element line energies

The data files are already included in this package, so you normally do NOT
need to run this. It is here so you can see how the data was made -- and
regenerate it if you want to.

Run it (optional):

    python make_synthetic_data.py
"""

import os

import numpy as np
from PIL import Image

# Write the data into a "data" folder next to this script, wherever it is run.
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")

SEED = 42  # a fixed seed -> the same data every time


def make_particle_image():
    """A 512x512 image with bright round particles on a dark background."""
    rng = np.random.default_rng(SEED)
    size = 512
    n_particles = 27

    # Place particles one at a time. Keep a new particle only if it does not
    # land too close to any particle already placed (so none of them touch).
    centers, radii = [], []
    while len(centers) < n_particles:
        r = rng.uniform(9, 22)
        y = rng.uniform(r + 5, size - r - 5)
        x = rng.uniform(r + 5, size - r - 5)
        too_close = any(
            np.hypot(y - cy, x - cx) < r + cr + 8
            for (cy, cx), cr in zip(centers, radii)
        )
        if not too_close:
            centers.append((y, x))
            radii.append(r)

    # Start with a dark background, then paint each particle as a bright disk.
    rows, cols = np.mgrid[0:size, 0:size]
    image = np.full((size, size), 0.10)
    for (cy, cx), r in zip(centers, radii):
        inside_particle = np.hypot(rows - cy, cols - cx) <= r
        image[inside_particle] = 1.0
    image += rng.normal(0, 0.03, image.shape)   # a little sensor noise
    image = np.clip(image, 0, 1)

    path = os.path.join(DATA_DIR, "nanoparticles.png")
    Image.fromarray((image * 255).astype(np.uint8)).save(path)
    print(f"wrote {path}  ({n_particles} particles)")


def make_eds_spectrum():
    """An EDS spectrum: a smooth background plus a peak for each element."""
    rng = np.random.default_rng(SEED)
    energy = np.round(np.arange(0.10, 12.00, 0.02), 2)   # keV

    # A smooth, decreasing background...
    counts = 800.0 * np.exp(-energy / 2.5) + 20.0
    # ...plus a Gaussian peak at each element's characteristic X-ray energy.
    peaks = [(0.52, 4000), (8.04, 6000), (9.71, 5000)]   # (energy_keV, height)
    for center, height in peaks:
        counts += height * np.exp(-((energy - center) ** 2) / (2 * 0.08 ** 2))
    counts += rng.normal(0, 15, counts.shape)            # measurement noise
    counts = np.clip(counts, 0, None).round(1)

    path = os.path.join(DATA_DIR, "eds_spectrum.csv")
    with open(path, "w") as f:
        f.write("energy_keV,counts\n")
        for e, c in zip(energy, counts):
            f.write(f"{e},{c}\n")
    print(f"wrote {path}  ({len(energy)} data points)")


os.makedirs(DATA_DIR, exist_ok=True)
make_particle_image()
make_eds_spectrum()
print("done.")
