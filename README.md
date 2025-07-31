[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

# ASTRA Web API
This repository is based on [astra-web](https://github.com/AlexanderKlemps/astra-web) by A. Klemps (Hamburg University of Technology, TUHH) and contains an API wrapper for the well-known [ASTRA simulation code](https://www.desy.de/~mpyflo/) by
K. Floettmann (DESY Hamburg) based on the Python FastAPI package and Docker.

This fork includes modification for improved interoperability with a SLURM environment.

# Requirements
- Linux (kernel v6.12+)
- docker compose (v2.38+)
- python (v3.13+)

Older versions may work, but are not tested.

# Startup

## Environment

Ensure the following environment variables are set (e.g. in `./docker/.env`)

| Variable          | Required | Description                                                                  |
|-------------------|----------|------------------------------------------------------------------------------|
| `ASTRA_API_KEY`   | yes      | The API key to access the ASTRA web API. This is required for authorization. |
| `ASTRA_DATA_PATH` | optional | The path to a local data directory where all results are stored. If not specified an internal storage volume will be used.|

note: Ensure that the user starting the Docker container has read and write access to the `ASTRA_DATA_PATH` directory when specified.

See [SLURM](#slurm) for additional environment variables required to connect to a SLURM server for remote execution.

## Local deployment in development environment 

Build the image and start container by execution of the following command

    docker compose stop && docker compose up -d --build

## Deployment in productive environment

In case you would like to deploy the API in a productive environment, say on a remote server, it is recommended to do
this via [Docker contexts](https://docs.docker.com/engine/context/working-with-contexts/).

Uncomment the COMPOSE_FILE environment variable in the .env file contained within this project an run

    docker context use [YOUR_REMOTE_CONTEXT]
    docker compose stop && docker compose up -d --build

# API documentation

In case you are running the API server locally, you will find the interactive API documentation under

    http://localhost:8000/docs

# SLURM
If you want to dispatch some computations to a [SLURM cluster](https://slurm.schedmd.com) carefully follow the instructions below. Otherwise you can skip this section.
Using SLURM is recommended for larger simulations only.
Successful execution on the cluster and correct execution order may not be checked.

Some operations may be simple enough to be executed locally and it is recommended to **mix local and remote execution**.

> ⚠️ Connecting to SLURM requires some advanced knowledge! Check the log files of the container if you recive internal errors.

## Setup
1. Ensure `docker-compose.slurm.yml` is included in your docker compose setup. (e.g. in `.env` under `COMPOSE_FILE`)

2. Set the following environment variables (e.g. in `./docker/.env`):

| Variable                      | Required | Description                                                                        | Example                                               |
|-------------------------------|----------|------------------------------------------------------------------------------------|-------------------------------------------------------|
| `SLURM_URL`                   | yes      | The URL of the [SLURM REST API](https://slurm.schedmd.com/rest_api.html).          | `https://slurm-rest.example.com/sapi/slurm/v0.0.40`   |
| `SLURM_PROXY` [1]             | optional | The URL of a SOCKS5 proxy to connect to the SLURM REST API.                        | `socks5h://host.docker.internal:1081`                 |
| `SLURM_USER_NAME`             | yes      | The SLURM user name.                                                               | `<user>`                                              |
| `SLURM_USER_TOKEN`            | yes      | The [JWT token](https://slurm.schedmd.com/jwt.html) to authenticate the SLURM user.|                                                 |
| `SLURM_ENVIRONMENT` [2]       | yes      | The environment variables to set for the SLURM job.                                |`"PATH=/bin:/usr/bin/:/usr/local/bin/","MORE="values"` |
| `SLURM_ASTRA_BINARY_PATH` [3] | yes      | The path to the ASTRA binary **as seen by the SLURM cluster!**                     | `/home/<user>/astra/bin`                              |
| `SLURM_DATA_PATH` [4]         | yes      | The path to the data directory **as seen by the SLURM cluster!**                   | `/home/<user>/astra/data`                             |

- [1]: In case the SLURM server is not reachable from the local host and requires a tunnel. See section on [Using a Proxy](#using-a-proxy).
- [2]: List of quoted strings separated by commas without spaces! Escaping commas inside strings is not possible!
- [3]: Ensure the versions of ASTRA match your local ones and the **⚠️binaries are renamed to [`astra`](https://www.desy.de/~mpyflo/Astra_for_64_Bit_Linux/) and [`parallel_astra`](https://www.desy.de/~mpyflo/Parallel_Astra_for_Linux)⚠️**.
- [4]: The paths for these files will most likely differ from the local paths on your machine. It is important that your local paths bind to the same directories as for the remote host as described in [Mount Data Directory](#mount-data-directory).

## Mount Data Directory
This step is critical to ensure local and remote execution work together seamlessly.

Mount the remote data directory as following:

```bash
sshfs -o idmap=user -o allow_other <user>@<bastion_host>:<SLURM_DATA_PATH> <ASTRA_DATA_PATH>
```

> ⚠️ Mount your data folder directly under `ASTRA_DATA_PATH` as shown above. **Do not mount a parent folder** as docker then cannot access the files for technical reasons.

## Using a Proxy
Consider using a VPN if you can to avoid this step.

If you need to connect to the SLURM server which has to be accessed via an SSH tunnel, you can use the `SLURM_PROXY` environment variable to specify the SOCKS5 proxy.

Setup the tunnel via SSH as in
```bash
ssh -D 1080 -N <user>@<bastion_host>
```

Forward the port to the container via 
```bash
socat TCP-LISTEN:1081,fork TCP:127.0.0.1:1080 
```

# Troubleshooting

### Problem: Rootless containers on the remote host quit once the user terminates the ssh session.
    
This is not an issue of Docker. Linux stops processes started by a normal user if loginctl is configured to not use 
lingering, to prevent normal users to keep long-running processes executing in the system.
In order to fix the problem, one can enable lingering by executing 

    loginctl enable-linger $UID

on the remote host.
Source: [Stackoverflow](https://stackoverflow.com/a/73312070)

# Cite this project

If you use this project in your scientific work and find it useful, you could use the following BibTeX entry to cite this project.

      @misc{astra-web,
        Author = {A. Klemps},
        Title = {ASTRA-Web},
        Year = {2024},
        publisher = {GitHub},
        version = {0.1.0},
        doi = {10.5281/zenodo.12606498},
        url = {https://doi.org/10.5281/zenodo.12606498}
      }
