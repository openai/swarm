import unittest
from swarm.util import function_to_json


class TestFunctionToJson(unittest.TestCase):
    def test_basic_function(self):
        def basic_function(arg1, arg2):
            return arg1 + arg2

        result = function_to_json(basic_function)
        self.assertEqual(result, {
            "type": "function",
            "function": {
                "name": "basic_function",
                "description": "",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg1": {"type": "string"},
                        "arg2": {"type": "string"},
                    },
                    "required": ["arg1", "arg2"],
                },
            },
        })

    def test_complex_function(self):
        def complex_function_with_types_and_descriptions(
            arg1: int, arg2: str, arg3: float = 3.14, arg4: bool = False
        ):
            """This is a complex function with a docstring."""
            pass

        result = function_to_json(complex_function_with_types_and_descriptions)
        self.assertEqual(result, {
            "type": "function",
            "function": {
                "name": "complex_function_with_types_and_descriptions",
                "description": "This is a complex function with a docstring.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg1": {"type": "integer"},
                        "arg2": {"type": "string"},
                        "arg3": {"type": "number"},
                        "arg4": {"type": "boolean"},
                    },
                    "required": ["arg1", "arg2"],
                },
            },
        })


if __name__ == "__main__":
    unittest.main()
