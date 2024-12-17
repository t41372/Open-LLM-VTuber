from typing import List, Dict, Union


class PromptFormatter:
    """
    A class to format inputs for multiple LLMs such as GPT and Ollama, including support for system prompt, goals, and action context.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PromptFormatter, cls).__new__(cls)
        return cls._instance

    def __init__(self, agent_name: str = "Stella"):
        """
        Initialize the input formatter with default names for agent and user.
        :param agent_name: Name of the conversational agent.
        :param user_name: Name of the user.
        """
        self.agent_name = agent_name

    def get_agent_name(self):
        return self.agent_name

    def set_agent_name(self, agent_name):
        self.agent_name = agent_name

    def format_system_prompt(self, system_prompt: str) -> str:
        """
        Format the system prompt section.
        :param system_prompt: A string describing the system-level instructions.
        :return: Formatted system prompt section.
        """
        return f"### System Prompt\n{system_prompt.strip()}\n"

    def format_goals(self, goals: str) -> str:
        """
        Format the conversation goals section.
        :param goals: A string describing the conversation goals.
        :return: Formatted goals section.
        """
        return f"### Goals\n{goals.strip()}\n"

    def format_action_context(self, action_context: str) -> str:
        """
        Format the action context section.
        :param action_context: A string describing the agent's action context traits.
        :return: Formatted action context section.
        """
        return f"### Action Context\n{action_context.strip()}\n"

    def format_conversation_history(self, conversation: List[Dict[str, Union[str, List[Dict[str, float]]]]]) -> str:
        """
        Format the conversation history.
        :param conversation: A list of dictionaries with keys 'role', 'name', and 'content'.
                             Each entry represents a single message (e.g., from user or agent).
        :return: Formatted conversation history section.
        """
        formatted_messages = ''
        for message in conversation:
            name = message["name"]
            content = message["content"]
            emotions = message["emotions"]
            current_message = f"{name}: {content}\nEmotions: {emotions}\n"
            formatted_messages += current_message
        return formatted_messages

    def format_for_gpt(
            self,
            goals: str,
            action_context: str,
            conversation: List[Dict[str, Union[str, List[Dict[str, float]]]]]
    ) -> str:
        """
        Format the prompt for GPT.
        :param persona_prompt: the persona of the agent.
        :param goals: The conversation goals.
        :param action_context: The agent's action context traits.
        :param conversation: The conversation history.
        :return: Formatted prompt string.
        """
        goals_section = self.format_goals(goals)
        action_context_section = self.format_action_context(action_context)
        conversation_history_section = self.format_conversation_history(conversation)
        return (
            f"{goals_section}\n{action_context_section}\n"
            f"### Conversation History\n{conversation_history_section}\n### Response"
        )

    def format_for_ollama(
            self,
            persona_prompt: str,
            goals: str,
            action_context: str,
            conversation: List[Dict[str, Union[str, List[Dict[str, float]]]]]
    ) -> Dict[str, Union[str, List]]:
        """
        Format the input for Ollama, which typically uses JSON-like input.
        :param persona_prompt: The persona for generation
        :param goals: The conversation goals.
        :param action_context: The agent's action context traits.
        :param conversation: The conversation history.
        :return: A dictionary formatted for Ollama.

        Args:
            persona_prompt:
        """
        if conversation is not None:
            formatted_conversation = [
                {
                    "role": conversation["role"],
                    "name": conversation["name"],
                    "content": conversation["content"],
                    "emotions": conversation["emotions"]
                }

            ]
        else:
            formatted_conversation = []
        return {
            "persona": persona_prompt.strip(),
            "goals": goals.strip(),
            "action_context": action_context.strip(),
            "conversation_history": formatted_conversation,
            "system_prompt": "Generate a response based on the system prompt, goals, action context, and conversation history, consider your emotions, the user emotions and respond only if you want to"
        }

    def format_prompt(
            self,
            llm: str,
            persona_prompt: str,
            goals: str,
            action_context: str,
            conversation: List[Dict[str, Union[str, List[Dict[str, float]]]]]
    ) -> Union[str, Dict[str, Union[str, List]]]:
        """
        Format the prompt for a specified LLM.
        :param llm: The target LLM ("gpt" or "ollama").
        :param persona_prompt: The persona for generation.
        :param goals: The conversation goals.
        :param action_context: The agent's action context traits.
        :param conversation: The conversation history.
        :return: A formatted string or dictionary for the LLM.
        """
        if llm.lower() == "gpt":
            return self.format_for_gpt(goals, action_context, conversation)
        elif llm.lower() == "ollama":
            return self.format_for_ollama(persona_prompt, goals, action_context, conversation)
        else:
            raise ValueError(f"Unsupported LLM: {llm}")
