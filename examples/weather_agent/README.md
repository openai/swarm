# Weather agent

This example is a weather agent demonstrating function calling with a single agent. The agent has tools to get the weather of a particular city, and send an email.

## Setup

To run the weather agent Swarm:

1. Run

```shell
python3 run.py
```

## Evals

> [!NOTE]
> These evals are intended to be examples to demonstrate functionality, but will have to be updated and catered to your particular use case.

This example uses `Pytest` to run eval unit tests. We have two tests in the `evals.py` file, one which
tests if we call the `get_weather` function when expected, and one which assesses if we properly do NOT call the
`get_weather` function when we shouldn't have a tool call.

To run the evals, run

```shell
pytest evals.py
```
