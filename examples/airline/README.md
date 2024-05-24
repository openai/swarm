# Airline customer service

This example demonstrates a multi-assistant setup for handling different customer service requests in an airline context using the Swarm framework. The assistants can triage requests, handle flight modifications, cancellations, and lost baggage cases.
This example uses the helper function `run_demo_loop`, which allows us to create an interactive Swarm session.

## Assistants

1. **Triage Assistant**: Determines the type of request and transfers to the appropriate assistant.
2. **Flight Modification Assistant**: Handles requests related to flight modifications, further triaging them into:
    - **Flight Cancel Assistant**: Manages flight cancellation requests.
    - **Flight Change Assistant**: Manages flight change requests.
3. **Lost Baggage Assistant**: Handles lost baggage inquiries.

## Setup

Once you have installed dependencies and Swarm, run the example using:

```shell
python3 main.py
```
## Evaluations
> [!NOTE]
> These evals are intended to be examples to demonstrate functionality, but will have to be updated and catered to your particular use case.

For this example, we run function evals, where we input a conversation, and the expected function call ('None' if no function call is expected).
The evaluation cases are stored in `eval/eval_cases/` subfolder.
```json
[
    {
        "conversation": [
            {"role": "user", "content": "My bag was not delivered!"}
        ],
        "function": "transfer_to_lost_baggage"
    },
    {
        "conversation": [
            {"role": "user", "content": "I had some turbulence on my flight"}
        ],
        "function": "None"
    }
]
```



The script 'function_evals.py' will run the evals. Make sure to set `n` to the number
of times you want to run each particular eval. To run the script from the root airline folder, execute:
```bash
cd evals
python3 function_evals.py
```

The results of these evaluations will be stored in `evals/eval_results/`

