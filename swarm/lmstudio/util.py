import inspect

def generate_tool_info(function):
    """
    指定した関数をLMStudio用のツール情報として出力する。

    Args:
        function (callable): ツール化したい関数オブジェクト。

    Returns:
        dict: LMStudio対応のツール情報構造。
    """
    # 関数のシグネチャとドキュメンテーション文字列を取得
    signature = inspect.signature(function)
    docstring = function.__doc__ or ""

    # 引数情報を解析してプロパティ構造を構築
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    for param_name, param in signature.parameters.items():
        param_info = {
            "type": "string",  # デフォルトはstring型（型注釈がない場合）
            "description": ""
        }

        # 型注釈を解析
        if param.annotation is not inspect.Parameter.empty:
            python_to_json_type = {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                dict: "object",
                list: "array",
            }
            param_info["type"] = python_to_json_type.get(param.annotation, "string")

        # 必須引数を設定
        if param.default is inspect.Parameter.empty:
            parameters["required"].append(param_name)

        parameters["properties"][param_name] = param_info

    # ツール情報の辞書を構築
    tool_info = {
        "type": "function",
        "function": {
            "name": function.__name__,
            "description": docstring.strip(),
            "parameters": parameters,
        }
    }

    return tool_info
