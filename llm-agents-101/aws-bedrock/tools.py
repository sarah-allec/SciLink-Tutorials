"""
Real (but simple) microscopy analysis tools for Lesson 3.

Each tool genuinely opens a file from the data/ folder and computes its
result -- there are no fake numbers here. The analysis is kept deliberately
simple so the code stays easy to read.

For each tool the agent needs three things:
  * a Python function that does the work     -> the functions below
  * a name + description + input schema      -> TOOL_SCHEMAS
  * a lookup from tool name to function      -> TOOL_FUNCTIONS

The DESCRIPTION text is the ONLY thing the model reads to decide which tool
to use -- so writing clear descriptions is the real work here.
"""

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.signal import find_peaks


# --------------------------------------------------------------------------
# 1. The tool implementations.
# --------------------------------------------------------------------------

def _find_particles(image_path):
    """Shared helper: load an image and label each bright blob.

    Returns the label array and the number of particles found.
    """
    image = np.array(Image.open(image_path).convert("L"), dtype=float) / 255.0
    bright = image > 0.5                          # particles are bright, background dark
    labels, n_particles = ndimage.label(bright)   # group touching bright pixels
    return labels, n_particles


def count_particles(image_path: str) -> dict:
    """Count how many particles are in a microscopy image."""
    _, n_particles = _find_particles(image_path)
    return {"image": image_path, "particle_count": int(n_particles)}


def measure_particle_sizes(image_path: str) -> dict:
    """Measure the average particle diameter (in pixels) in an image."""
    labels, n_particles = _find_particles(image_path)
    diameters = []
    for particle_id in range(1, n_particles + 1):
        area_px = int(np.sum(labels == particle_id))
        # diameter of a circle that has the same area as the particle
        diameters.append(2.0 * np.sqrt(area_px / np.pi))
    diameters = np.array(diameters)
    return {
        "image": image_path,
        "particle_count": int(n_particles),
        "mean_diameter_px": round(float(diameters.mean()), 1),
        "std_diameter_px": round(float(diameters.std()), 1),
    }


# Characteristic X-ray line energies (keV) for a handful of elements.
ELEMENT_LINES = {
    "C": 0.28, "O": 0.52, "Al": 1.49, "Si": 1.74,
    "Ti": 4.51, "Fe": 6.40, "Cu": 8.04, "Au": 9.71,
}


def identify_elements(spectrum_path: str) -> dict:
    """Identify which elements are present in an EDS spectrum."""
    data = np.loadtxt(spectrum_path, delimiter=",", skiprows=1)
    energy, counts = data[:, 0], data[:, 1]

    # Find the peaks: points that stand well above their surroundings.
    peak_indices, _ = find_peaks(counts, height=counts.max() * 0.15, distance=20)

    # Match each peak's energy to the nearest known element line.
    elements = []
    for peak_energy in energy[peak_indices]:
        for symbol, line_energy in ELEMENT_LINES.items():
            if abs(peak_energy - line_energy) < 0.15:
                elements.append(symbol)
    return {"spectrum": spectrum_path, "elements_detected": sorted(set(elements))}


# --------------------------------------------------------------------------
# 2. Name -> function lookup. The agent loop uses this to run a chosen tool.
# --------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "count_particles": count_particles,
    "measure_particle_sizes": measure_particle_sizes,
    "identify_elements": identify_elements,
}


# --------------------------------------------------------------------------
# 3. The tool schemas. Each one has three fields: a name, a description,
#    and an input_schema (JSON Schema for the arguments). The model picks
#    a tool from the DESCRIPTION text alone, so each one says clearly when
#    to use it.
# --------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "count_particles",
        "description": (
            "Count how many discrete particles are in a microscopy image. "
            "Use this for 'how many particles' questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the microscopy image file.",
                }
            },
            "required": ["image_path"],
        },
    },
    {
        "name": "measure_particle_sizes",
        "description": (
            "Measure the average size (diameter) of the particles in a "
            "microscopy image. Use this for questions about how big the "
            "particles are or their size."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the microscopy image file.",
                }
            },
            "required": ["image_path"],
        },
    },
    {
        "name": "identify_elements",
        "description": (
            "Identify which chemical elements are present from an EDS "
            "(energy-dispersive X-ray) spectrum. Use this for questions "
            "about elemental composition or which elements a sample contains."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "spectrum_path": {
                    "type": "string",
                    "description": "Path to the EDS spectrum CSV file.",
                }
            },
            "required": ["spectrum_path"],
        },
    },
]
