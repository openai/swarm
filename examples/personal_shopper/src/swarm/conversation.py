class Conversation:
    def __init__(self):
        self.history = []  # Stores all messages, tool calls, and outputs
        self.current_messages = []  # Stores messages of the current interaction
        self.summary = None

    def add_tool_call(self, tool_call):
        self.history.append(tool_call)

    def add_output(self, output):
        self.history.append(output)

    def summarize(self):
        # Implement summarization logic here
        self.summary = "Summary of the conversation"

    def get_summary(self):
        if not self.summary:
            self.summarize()
        return self.summary

    def clear_current_messages(self):
        self.current_messages = []

    def __repr__(self):
        return f"Conversation(History: {len(self.history)}, Current Messages: {len(self.current_messages)}, Summary: {self.summary})"
