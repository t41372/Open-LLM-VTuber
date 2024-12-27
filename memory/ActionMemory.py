from typing import TYPE_CHECKING, List, Optional

from letta.schemas.agent import AgentState
from letta.schemas.memory import Memory

# Forward referencing to avoid circular import with Agent -> Memory -> Agent
if TYPE_CHECKING:
    pass

from letta.schemas.block import Block


class ActionMemory(Memory):
    """
    BasicBlockMemory is a basic implemention of the Memory class, which takes in a list of blocks and links them to the memory object. These are editable by the agent via the core memory functions.

    Attributes:
        memory (Dict[str, Block]): Mapping from memory block section to memory block.

    Methods:
        core_memory_append: Append to the contents of core memory.
        core_memory_replace: Replace the contents of core memory.
    """

    def __init__(self, blocks: List[Block] = []):
        """
        Initialize the BasicBlockMemory object with a list of pre-defined blocks.

        Args:
            blocks (List[Block]): List of blocks to be linked to the memory object.
        """
        super().__init__(blocks=blocks)

    def core_memory_append(self,agent_state: "AgentState", label: str, content: str) -> Optional[str]:  # type: ignore
        """
        Append to the contents of core memory.

        Args:
            agent_state: The AgentState object. ie. the agent itself.
            label (str): Section of the memory to be edited (persona or human).
            content (str): Content to write to the memory. All unicode (including emojis) are supported.

        Returns:
            Optional[str]: None is always returned as this function does not produce a response.
        """
        current_value = str(agent_state.memory.get_block(label).value)
        new_value = current_value + "\n" + str(content)
        agent_state.memory.update_block_value(label=label, value=new_value)
        return None

    def core_memory_replace(self,agent_state: "AgentState", label: str, old_content: str, new_content: str) -> Optional[str]:  # type: ignore
        """
        Replace the contents of core memory. To delete memories, use an empty string for new_content.

        Args:
            agent_state: The AgentState object.ie, The Agent itself
            label (str): Section of the memory to be edited (persona or human).
            old_content (str): String to replace. Must be an exact match.
            new_content (str): Content to write to the memory. All unicode (including emojis) are supported.

        Returns:
            Optional[str]: None is always returned as this function does not produce a response.
        """
        current_value = str(agent_state.memory.get_block(label).value)
        if old_content not in current_value:
            raise ValueError(f"Old content '{old_content}' not found in memory block '{label}'")
        new_value = current_value.replace(str(old_content), str(new_content))
        agent_state.memory.update_block_value(label=label, value=new_value)
        return None








