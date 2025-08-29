[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

# ASTRA Web API
This repository is based on [astra-web](https://github.com/AlexanderKlemps/astra-web) by A. Klemps (Hamburg University of Technology, TUHH) and contains an API wrapper for the well-known [ASTRA simulation code](https://www.desy.de/~mpyflo/) by
K. Floettmann (DESY Hamburg) based on the Python FastAPI package.

This fork includes modification for improved interoperability with a SLURM environment (more specifically the Maxwell cluster at DESY Hamburg).

# Requirements
Older versions may work, but are not tested.

## local
- Linux (kernel v6.12+)
- python (v3.13+)
- openmpi (v5.0.3+, optional for multi-threaded simulations, ensure `libmpi_usempi.so.40` is available)
## remote
- SLURM (v0.0.40+, optional for remote execution on cluster)


# Setup
## Install openmpi (optional, for local multi-treaded simulations)
In case you want to run ASTRA in multi-threaded mode on the local host also install openmpi (see [Parallel Astra Readme](https://www.desy.de/~mpyflo/Parallel_Astra_for_Linux/AAA_Readme.txt)).

When using [SLURM](#slurm), the SLURM server may take care of the parallel execution in that case openmpi is not required.

⚠️ Ensure that the `libmpi_usempi.so.40` is available via the `LD_LIBRARY_PATH` environment variable. E.g. create a symlink to `.../openmpi/5.0.3/lib/libmpi_usempi_ignore_tkr.so.40` in `./lib` and append `.lib` to `LD_LIBRARY_PATH`.

## Environment
Create `bare/.env` and set the environment variables according to:

| Variable            | Required | Description                                                                  |
|---------------------|----------|------------------------------------------------------------------------------|
| `ASTRA_WEB_API_KEY` | yes      | The API key to access the ASTRA web API. This is required for authorization. |
| `ASTRA_DATA_PATH`   | yes      | The path to a local data directory where all results are stored.             |
| `ASTRA_BINARY_PATH` | yes      | The path to the folder with ASTRA binaries. Binaries must be called `generator`, `astra` and `parallel_astra` respectively. |

See [SLURM](#slurm) for additional environment variables required to connect to a SLURM server for remote execution.

## Start
Start the server locally by executing the following command in the root directory of this project:

    ./start_bare.sh

# API Documentation

Once the server is [set up](#setup) you will find the interactive API documentation under

    http://<host>:8000/docs

where `<host>` is the URL of the host where the server is running. E.g. `localhost` when accessed locally.

⚠️ All communication with the host is done via HTTP which provides **no encryption**! Allways route your trafic through a secure connection like a VPN or SSH tunnel to ensure your data (e.g. tokens) is protected!

# SLURM
If you want to dispatch some computations to a [SLURM cluster](https://slurm.schedmd.com) carefully follow the instructions below. Otherwise you can skip this section.
Using SLURM is recommended for resource intensive simulations only.
Fig. 1 shows a schematic for when ASTRA web is set up with SLURM.

> ⚠️ Using SLURM may lead to unexpected problems! Check the server log if any are encountered. 

```mermaid
flowchart LR
    you((your device))
    astra_web[ASTRA Web
    Server]
    SLURM[SLURM Cluster
    Server]
    server_data[(server data)]
    cluster_data[(persistent storage)]

    you--https-->astra_web
    astra_web--https-->SLURM
    astra_web-->server_data
    server_data--mount or is-->cluster_data
    SLURM--mount-->cluster_data

    style you fill:#fff,stroke:#333,color:#000
    style astra_web fill:#fff,stroke:#333,color:#000
    style server_data fill:#fff,stroke:#333,color:#000
    style SLURM fill:#aaa,stroke:#000,color:#000
    style cluster_data fill:#aaa,stroke:#000,color:#000

    %% legend
    subgraph legend [ ]
        legend_item1(["ASTRA Web"])
        legend_item2(["SLURM (optional)"])
        style legend_item1 fill:#fff,stroke:#333,color:#000
        style legend_item2 fill:#aaa,stroke:#000,color:#000
    end
    style legend fill:transparent,stroke:transparent,color:transparent
```
Fig. 1: Schematic overview of the ASTRA Web with SLURM support. The ASTRA Web server is accessed via a REST API over the https protocol. Some actions may be dispatched to a SLURM cluster for asynchronous execution via its own REST API. All data is stored persistently in the cluster. In case the server has no direct access to the persistent storage, it has to be mounted manually (see [Mount Data Directory](#mount-data-directory)).

## SLURM Environment
In addition to the [basic environment](#environment), set the following environment variables (e.g. in `./docker/.env`):

| Variable                      | Required | Description                                                                        | Example                                               |
|-------------------------------|----------|------------------------------------------------------------------------------------|-------------------------------------------------------|
| `SLURM_BASE_URL`                   | yes      | The URL of the [SLURM REST API](https://slurm.schedmd.com/rest_api.html).          | `https://slurm-rest.example.com/sapi`   |
| `SLURM_API_VERSION` [0]       | yes      | The version of the SLURM REST API to use.                                          | `v0.0.40`                                            |
| `SLURM_PROXY` [1]             | optional | The URL of a SOCKS5 proxy to connect to the SLURM REST API.                        | `socks5h://host.docker.internal:1080`                 |
| `SLURM_USER_NAME`             | yes      | The SLURM user name.                                                               | `<user>`                                              |
| `SLURM_USER_TOKEN` [2]          | yes      | The [JWT token](https://slurm.schedmd.com/jwt.html) to authenticate the SLURM user.|                                                 |
| `SLURM_PARTITION`             | yes      | The SLURM partition to use for the job.                                            | `short`                                              |
| `SLURM_CONSTRAINTS`           | optional | The SLURM constraints to use for the job. This is a comma-separated list of constraints. | `gpu,highmem`, `none` |
| `SLURM_ENVIRONMENT` [3]       | yes      | The environment variables to set for the SLURM job.                                |`"PATH=/bin:/usr/bin/:/usr/local/bin/","MORE="values"` |
| `SLURM_ASTRA_BINARY_PATH` [4] | yes      | The path to the ASTRA binary **as seen by the SLURM cluster!**                     | `/home/<user>/astra/bin`                              |
| `SLURM_DATA_PATH` [5]         | yes      | The path to the data directory **as seen by the SLURM cluster!**                   | `/home/<user>/astra/data`                             |
| `SLURM_OUTPUT_PATH` [6]       | optional | The path to a directory where the slurm output should be written to.               | `/home/<user>/slurm` or `./slurm`|
| `SLURM_SCRIPT_SETUP` | optional | A BASH script fragment to be executed inside the job script before each dispatched command. | `module purge\nmodule load openmpi` |

- [0]: A complete example URL of an endpoint is `https://slurm-rest.example.com/sapi/slurm/v0.0.40/jobs`.
- [1]: In case the SLURM server is not reachable from the local host and requires a tunnel. See section on [Using a Proxy](#using-a-proxy).
- [2]: The **⚠️SLURM token may expire⚠️** due to limited a lifetime. Make sure to refresh it regularly via the endpoint `/slurm/configuration/user_token`.
- [3]: List of quoted strings separated by commas without spaces! Escaping commas inside strings is not possible!
- [4]: Ensure the versions of ASTRA match your local ones and the **⚠️binaries are renamed to [`astra`](https://www.desy.de/~mpyflo/Astra_for_64_Bit_Linux/) and [`parallel_astra`](https://www.desy.de/~mpyflo/Parallel_Astra_for_Linux)⚠️**.
- [5]: The paths for these files will most likely differ from the local paths on your machine. It is important that your local paths bind to the same directories as for the remote host as described in [Mount Data Directory](#mount-data-directory).
- [6]: The output of the SLURM job itself is allways separated from the output of the ASTRA computations and may be ignored. This keeps the output files from ASTRA clean and independent of the execution host.

## Mount Data Directory
This step is critical to ensure local and remote execution work together seamlessly.

Mount the remote data directory as following:

```bash
sshfs -o idmap=user -o allow_other <user>@<bastion_host>:<SLURM_DATA_PATH> <ASTRA_DATA_PATH>
```

## Using a Proxy
When the server is positioned outside of the network of the SLURM cluster and using a VPN is not an option one can use an ssh tunnel to access SLURM.

Setup the tunnel via SSH as in
```bash
ssh -D 1080 -N <user>@<bastion_host>
```

And set the `SLURM_PROXY` [environment](#slurm-environment) variable to specify the SOCKS5 proxy.