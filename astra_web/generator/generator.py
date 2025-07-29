import os
from subprocess import run
from astra_web.host_localizer import        HostLocalizer
from .schemas.io import GeneratorInput
from .schemas.particles import Particles


def write_input_file(generator_input: GeneratorInput) -> str:
    ini_content = generator_input.to_ini()
    os.makedirs(os.path.dirname(generator_input.input_filename), exist_ok=True)
    with open(generator_input.input_filename, "w") as input_file:
        input_file.write(ini_content)

    return ini_content


def process_generator_input(generator_input: GeneratorInput, localizer: HostLocalizer) -> str:
    raw_process_output = run([
        _generator_binary(localizer),
        generator_input.input_filename],
        capture_output=True
    ).stdout
    decoded_process_output = raw_process_output.decode()
    output_file_name = localizer.generator_path(generator_input.gen_id, ".out")
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)
    with open(output_file_name, "w") as file:
        file.write(decoded_process_output)

    return decoded_process_output


def _generator_binary(localizer: HostLocalizer) -> str:
    return localizer.astra_binary_path("generator")


def read_particle_file(filepath):
    if os.path.exists(filepath):
        return Particles.from_csv(filepath)
    else:
        raise FileNotFoundError(f"Particle file '{filepath}' does not exist.")


def read_output_file(generator_input: GeneratorInput, localizer: HostLocalizer) -> Particles:
    filepath = localizer.generator_path(generator_input.gen_id, ".ini")

    return read_particle_file(filepath)

