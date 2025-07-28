[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

# ASTRA Web API
This repository is based on [astra-web](https://github.com/AlexanderKlemps/astra-web) by A. Klemps (Hamburg University of Technology, TUHH) and contains an API wrapper for the well-known [ASTRA simulation code](https://www.desy.de/~mpyflo/) by
K. Floettmann (DESY Hamburg) based on the Python FastAPI package and Docker.

This fork includes modification for improved interoperability with a SLURM environment.

# Startup

## Environment

Ensure the following environment variables are set (e.g. in `./docker/.env`)

| Variable          | Required | Description                                                                  |
|-------------------|----------|------------------------------------------------------------------------------|
| `ASTRA_API_KEY`   | yes      | The API key to access the ASTRA web API. This is required for authorization. |
| `ASTRA_DATA_PATH` | optional | The path to a local data directory where all results are stored. If not specified an internal storage volume will be used.|

note: Ensure that the user starting the Docker container has read and write access to the `ASTRA_DATA_PATH` directory when specified.

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
