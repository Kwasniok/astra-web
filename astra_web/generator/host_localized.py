import os
from subprocess import run
from astra_web.host_localizer import HostLocalizer
from .schemas.io import GeneratorInput
from .schemas.particles import Particles
from .util import _read_particle_file


def write_generator_files(
    generator_input: GeneratorInput, localizer: HostLocalizer
) -> str:
    path = localizer.generator_path(generator_input.gen_id, ".in")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ini_content = generator_input.to_ini()
    with open(path, "w") as input_file:
        input_file.write(ini_content)

    return ini_content


def process_generator_input(
    generator_input: GeneratorInput, localizer: HostLocalizer
) -> None:
    raw_process_output = run(
        [localizer.astra_binary_path("generator"), f"{generator_input.gen_id}.in"],
        cwd=localizer.generator_path(),
        capture_output=True,
    ).stdout
    decoded_process_output = raw_process_output.decode()
    output_file_name = localizer.generator_path(generator_input.gen_id, ".out")
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)
    with open(output_file_name, "w") as file:
        file.write(decoded_process_output)


def read_particle_file(gen_id: str, localizer: HostLocalizer) -> Particles:
    filepath = localizer.generator_path(gen_id, ".ini")

    return _read_particle_file(filepath)


def read_generator_file(gen_id: str, extension: str, localizer: HostLocalizer) -> str:
    filepath = localizer.generator_path(gen_id, extension)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Generator file '{filepath}' not found.")

    with open(filepath, "r") as file:
        return file.read()
