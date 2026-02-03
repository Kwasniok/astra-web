#!/usr/bin/env bash

set -eo pipefail

# environment
ENV_FILE="config/.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "Warning: `$ENV_FILE` not found, skipping .env file import."
fi
: "${ASTRA_BINARY_CHECK_HASH:=false}"
: "${ASTRA_WEB_PORT:=8000}"

# setup python
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements/requirements.txt


# ensure ASTRA binaries are installed
if [ ! -d "$ASTRA_BINARY_PATH" ]; then
    mkdir -p "$ASTRA_BINARY_PATH"
fi
# name, source, checksum for v4.0 (2025.09.19)
binaries=(
    "generator@https://www.desy.de/~mpyflo/Astra_for_64_Bit_Linux/generator@cb21b391e1122803aee7eebecfabe495"
    "astra@https://www.desy.de/~mpyflo/Astra_for_64_Bit_Linux/Astra@82417dc3faf6fddbb3f01d7292b0491e"
    "parallel_astra@https://www.desy.de/~mpyflo/Parallel_Astra_for_Linux/Astra@c12881078456070c3a52f2a0f0a01ce9"
)
for binary in "${binaries[@]}"; do
    IFS="@" read -r name source hash <<< "$binary"

    # download (if absent)
    if [ ! -f "$ASTRA_BINARY_PATH/$name" ]; then
        echo "Downloading $name ..."
        wget -q "$source" -O "$name"
        chmod 754 "$name"
        mv "$name" "$ASTRA_BINARY_PATH/$name"
    fi

    # check hash
    if [ "$ASTRA_BINARY_CHECK_HASH" == true ]; then
        computed_hash=$(md5sum "$ASTRA_BINARY_PATH/$name" | awk '{print $1}')
        if [ "$computed_hash" != "$hash" ]; then
            echo "ERROR: checksum mismatch for binary $name!"
            echo "Expected HASH: $hash"
            echo "Got HASH:      $computed_hash"
            echo "Corrupted file or unexpected version."
            echo "Set `ASTRA_BINARY_CHECK_HASH=false` in your environment to skip this check."
            exit 1
        fi
    fi
done

# check cli interface
CLI_PATH="$ASTRA_BINARY_PATH/astra-web-cli"
if [ ! -f "$CLI_PATH" ]; then
    echo "WARNING: astra-web cli not found at $CLI_PATH"
    echo "Installing it ..."
    cp "scripts/astra-web-cli" "$CLI_PATH"
    SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
    sed -i "s|{{ASTRA_WEB_DIR}}|$SCRIPT_DIR|g" "$CLI_PATH"
    chmod ug+x "$CLI_PATH"
fi
# test cli
echo "Checking astra-web-cli ..."
"$CLI_PATH" --help > /dev/null


# run
uvicorn astra_web.web_api:app --host 0.0.0.0 --port $ASTRA_WEB_PORT
