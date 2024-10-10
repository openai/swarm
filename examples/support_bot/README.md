# Support bot

This example is a customer service bot which includes a user interface agent and a help center agent with several tools.
This example uses the helper function `run_demo_loop`, which allows us to create an interactive Swarm session.

## Overview

The support bot consists of two main agents:

1. **User Interface Agent**: Handles initial user interactions and directs them to the help center agent based on their needs.
2. **Help Center Agent**: Provides detailed help and support using various tools and integrated with a Qdrant VectorDB for documentation retrieval.

## Setup

To start the support bot:

1. Ensure Docker is installed and running on your system.
2. Install the necessary additional libraries:

```shell
make install
```

3. Initialize docker

```shell
docker-compose up -d
```

4. Prepare the vector DB:

```shell
make prep
```

5. Run the main scripy:

```shell
make run
```
