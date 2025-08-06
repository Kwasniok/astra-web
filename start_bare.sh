#!/bin/bash

set -eo pipefail

# python
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements/requirements.txt

# load and export environment
set -a
source bare/.env
set +a

# ensure ASTRA binaries are installed
if [ ! -d "$ASTRA_BINARY_PATH" ]; then
    mkdir -p "$ASTRA_BINARY_PATH"
fi
binary_names=(
    "generator@https://www.desy.de/~mpyflo/Astra_for_64_Bit_Linux/generator"
    "astra@https://www.desy.de/~mpyflo/Astra_for_64_Bit_Linux/Astra"
    "parallel_astra@https://www.desy.de/~mpyflo/Parallel_Astra_for_Linux/Astra"
)
for pair in "${binary_names[@]}"; do
    name="${pair%@*}"
    source="${pair#*@}"
    if [ ! -f "$ASTRA_BINARY_PATH/$name" ]; then
        echo "Downloading $name..."
        wget $source -O $name
        chmod 754 $name
        mv $name "$ASTRA_BINARY_PATH/$name"
    fi
done

# run
uvicorn astra_web.main:app --host 0.0.0.0 --port 8000