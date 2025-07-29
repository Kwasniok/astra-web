import os
from .schemas.particles import Particles


def _read_particle_file(filepath):
    if os.path.exists(filepath):
        return Particles.from_csv(filepath)
    else:
        raise FileNotFoundError(f"Particle file '{filepath}' does not exist.")
