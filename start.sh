#!/usr/bin/env bash

set -eo pipefail

# environment
# NOTE: previously defined variables are not overwritten
: "${ASTRA_WEB_ENV_FILE:=.env}"

# check if file exists
if [[ -f "$ASTRA_WEB_ENV_FILE" ]]; then

  # load undefined variables
  while IFS='=' read -r key value; do
    # skip empty lines and comments
    [[ -z "$key" || "$key" =~ ^# ]] && continue

    # trim whitespace around key
    key="${key//[[:space:]]/}"

    # strip surrounding quotes from value
    value="${value%\"}"   # remove trailing double quote
    value="${value#\"}"   # remove leading double quote
    value="${value%\'}"   # remove trailing single quote
    value="${value#\'}"   # remove leading single quote

    # export only if the variable was undefined
    if [[ ! -v "$key" ]]; then
        export "$key=$value"
    else
        echo "INFO: Environment variable $key is already defined as \"$value\", skipping value from \`$ASTRA_WEB_ENV_FILE\`"
    fi
  done < "$ASTRA_WEB_ENV_FILE"

else
  echo "INFO: No environment file found at \`$ASTRA_WEB_ENV_FILE\`!"
fi

# defaults
: "${ASTRA_BINARY_CHECK_HASH:=false}"
: "${ASTRA_WEB_PORT:=8000}"

# ensure all required environment variables are set
required_env_vars=(ASTRA_WEB_API_KEY ASTRA_DATA_PATH ASTRA_BINARY_PATH)
for v in "${required_env_vars[@]}"; do
  if [[ ! -v $v ]]; then
    echo "ERROR: Environment variable $v is NOT defined!"
    exit 1
  fi
done


# setup python
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate
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
