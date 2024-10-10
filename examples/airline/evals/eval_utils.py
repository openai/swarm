import datetime
import json
import uuid

from swarm import Swarm


def run_function_evals(agent, test_cases, n=1, eval_path=None):
    correct_function = 0
    results = []
    eval_id = str(uuid.uuid4())
    eval_timestamp = datetime.datetime.now().isoformat()
    client = Swarm()

    for test_case in test_cases:
        case_correct = 0
        case_results = {
            "messages": test_case["conversation"],
            "expected_function": test_case["function"],
            "actual_function": [],
            "actual_message": [],
        }
        print(50 * "--")
        print(f"\033[94mConversation: \033[0m{test_case['conversation']}\n")
        for i in range(n):
            print(f"\033[90mIteration: {i + 1}/{n}\033[0m")
            response = client.run(
                agent=agent, messages=test_case["conversation"], max_turns=1
            )
            output = extract_response_info(response)
            actual_function = output.get("tool_calls", "None")
            actual_message = output.get("message", "None")

            case_results["actual_function"].append(actual_function)
            case_results["actual_message"].append(actual_message)

            if "tool_calls" in output:
                print(
                    f'\033[95mExpected function: \033[0m {test_case["function"]}, \033[95mGot: \033[0m{output["tool_calls"]}\n'
                )
                if output["tool_calls"] == test_case["function"]:
                    case_correct += 1
                    correct_function += 1

            elif "message" in output:
                print(
                    f'\033[95mExpected function: \033[0m {test_case["function"]}, \033[95mGot: \033[0mNone'
                )
                print(f'\033[90mMessage: {output["message"]}\033[0m\n')
                if test_case["function"] == "None":
                    case_correct += 1
                    correct_function += 1

        case_accuracy = (case_correct / n) * 100
        case_results["case_accuracy"] = f"{case_accuracy:.2f}%"
        results.append(case_results)

        print(
            f"\033[92mCorrect functions for this case: {case_correct} out of {n}\033[0m"
        )
        print(f"\033[93mAccuracy for this case: {case_accuracy:.2f}%\033[0m")
    overall_accuracy = (correct_function / (len(test_cases) * n)) * 100
    print(50 * "**")
    print(
        f"\n\033[92mOVERALL: Correct functions selected: {correct_function} out of {len(test_cases) * n}\033[0m"
    )
    print(f"\033[93mOVERALL: Accuracy: {overall_accuracy:.2f}%\033[0m")

    final_result = {
        "id": eval_id,
        "timestamp": eval_timestamp,
        "results": results,
        "correct_evals": correct_function,
        "total_evals": len(test_cases) * n,
        "overall_accuracy_percent": f"{overall_accuracy:.2f}%",
    }

    if eval_path:
        try:
            with open(eval_path, "r") as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = []

        if not isinstance(existing_data, list):
            existing_data = [existing_data]

        existing_data.append(final_result)

        with open(eval_path, "w") as file:
            json.dump(existing_data, file, indent=4)

    return overall_accuracy

    return overall_accuracy


def extract_response_info(response):
    results = {}
    for message in response.messages:
        if message["role"] == "tool":
            results["tool_calls"] = message["tool_name"]
            break
        elif not message["tool_calls"]:
            results["message"] = message["content"]
    return results
