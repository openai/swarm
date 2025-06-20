import util

def fetch_wikipedia_content(search_query: str) -> dict:
    """Fetches wikipedia content for a given search_query"""
    return {"status": "success", "message": f"Fetched content for {search_query}"}

if __name__ == "__main__":
    # 関数オブジェクトを指定してテスト
    tool_info = util.generate_tool_info(fetch_wikipedia_content)

    print("Generated Tool Info:")
    print(tool_info)

    # 検証
    assert tool_info["function"]["name"] == fetch_wikipedia_content.__name__, "Function name mismatch"
    assert "parameters" in tool_info["function"], "Parameters missing in tool info"
    assert "search_query" in tool_info["function"]["parameters"]["properties"], "search_query parameter missing"

    print("All tests passed!")
