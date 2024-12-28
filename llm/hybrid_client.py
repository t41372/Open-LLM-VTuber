import time
from typing import Callable, Dict, Generator, List, Optional, Union

import requests
from letta.client.client import AbstractClient
from letta.constants import (
    ADMIN_PREFIX,
    BASE_MEMORY_TOOLS,
    BASE_TOOLS,
    DEFAULT_HUMAN,
    DEFAULT_PERSONA,
    FUNCTION_RETURN_CHAR_LIMIT,
)
from letta.data_sources.connectors import DataConnector
from letta.functions.functions import parse_source_code
from letta.schemas.agent import AgentState, AgentType, CreateAgent, UpdateAgentState
from letta.schemas.block import Block, BlockUpdate, CreateBlock, Human, Persona, UpdatePersona, UpdateHuman
from letta.schemas.embedding_config import EmbeddingConfig
# new schemas
from letta.schemas.enums import JobStatus, MessageRole
from letta.schemas.file import FileMetadata
from letta.schemas.job import Job
from letta.schemas.letta_request import LettaRequest, LettaStreamingRequest
from letta.schemas.letta_response import LettaResponse, LettaStreamingResponse
from letta.schemas.llm_config import LLMConfig
from letta.schemas.memory import (
    ArchivalMemorySummary,
    CreateArchivalMemory,
    Memory,
    RecallMemorySummary, BasicBlockMemory,
)
from letta.schemas.message import Message, MessageCreate, MessageUpdate
from letta.schemas.openai.chat_completions import ToolCall
from letta.schemas.organization import Organization
from letta.schemas.passage import Passage
from letta.schemas.sandbox_config import (
    E2BSandboxConfig,
    LocalSandboxConfig,
    SandboxConfig,
    SandboxEnvironmentVariable,
)
from letta.schemas.source import Source, SourceCreate, SourceUpdate
from letta.schemas.tool import Tool, ToolCreate, ToolUpdate
from letta.schemas.tool_rule import BaseToolRule
from letta.server.rest_api.interface import QueuingInterface
from letta.server.server import SyncServer


class HybridClient(AbstractClient):
    """
    REST client for Letta

    Attributes:
        base_url (str): Base URL of the REST API
        headers (Dict): Headers for the REST API (includes token)
    """

    def __init__(
            self,
            base_url: str,
            token: str = None,
            api_prefix: str = "v1",
            debug: bool = False,
            default_llm_config: Optional[LLMConfig] = None,
            default_embedding_config: Optional[EmbeddingConfig] = None,
            headers: Optional[Dict] = None,
    ):
        """
        Initializes a new instance of Client class.

        Args:
            auto_save (bool): Whether to automatically save changes.
            user_id (str): The user ID.
            debug (bool): Whether to print debug information.
            default_llm_config (Optional[LLMConfig]): The default LLM configuration.
            default_embedding_config (Optional[EmbeddingConfig]): The default embedding configuration.
            headers (Optional[Dict]): The additional headers for the REST API.
        """
        super().__init__(debug=debug)
        self.base_url = base_url
        self.api_prefix = api_prefix
        self.headers = {"accept": "application/json", "authorization": f"Bearer {token}"}
        if headers:
            self.headers.update(headers)
        self._default_llm_config = default_llm_config
        self._default_embedding_config = default_embedding_config
        self.interface = QueuingInterface(debug=debug)
        self.server = SyncServer(default_interface_factory=lambda: self.interface)
        self.user_id = self.server.user_manager.DEFAULT_USER_ID
        self.user = self.server.get_user_or_default(self.user_id)

    def list_agents(self, tags: Optional[List[str]] = None) -> List[AgentState]:
        params = {}
        if tags:
            params["tags"] = tags

        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents", headers=self.headers, params=params)
        return [AgentState(**agent) for agent in response.json()]

    def agent_exists(self, agent_id: str) -> bool:
        """
        Check if an agent exists

        Args:
            agent_id (str): ID of the agent
            agent_name (str): Name of the agent

        Returns:
            exists (bool): `True` if the agent exists, `False` otherwise
        """

        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}", headers=self.headers)
        if response.status_code == 404:
            # not found error
            return False
        elif response.status_code == 200:
            return True
        else:
            raise ValueError(f"Failed to check if agent exists: {response.text}")

    def create_agent(
            self,
            name: Optional[str] = None,
            # agent config
            agent_type: Optional[AgentType] = AgentType.memgpt_agent,
            # model configs
            embedding_config: EmbeddingConfig = None,
            llm_config: LLMConfig = None,
            # memory
            memory: Memory = BasicBlockMemory(blocks=[]),
            # system
            system: Optional[str] = None,
            # tools
            tools: Optional[List[str]] = None,
            tool_rules: Optional[List[BaseToolRule]] = None,
            include_base_tools: Optional[bool] = True,
            # metadata
            metadata: Optional[Dict] = {"human:": DEFAULT_HUMAN, "persona": DEFAULT_PERSONA},
            description: Optional[str] = None,
            initial_message_sequence: Optional[List[Message]] = None,
            tags: Optional[List[str]] = None,
    ) -> AgentState:
        """Create an agent

        Args:
            agent_type: the type of agent. ie. whether MemGPT or OPENAI
            initial_message_sequence:
            tool_rules: any rules for tools in the system.
            name (str): Name of the agent
            embedding_config (EmbeddingConfig): Embedding configuration
            llm_config (LLMConfig): LLM configuration
            memory (Memory): Memory configuration
            system (str): System configuration
            tools (List[str]): List of tools
            include_base_tools (bool): Include base tools
            metadata (Dict): Metadata
            description (str): Description
            tags (List[str]): Tags for filtering agents

        Returns:
            agent_state (AgentState): State of the created agent
        """
        tool_names = []
        if tools:
            tool_names += tools
        if include_base_tools:
            tool_names += BASE_TOOLS
            tool_names += BASE_MEMORY_TOOLS

        assert embedding_config or self._default_embedding_config, f"Embedding config must be provided"
        assert llm_config or self._default_llm_config, f"LLM config must be provided"

        # create agent
        request = CreateAgent(
            name=name,
            description=description,
            metadata_=metadata,
            memory_blocks=[],
            tools=tool_names,
            tool_rules=tool_rules,
            system=system,
            agent_type=agent_type,
            llm_config=llm_config if llm_config else self._default_llm_config,
            embedding_config=embedding_config if embedding_config else self._default_embedding_config,
            initial_message_sequence=initial_message_sequence,
            tags=tags,
        )

        # Use model_dump_json() instead of model_dump()
        # If we use model_dump(), the datetime objects will not be serialized correctly
        # response = requests.post(f"{self.base_url}/{self.api_prefix}/agents", json=request.model_dump(), headers=self.headers)
        response = requests.post(
            f"{self.base_url}/{self.api_prefix}/agents",
            data=request.model_dump_json(),  # Use model_dump_json() instead of json=model_dump()
            headers={"Content-Type": "application/json", **self.headers},
        )

        if response.status_code != 200:
            raise ValueError(f"Status {response.status_code} - Failed to create agent: {response.text}")

        # gather agent state
        agent_state = AgentState(**response.json())

        # create and link blocks
        for block in memory.get_blocks():
            if not self.get_block(block.id):
                # note: this does not update existing blocks
                # WARNING: this resets the block ID - this method is a hack for backwards compat, should eventually use CreateBlock not Memory
                block = self.create_block(label=block.label, value=block.value, limit=block.limit)
            self.link_agent_memory_block(agent_id=agent_state.id, block_id=block.id)

        # refresh and return agent
        return self.get_agent(agent_state.id)

    def update_message(
            self,
            agent_id: str,
            message_id: str,
            role: Optional[MessageRole] = None,
            text: Optional[str] = None,
            name: Optional[str] = None,
            tool_calls: Optional[List[ToolCall]] = None,
            tool_call_id: Optional[str] = None,
    ) -> Message:
        request = MessageUpdate(
            role=role,
            text=text,
            name=name,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
        )
        response = requests.patch(
            f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/messages/{message_id}", json=request.model_dump(),
            headers=self.headers
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to update message: {response.text}")
        return Message(**response.json())

    def update_agent_memory(
            self,
            agent_id: str,
            name: Optional[str] = None,
            description: Optional[str] = None,
            system: Optional[str] = None,
            tools: Optional[List[str]] = None,
            tags: Optional[List[str]] = None,
            metadata: Optional[Dict] = None,
            llm_config: Optional[LLMConfig] = None,
            embedding_config: Optional[EmbeddingConfig] = None,
            message_ids: Optional[List[str]] = None,
            memory_blocks: Optional[Memory] = None,
    ):
        """
        Update an existing agent

        Args:
            memory_blocks:
            tools: list of tools for inference
            agent_id (str): ID of the agent
            name (str): Name of the agent
            description (str): Description of the agent
            system (str): System configuration
            metadata (Dict): Metadata
            llm_config (LLMConfig): LLM configuration
            embedding_config (EmbeddingConfig): Embedding configuration
            message_ids (List[str]): List of message IDs
            tags (List[str]): Tags for filtering agents

        Returns:
            agent_state (AgentState): State of the updated agent
        """
        self.interface.clear()
        agent_state = self.server.update_agent(
            UpdateAgentState(
                id=agent_id,
                name=name,
                system=system,
                tool_names=tools,
                tags=tags,
                description=description,
                metadata_=metadata,
                llm_config=llm_config,
                embedding_config=embedding_config,
                message_ids=message_ids,
                memory_blocks=memory_blocks
            ),
            actor=self.user,
        )
        return agent_state

    def update_agent(
            self,
            agent_id: str,
            name: Optional[str] = None,
            description: Optional[str] = None,
            system: Optional[str] = None,
            tool_names: Optional[List[str]] = None,
            memory: Optional[Memory] = None,

            metadata: Optional[Dict] = None,
            llm_config: Optional[LLMConfig] = None,
            embedding_config: Optional[EmbeddingConfig] = None,
            message_ids: Optional[List[str]] = None,
            tags: Optional[List[str]] = None,
    ):
        """
        Update an existing agent

        Args:
            memory:
            agent_id (str): ID of the agent
            name (str): Name of the agent
            description (str): Description of the agent
            system (str): System configuration
            tool_names (List[str]): List of tools
            metadata (Dict): Metadata
            llm_config (LLMConfig): LLM configuration
            embedding_config (EmbeddingConfig): Embedding configuration
            message_ids (List[str]): List of message IDs
            tags (List[str]): Tags for filtering agents

        Returns:
            agent_state (AgentState): State of the updated agent
        """
        request = UpdateAgentState(
            id=agent_id,
            name=name,
            system=system,
            tool_names=tool_names,
            tags=tags,
            description=description,
            metadata_=metadata,
            llm_config=llm_config,
            embedding_config=embedding_config,
            message_ids=message_ids,
            memory_blocks=memory
        )
        response = requests.patch(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}", json=request.model_dump(),
                                  headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to update agent: {response.text}")
        return AgentState(**response.json())

    def get_memory_block(self, id: str) -> Optional[Block]:
        return self.server.create_or_fetch_block_by_id(self.user_id, id)

    def get_tools_from_agent(self, agent_id: str) -> List[Tool]:
        """
        Get tools to an existing agent

        Args:
           agent_id (str): ID of the agent

        Returns:
           List[Tool]: A List of Tool objs
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/tools", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to get tools from agents: {response.text}")
        return [Tool(**tool) for tool in response.json()]

    def add_tool_to_agent(self, agent_id: str, tool_id: str):
        """
        Add tool to an existing agent

        Args:
            agent_id (str): ID of the agent
            tool_id (str): A tool id

        Returns:
            agent_state (AgentState): State of the updated agent
        """
        response = requests.patch(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/add-tool/{tool_id}",
                                  headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to update agent: {response.text}")
        return AgentState(**response.json())

    def remove_tool_from_agent(self, agent_id: str, tool_id: str):
        """
        Removes tools from an existing agent

        Args:
            agent_id (str): ID of the agent
            tool_id (str): The tool id

        Returns:
            agent_state (AgentState): State of the updated agent
        """

        response = requests.patch(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/remove-tool/{tool_id}",
                                  headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to update agent: {response.text}")
        return AgentState(**response.json())

    def rename_agent(self, agent_id: str, new_name: str):
        """
        Rename an agent

        Args:
            agent_id (str): ID of the agent
            new_name (str): New name for the agent

        """
        return self.update_agent(agent_id, name=new_name)

    def delete_agent(self, agent_id: str):
        """
        Delete an agent

        Args:
            agent_id (str): ID of the agent to delete
        """
        response = requests.delete(f"{self.base_url}/{self.api_prefix}/agents/{str(agent_id)}", headers=self.headers)
        assert response.status_code == 200, f"Failed to delete agent: {response.text}"

    def get_agent(self, agent_id: Optional[str] = None, agent_name: Optional[str] = None) -> AgentState:
        """
        Get an agent's state by it's ID.

        Args:
            agent_id (str): ID of the agent

        Returns:
            agent_state (AgentState): State representation of the agent
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}", headers=self.headers)
        assert response.status_code == 200, f"Failed to get agent: {response.text}"
        return AgentState(**response.json())

    def get_agent_id(self, agent_name: str) -> AgentState:
        """
        Get the ID of an agent by name (names are unique per user)

        Args:
            agent_name (str): Name of the agent

        Returns:
            agent_id (str): ID of the agent
        """
        # TODO: implement this
        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents", headers=self.headers,
                                params={"name": agent_name})
        agents = [AgentState(**agent) for agent in response.json()]
        if len(agents) == 0:
            return None
        agents = [agents[0]]  # TODO: @matt monkeypatched
        assert len(
            agents) == 1, f"Multiple agents with the same name: {[(agents.name, agents.id) for agents in agents]}"
        return agents[0].id

    # memory
    def get_in_context_memory(self, agent_id: str) -> Memory:
        """
        Get the in-contxt (i.e. core) memory of an agent

        Args:
            agent_id (str): ID of the agent

        Returns:
            memory (Memory): In-context memory of the agent
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/memory", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to get in-context memory: {response.text}")
        return Memory(**response.json())

    def get_core_memory(self, agent_id: str) -> Memory:
        return self.get_in_context_memory(agent_id)

    def update_in_context_memory(self, agent_id: str, section: str, value: Union[List[str], str]) -> Memory:
        """
        Update the in-context memory of an agent

        Args:
            agent_id (str): ID of the agent

        Returns:
            memory (Memory): The updated in-context memory of the agent

        """
        memory_update_dict = {section: value}
        response = requests.patch(
            f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/memory", json=memory_update_dict, headers=self.headers
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to update in-context memory: {response.text}")
        return Memory(**response.json())

    def get_archival_memory_summary(self, agent_id: str) -> ArchivalMemorySummary:
        """
        Get a summary of the archival memory of an agent

        Args:
            agent_id (str): ID of the agent

        Returns:
            summary (ArchivalMemorySummary): Summary of the archival memory

        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/memory/archival",
                                headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to get archival memory summary: {response.text}")
        return ArchivalMemorySummary(**response.json())

    def get_recall_memory_summary(self, agent_id: str) -> RecallMemorySummary:
        """
        Get a summary of the recall memory of an agent

        Args:
            agent_id (str): ID of the agent

        Returns:
            summary (RecallMemorySummary): Summary of the recall memory
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/memory/recall",
                                headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to get recall memory summary: {response.text}")
        return RecallMemorySummary(**response.json())

    def get_in_context_messages(self, agent_id: str) -> List[Message]:
        """
        Get in-context messages of an agent

        Args:
            agent_id (str): ID of the agent

        Returns:
            messages (List[Message]): List of in-context messages
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/memory/messages",
                                headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to get in-context messages: {response.text}")
        return [Message(**message) for message in response.json()]

    # agent interactions

    def user_message(self, agent_id: str, message: str) -> LettaResponse:
        """
        Send a message to an agent as a user

        Args:
            agent_id (str): ID of the agent
            message (str): Message to send

        Returns:
            response (LettaResponse): Response from the agent
        """
        return self.send_message(agent_id=agent_id, message=message, role="user", stream_tokens=True)

    def save(self):
        raise NotImplementedError

    # archival memory

    def get_archival_memory(
            self, agent_id: str, before: Optional[str] = None, after: Optional[str] = None, limit: Optional[int] = 1000
    ) -> List[Passage]:
        """
        Get archival memory from an agent with pagination.

        Args:
            agent_id (str): ID of the agent
            before (str): Get memories before a certain time
            after (str): Get memories after a certain time
            limit (int): Limit number of memories

        Returns:
            passages (List[Passage]): List of passages
        """
        params = {"limit": limit}
        if before:
            params["before"] = str(before)
        if after:
            params["after"] = str(after)
        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents/{str(agent_id)}/archival", params=params,
                                headers=self.headers)
        assert response.status_code == 200, f"Failed to get archival memory: {response.text}"
        return [Passage(**passage) for passage in response.json()]

    def insert_archival_memory(self, agent_id: str, memory: str) -> List[Passage]:
        """
        Insert archival memory into an agent

        Args:
            agent_id (str): ID of the agent
            memory (str): Memory string to insert

        Returns:
            passages (List[Passage]): List of inserted passages
        """
        request = CreateArchivalMemory(text=memory)
        response = requests.post(
            f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/archival", headers=self.headers,
            json=request.model_dump()
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to insert archival memory: {response.text}")
        return [Passage(**passage) for passage in response.json()]

    def delete_archival_memory(self, agent_id: str, memory_id: str):
        """
        Delete archival memory from an agent

        Args:
            agent_id (str): ID of the agent
            memory_id (str): ID of the memory
        """
        response = requests.delete(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/archival/{memory_id}",
                                   headers=self.headers)
        assert response.status_code == 200, f"Failed to delete archival memory: {response.text}"

    # messages (recall memory)

    def get_messages(
            self, agent_id: str, before: Optional[str] = None, after: Optional[str] = None, limit: Optional[int] = 1000
    ) -> List[Message]:
        """
        Get messages from an agent with pagination.

        Args:
            agent_id (str): ID of the agent
            before (str): Get messages before a certain time
            after (str): Get messages after a certain time
            limit (int): Limit number of messages

        Returns:
            messages (List[Message]): List of messages
        """

        params = {"before": before, "after": after, "limit": limit, "msg_object": True}
        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/messages", params=params,
                                headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to get messages: {response.text}")
        return [Message(**message) for message in response.json()]

    def send_message(
            self,
            message: str,
            role: str,
            agent_id: Optional[str] = None,
            name: Optional[str] = None,
            stream: Optional[bool] = False,
            stream_steps: bool = False,
            stream_tokens: bool = False,
    ) -> Union[LettaResponse, Generator[LettaStreamingResponse, None, None]]:
        """
        Send a message to an agent

        Args:
            message (str): Message to send
            role (str): Role of the message
            agent_id (str): ID of the agent
            name(str): Name of the sender
            stream (bool): Stream the response (default: `False`)
            stream_tokens (bool): Stream tokens (default: `False`)

        Returns:
            response (LettaResponse): Response from the agent
        """
        # TODO: implement include_full_message
        messages = [MessageCreate(role=MessageRole(role), text=message, name=name)]
        # TODO: figure out how to handle stream_steps and stream_tokens

        # When streaming steps is True, stream_tokens must be False
        if stream_tokens or stream_steps:
            from letta.client.streaming import _sse_post

            request = LettaStreamingRequest(messages=messages, stream_tokens=stream_tokens)
            return _sse_post(f"{self.base_url}{self.api_prefix}/agents/{agent_id}/messages/stream",
                             request.model_dump(), self.headers)
        else:
            request = LettaRequest(messages=messages)
            response = requests.post(
                f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/messages", json=request.model_dump(),
                headers=self.headers
            )
            if response.status_code != 200:
                raise ValueError(f"Failed to send message: {response.text}")
            response = LettaResponse(**response.json())

            # simplify messages
            # if not include_full_message:
            #     messages = []
            #     for m in response.messages:
            #         assert isinstance(m, Message)
            #         messages += m.to_letta_message()
            #     response.messages = messages

            return response

    def send_message_async(
            self,
            message: str,
            role: str,
            agent_id: Optional[str] = None,
            name: Optional[str] = None,
    ) -> Job:
        """
        Send a message to an agent (async, returns a job)

        Args:
            message (str): Message to send
            role (str): Role of the message
            agent_id (str): ID of the agent
            name(str): Name of the sender

        Returns:
            job (Job): Information about the async job
        """
        messages = [MessageCreate(role=MessageRole(role), text=message, name=name)]

        request = LettaRequest(messages=messages)
        response = requests.post(
            f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/messages/async",
            json=request.model_dump(),
            headers=self.headers,
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to send message: {response.text}")
        response = Job(**response.json())

        return response

    # humans / personas

    def list_blocks(self, label: Optional[str] = None, templates_only: Optional[bool] = True) -> List[Block]:
        params = {"label": label, "templates_only": templates_only}
        response = requests.get(f"{self.base_url}/{self.api_prefix}/blocks", params=params, headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to list blocks: {response.text}")

        if label == "human":
            return [Human(**human) for human in response.json()]
        elif label == "persona":
            return [Persona(**persona) for persona in response.json()]
        else:
            return [Block(**block) for block in response.json()]

    def create_block(
            self, label: str, value: str, limit: Optional[int] = None, template_name: Optional[str] = None,
            is_template: bool = False
    ) -> Block:  #
        request = CreateBlock(label=label, value=value, template=is_template, template_name=template_name)
        if limit:
            request.limit = limit
        response = requests.post(f"{self.base_url}/{self.api_prefix}/blocks", json=request.model_dump(),
                                 headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to create block: {response.text}")
        if request.label == "human":
            return Human(**response.json())
        elif request.label == "persona":
            return Persona(**response.json())
        else:
            return Block(**response.json())

    def update_block(self, block_id: str, name: Optional[str] = None, text: Optional[str] = None,
                     limit: Optional[int] = None) -> Block:
        request = BlockUpdate(id=block_id, template_name=name, value=text,
                              limit=limit if limit else self.get_block(block_id).limit)
        response = requests.post(f"{self.base_url}/{self.api_prefix}/blocks/{block_id}", json=request.model_dump(),
                                 headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to update block: {response.text}")
        return Block(**response.json())

    def get_block(self, block_id: str) -> Block:
        response = requests.get(f"{self.base_url}/{self.api_prefix}/blocks/{block_id}", headers=self.headers)
        if response.status_code == 404:
            return None
        elif response.status_code != 200:
            raise ValueError(f"Failed to get block: {response.text}")
        return Block(**response.json())

    def get_block_id(self, name: str, label: str) -> str:
        params = {"name": name, "label": label}
        response = requests.get(f"{self.base_url}/{self.api_prefix}/blocks", params=params, headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to get block ID: {response.text}")
        blocks = [Block(**block) for block in response.json()]
        if len(blocks) == 0:
            return None
        elif len(blocks) > 1:
            raise ValueError(f"Multiple blocks found with name {name}")
        return blocks[0].id

    def delete_block(self, id: str) -> Block:
        response = requests.delete(f"{self.base_url}/{self.api_prefix}/blocks/{id}", headers=self.headers)
        assert response.status_code == 200, f"Failed to delete block: {response.text}"
        if response.status_code != 200:
            raise ValueError(f"Failed to delete block: {response.text}")
        return Block(**response.json())

    def list_humans(self):
        """
        List available human block templates

        Returns:
            humans (List[Human]): List of human blocks
        """
        blocks = self.list_blocks(label="human")
        return [Human(**block.model_dump()) for block in blocks]

    def create_human(self, name: str, text: str) -> Human:
        """
        Create a human block template (saved human string to pre-fill `ChatMemory`)

        Args:
            name (str): Name of the human block template
            text (str): Text of the human block template

        Returns:
            human (Human): Human block
        """
        return self.create_block(label="human", template_name=name, value=text, is_template=True)

    def update_human(self, human_id: str, name: Optional[str] = None, text: Optional[str] = None) -> Human:
        """
        Update a human block template

        Args:
            human_id (str): ID of the human block
            text (str): Text of the human block

        Returns:
            human (Human): Updated human block
        """
        request = UpdateHuman(id=human_id, template_name=name, value=text)
        response = requests.post(f"{self.base_url}/{self.api_prefix}/blocks/{human_id}", json=request.model_dump(),
                                 headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to update human: {response.text}")
        return Human(**response.json())

    def list_personas(self):
        """
        List available persona block templates

        Returns:
            personas (List[Persona]): List of persona blocks
        """
        blocks = self.list_blocks(label="persona")
        return [Persona(**block.model_dump()) for block in blocks]

    def create_persona(self, name: str, text: str) -> Persona:
        """
        Create a persona block template (saved persona string to pre-fill `ChatMemory`)

        Args:
            name (str): Name of the persona block
            text (str): Text of the persona block

        Returns:
            persona (Persona): Persona block
        """
        return self.create_block(label="persona", template_name=name, value=text, is_template=True)

    def update_persona(self, persona_id: str, name: Optional[str] = None, text: Optional[str] = None) -> Persona:
        """
        Update a persona block template

        Args:
            persona_id (str): ID of the persona block
            text (str): Text of the persona block

        Returns:
            persona (Persona): Updated persona block
        """
        request = UpdatePersona(id=persona_id, template_name=name, value=text)
        response = requests.post(f"{self.base_url}/{self.api_prefix}/blocks/{persona_id}", json=request.model_dump(),
                                 headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to update persona: {response.text}")
        return Persona(**response.json())

    def get_persona(self, persona_id: str) -> Persona:
        """
        Get a persona block template

        Args:
            id (str): ID of the persona block

        Returns:
            persona (Persona): Persona block
        """
        return self.get_block(persona_id)

    def get_persona_id(self, name: str) -> str:
        """
        Get the ID of a persona block template

        Args:
            name (str): Name of the persona block

        Returns:
            id (str): ID of the persona block
        """
        return self.get_block_id(name, "persona")

    def delete_persona(self, persona_id: str) -> Persona:
        """
        Delete a persona block template

        Args:
            id (str): ID of the persona block
        """
        return self.delete_block(persona_id)

    def get_human(self, human_id: str) -> Human:
        """
        Get a human block template

        Args:
            id (str): ID of the human block

        Returns:
            human (Human): Human block
        """
        return self.get_block(human_id)

    def get_human_id(self, name: str) -> str:
        """
        Get the ID of a human block template

        Args:
            name (str): Name of the human block

        Returns:
            id (str): ID of the human block
        """
        return self.get_block_id(name, "human")

    def delete_human(self, human_id: str) -> Human:
        """
        Delete a human block template

        Args:
            id (str): ID of the human block
        """
        return self.delete_block(human_id)

    # sources

    def get_source(self, source_id: str) -> Source:
        """
        Get a source given the ID.

        Args:
            source_id (str): ID of the source

        Returns:
            source (Source): Source
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/sources/{source_id}", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to get source: {response.text}")
        return Source(**response.json())

    def get_source_id(self, source_name: str) -> str:
        """
        Get the ID of a source

        Args:
            source_name (str): Name of the source

        Returns:
            source_id (str): ID of the source
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/sources/name/{source_name}", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to get source ID: {response.text}")
        return response.json()

    def list_sources(self) -> List[Source]:
        """
        List available sources

        Returns:
            sources (List[Source]): List of sources
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/sources", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to list sources: {response.text}")
        return [Source(**source) for source in response.json()]

    def delete_source(self, source_id: str):
        """
        Delete a source

        Args:
            source_id (str): ID of the source
        """
        response = requests.delete(f"{self.base_url}/{self.api_prefix}/sources/{str(source_id)}", headers=self.headers)
        assert response.status_code == 200, f"Failed to delete source: {response.text}"

    def get_job(self, job_id: str) -> Job:
        response = requests.get(f"{self.base_url}/{self.api_prefix}/jobs/{job_id}", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to get job: {response.text}")
        return Job(**response.json())

    def delete_job(self, job_id: str) -> Job:
        response = requests.delete(f"{self.base_url}/{self.api_prefix}/jobs/{job_id}", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to delete job: {response.text}")
        return Job(**response.json())

    def list_jobs(self):
        response = requests.get(f"{self.base_url}/{self.api_prefix}/jobs", headers=self.headers)
        return [Job(**job) for job in response.json()]

    def list_active_jobs(self):
        response = requests.get(f"{self.base_url}/{self.api_prefix}/jobs/active", headers=self.headers)
        return [Job(**job) for job in response.json()]

    def load_data(self, connector: DataConnector, source_name: str):
        raise NotImplementedError

    def load_file_to_source(self, filename: str, source_id: str, blocking=True):
        """
        Load a file into a source

        Args:
            filename (str): Name of the file
            source_id (str): ID of the source
            blocking (bool): Block until the job is complete

        Returns:
            job (Job): Data loading job including job status and metadata
        """
        files = {"file": open(filename, "rb")}

        # create job
        response = requests.post(f"{self.base_url}/{self.api_prefix}/sources/{source_id}/upload", files=files,
                                 headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to upload file to source: {response.text}")

        job = Job(**response.json())
        if blocking:
            # wait until job is completed
            while True:
                job = self.get_job(job.id)
                if job.status == JobStatus.completed:
                    break
                elif job.status == JobStatus.failed:
                    raise ValueError(f"Job failed: {job.metadata}")
                time.sleep(1)
        return job

    def delete_file_from_source(self, source_id: str, file_id: str) -> None:
        response = requests.delete(f"{self.base_url}/{self.api_prefix}/sources/{source_id}/{file_id}",
                                   headers=self.headers)
        if response.status_code not in [200, 204]:
            raise ValueError(f"Failed to delete tool: {response.text}")

    def create_source(self, name: str, embedding_config: Optional[EmbeddingConfig] = None) -> Source:
        """
        Create a source

        Args:
            name (str): Name of the source

        Returns:
            source (Source): Created source
        """
        assert embedding_config or self._default_embedding_config, f"Must specify embedding_config for source"
        source_create = SourceCreate(name=name, embedding_config=embedding_config or self._default_embedding_config)
        payload = source_create.model_dump()
        response = requests.post(f"{self.base_url}/{self.api_prefix}/sources", json=payload, headers=self.headers)
        response_json = response.json()
        return Source(**response_json)

    def list_attached_sources(self, agent_id: str) -> List[Source]:
        """
        List sources attached to an agent

        Args:
            agent_id (str): ID of the agent

        Returns:
            sources (List[Source]): List of sources
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/sources", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to list attached sources: {response.text}")
        return [Source(**source) for source in response.json()]

    def list_files_from_source(self, source_id: str, limit: int = 1000, cursor: Optional[str] = None) -> List[
        FileMetadata]:
        """
        List files from source with pagination support.

        Args:
            source_id (str): ID of the source
            limit (int): Number of files to return
            cursor (Optional[str]): Pagination cursor for fetching the next page

        Returns:
            List[FileMetadata]: List of files
        """
        # Prepare query parameters for pagination
        params = {"limit": limit, "cursor": cursor}

        # Make the request to the FastAPI endpoint
        response = requests.get(f"{self.base_url}/{self.api_prefix}/sources/{source_id}/files", headers=self.headers,
                                params=params)

        if response.status_code != 200:
            raise ValueError(
                f"Failed to list files with source id {source_id}: [{response.status_code}] {response.text}")

        # Parse the JSON response
        return [FileMetadata(**metadata) for metadata in response.json()]

    def update_source(self, source_id: str, name: Optional[str] = None) -> Source:
        """
        Update a source

        Args:
            source_id (str): ID of the source
            name (str): Name of the source

        Returns:
            source (Source): Updated source
        """
        request = SourceUpdate(name=name)
        response = requests.patch(f"{self.base_url}/{self.api_prefix}/sources/{source_id}", json=request.model_dump(),
                                  headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to update source: {response.text}")
        return Source(**response.json())

    def attach_source_to_agent(self, source_id: str, agent_id: str):
        """
        Attach a source to an agent

        Args:
            agent_id (str): ID of the agent
            source_id (str): ID of the source
            source_name (str): Name of the source
        """
        params = {"agent_id": agent_id}
        response = requests.post(f"{self.base_url}/{self.api_prefix}/sources/{source_id}/attach", params=params,
                                 headers=self.headers)
        assert response.status_code == 200, f"Failed to attach source to agent: {response.text}"

    def detach_source(self, source_id: str, agent_id: str):
        """Detach a source from an agent"""
        params = {"agent_id": str(agent_id)}
        response = requests.post(f"{self.base_url}/{self.api_prefix}/sources/{source_id}/detach", params=params,
                                 headers=self.headers)
        assert response.status_code == 200, f"Failed to detach source from agent: {response.text}"
        return Source(**response.json())

    # tools

    def get_tool_id(self, tool_name: str):
        """
        Get the ID of a tool

        Args:
            name (str): Name of the tool

        Returns:
            id (str): ID of the tool (`None` if not found)
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/tools/name/{tool_name}", headers=self.headers)
        if response.status_code == 404:
            return None
        elif response.status_code != 200:
            raise ValueError(f"Failed to get tool: {response.text}")
        return response.json()

    def add_base_tools(self) -> List[Tool]:
        response = requests.post(f"{self.base_url}/{self.api_prefix}/tools/add-base-tools/", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to add base tools: {response.text}")

        return [Tool(**tool) for tool in response.json()]

    def create_tool(
            self,
            func: Callable,
            name: Optional[str] = None,
            tags: Optional[List[str]] = None,
            return_char_limit: int = FUNCTION_RETURN_CHAR_LIMIT,
    ) -> Tool:
        """
        Create a tool. This stores the source code of function on the server, so that the server can execute the function and generate an OpenAI JSON schemas for it when using with an agent.

        Args:
            func (callable): The function to create a tool for.
            name: (str): Name of the tool (must be unique per-user.)
            tags (Optional[List[str]], optional): Tags for the tool. Defaults to None.
            return_char_limit (int): The character limit for the tool's return value. Defaults to FUNCTION_RETURN_CHAR_LIMIT.

        Returns:
            tool (Tool): The created tool.
        """
        source_code = parse_source_code(func)
        source_type = "python"

        # call server function
        request = ToolCreate(source_type=source_type, source_code=source_code, name=name,
                             return_char_limit=return_char_limit)
        if tags:
            request.tags = tags
        response = requests.post(f"{self.base_url}/{self.api_prefix}/tools", json=request.model_dump(),
                                 headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to create tool: {response.text}")
        return Tool(**response.json())

    def create_or_update_tool(
            self,
            func: Callable,
            name: Optional[str] = None,
            tags: Optional[List[str]] = None,
            return_char_limit: int = FUNCTION_RETURN_CHAR_LIMIT,
    ) -> Tool:
        """
        Creates or updates a tool. This stores the source code of function on the server, so that the server can execute the function and generate an OpenAI JSON schemas for it when using with an agent.

        Args:
            func (callable): The function to create a tool for.
            name: (str): Name of the tool (must be unique per-user.)
            tags (Optional[List[str]], optional): Tags for the tool. Defaults to None.
            return_char_limit (int): The character limit for the tool's return value. Defaults to FUNCTION_RETURN_CHAR_LIMIT.

        Returns:
            tool (Tool): The created tool.
        """
        source_code = parse_source_code(func)
        source_type = "python"

        # call server function
        request = ToolCreate(source_type=source_type, source_code=source_code, name=name,
                             return_char_limit=return_char_limit)
        if tags:
            request.tags = tags
        response = requests.put(f"{self.base_url}/{self.api_prefix}/tools", json=request.model_dump(),
                                headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to create tool: {response.text}")
        return Tool(**response.json())

    def update_tool(
            self,
            id: str,
            name: Optional[str] = None,
            description: Optional[str] = None,
            func: Optional[Callable] = None,
            tags: Optional[List[str]] = None,
            return_char_limit: int = FUNCTION_RETURN_CHAR_LIMIT,
    ) -> Tool:
        """
        Update a tool with provided parameters (name, func, tags)

        Args:
            id (str): ID of the tool
            name (str): Name of the tool
            func (callable): Function to wrap in a tool
            tags (List[str]): Tags for the tool
            return_char_limit (int): The character limit for the tool's return value. Defaults to FUNCTION_RETURN_CHAR_LIMIT.

        Returns:
            tool (Tool): Updated tool
        """
        if func:
            source_code = parse_source_code(func)
        else:
            source_code = None

        source_type = "python"

        request = ToolUpdate(
            description=description,
            source_type=source_type,
            source_code=source_code,
            tags=tags,
            name=name,
            return_char_limit=return_char_limit,
        )
        response = requests.patch(f"{self.base_url}/{self.api_prefix}/tools/{id}", json=request.model_dump(),
                                  headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to update tool: {response.text}")
        return Tool(**response.json())

    def list_tools(self, cursor: Optional[str] = None, limit: Optional[int] = 50) -> List[Tool]:
        """
        List available tools for the user.

        Returns:
            tools (List[Tool]): List of tools
        """
        params = {}
        if cursor:
            params["cursor"] = str(cursor)
        if limit:
            params["limit"] = limit

        response = requests.get(f"{self.base_url}/{self.api_prefix}/tools", params=params, headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to list tools: {response.text}")
        return [Tool(**tool) for tool in response.json()]

    def delete_tool(self, name: str):
        """
        Delete a tool given the ID.

        Args:
            id (str): ID of the tool
        """
        response = requests.delete(f"{self.base_url}/{self.api_prefix}/tools/{name}", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to delete tool: {response.text}")

    def get_tool(self, id: str) -> Optional[Tool]:
        """
        Get a tool give its ID.

        Args:
            id (str): ID of the tool

        Returns:
            tool (Tool): Tool
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/tools/{id}", headers=self.headers)
        if response.status_code == 404:
            return None
        elif response.status_code != 200:
            raise ValueError(f"Failed to get tool: {response.text}")
        return Tool(**response.json())

    def get_tool_id(self, name: str) -> Optional[str]:
        """
        Get a tool ID by its name.

        Args:
            id (str): ID of the tool

        Returns:
            tool (Tool): Tool
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/tools/name/{name}", headers=self.headers)
        if response.status_code == 404:
            return None
        elif response.status_code != 200:
            raise ValueError(f"Failed to get tool: {response.text}")
        return response.json()

    def set_default_llm_config(self, llm_config: LLMConfig):
        """
        Set the default LLM configuration

        Args:
            llm_config (LLMConfig): LLM configuration
        """
        self._default_llm_config = llm_config

    def set_default_embedding_config(self, embedding_config: EmbeddingConfig):
        """
        Set the default embedding configuration

        Args:
            embedding_config (EmbeddingConfig): Embedding configuration
        """
        self._default_embedding_config = embedding_config

    def list_llm_configs(self) -> List[LLMConfig]:
        """
        List available LLM configurations

        Returns:
            configs (List[LLMConfig]): List of LLM configurations
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/models", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to list LLM configs: {response.text}")
        return [LLMConfig(**config) for config in response.json()]

    def list_embedding_configs(self) -> List[EmbeddingConfig]:
        """
        List available embedding configurations

        Returns:
            configs (List[EmbeddingConfig]): List of embedding configurations
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/models/embedding", headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to list embedding configs: {response.text}")
        return [EmbeddingConfig(**config) for config in response.json()]

    def list_orgs(self, cursor: Optional[str] = None, limit: Optional[int] = 50) -> List[Organization]:
        """
        Retrieves a list of all organizations in the database, with optional pagination.

        @param cursor: the pagination cursor, if any
        @param limit: the maximum number of organizations to retrieve
        @return: a list of Organization objects
        """
        params = {"cursor": cursor, "limit": limit}
        response = requests.get(f"{self.base_url}/{ADMIN_PREFIX}/orgs", headers=self.headers, params=params)
        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve organizations: {response.text}")
        return [Organization(**org_data) for org_data in response.json()]

    def create_org(self, name: Optional[str] = None) -> Organization:
        """
        Creates an organization with the given name. If not provided, we generate a random one.

        @param name: the name of the organization
        @return: the created Organization
        """
        payload = {"name": name}
        response = requests.post(f"{self.base_url}/{ADMIN_PREFIX}/orgs", headers=self.headers, json=payload)
        if response.status_code != 200:
            raise ValueError(f"Failed to create org: {response.text}")
        return Organization(**response.json())

    def delete_org(self, org_id: str) -> Organization:
        """
        Deletes an organization by its ID.

        @param org_id: the ID of the organization to delete
        @return: the deleted Organization object
        """
        # Define query parameters with org_id
        params = {"org_id": org_id}

        # Make the DELETE request with query parameters
        response = requests.delete(f"{self.base_url}/{ADMIN_PREFIX}/orgs", headers=self.headers, params=params)

        if response.status_code == 404:
            raise ValueError(f"Organization with ID '{org_id}' does not exist")
        elif response.status_code != 200:
            raise ValueError(f"Failed to delete organization: {response.text}")

        # Parse and return the deleted organization
        return Organization(**response.json())

    def create_sandbox_config(self, config: Union[LocalSandboxConfig, E2BSandboxConfig]) -> SandboxConfig:
        """
        Create a new sandbox configuration.
        """
        payload = {
            "config": config.model_dump(),
        }
        response = requests.post(f"{self.base_url}/{self.api_prefix}/sandbox-config", headers=self.headers,
                                 json=payload)
        if response.status_code != 200:
            raise ValueError(f"Failed to create sandbox config: {response.text}")
        return SandboxConfig(**response.json())

    def update_sandbox_config(self, sandbox_config_id: str,
                              config: Union[LocalSandboxConfig, E2BSandboxConfig]) -> SandboxConfig:
        """
        Update an existing sandbox configuration.
        """
        payload = {
            "config": config.model_dump(),
        }
        response = requests.patch(
            f"{self.base_url}/{self.api_prefix}/sandbox-config/{sandbox_config_id}",
            headers=self.headers,
            json=payload,
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to update sandbox config with ID '{sandbox_config_id}': {response.text}")
        return SandboxConfig(**response.json())

    def delete_sandbox_config(self, sandbox_config_id: str) -> None:
        """
        Delete a sandbox configuration.
        """
        response = requests.delete(f"{self.base_url}/{self.api_prefix}/sandbox-config/{sandbox_config_id}",
                                   headers=self.headers)
        if response.status_code == 404:
            raise ValueError(f"Sandbox config with ID '{sandbox_config_id}' does not exist")
        elif response.status_code != 204:
            raise ValueError(f"Failed to delete sandbox config with ID '{sandbox_config_id}': {response.text}")

    def list_sandbox_configs(self, limit: int = 50, cursor: Optional[str] = None) -> List[SandboxConfig]:
        """
        List all sandbox configurations.
        """
        params = {"limit": limit, "cursor": cursor}
        response = requests.get(f"{self.base_url}/{self.api_prefix}/sandbox-config", headers=self.headers,
                                params=params)
        if response.status_code != 200:
            raise ValueError(f"Failed to list sandbox configs: {response.text}")
        return [SandboxConfig(**config_data) for config_data in response.json()]

    def create_sandbox_env_var(
            self, sandbox_config_id: str, key: str, value: str, description: Optional[str] = None
    ) -> SandboxEnvironmentVariable:
        """
        Create a new environment variable for a sandbox configuration.
        """
        payload = {"key": key, "value": value, "description": description}
        response = requests.post(
            f"{self.base_url}/{self.api_prefix}/sandbox-config/{sandbox_config_id}/environment-variable",
            headers=self.headers,
            json=payload,
        )
        if response.status_code != 200:
            raise ValueError(
                f"Failed to create environment variable for sandbox config ID '{sandbox_config_id}': {response.text}")
        return SandboxEnvironmentVariable(**response.json())

    def update_sandbox_env_var(
            self, env_var_id: str, key: Optional[str] = None, value: Optional[str] = None,
            description: Optional[str] = None
    ) -> SandboxEnvironmentVariable:
        """
        Update an existing environment variable.
        """
        payload = {k: v for k, v in {"key": key, "value": value, "description": description}.items() if v is not None}
        response = requests.patch(
            f"{self.base_url}/{self.api_prefix}/sandbox-config/environment-variable/{env_var_id}",
            headers=self.headers,
            json=payload,
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to update environment variable with ID '{env_var_id}': {response.text}")
        return SandboxEnvironmentVariable(**response.json())

    def delete_sandbox_env_var(self, env_var_id: str) -> None:
        """
        Delete an environment variable by its ID.
        """
        response = requests.delete(
            f"{self.base_url}/{self.api_prefix}/sandbox-config/environment-variable/{env_var_id}", headers=self.headers
        )
        if response.status_code == 404:
            raise ValueError(f"Environment variable with ID '{env_var_id}' does not exist")
        elif response.status_code != 204:
            raise ValueError(f"Failed to delete environment variable with ID '{env_var_id}': {response.text}")

    def list_sandbox_env_vars(
            self, sandbox_config_id: str, limit: int = 50, cursor: Optional[str] = None
    ) -> List[SandboxEnvironmentVariable]:
        """
        List all environment variables associated with a sandbox configuration.
        """
        params = {"limit": limit, "cursor": cursor}
        response = requests.get(
            f"{self.base_url}/{self.api_prefix}/sandbox-config/{sandbox_config_id}/environment-variable",
            headers=self.headers,
            params=params,
        )
        if response.status_code != 200:
            raise ValueError(
                f"Failed to list environment variables for sandbox config ID '{sandbox_config_id}': {response.text}")
        return [SandboxEnvironmentVariable(**var_data) for var_data in response.json()]

    def update_agent_memory_block_label(self, agent_id: str, current_label: str, new_label: str) -> Memory:
        """Rename a block in the agent's core memory

        Args:
            agent_id (str): The agent ID
            current_label (str): The current label of the block
            new_label (str): The new label of the block

        Returns:
            memory (Memory): The updated memory
        """
        block = self.get_agent_memory_block(agent_id, current_label)
        return self.update_block(block.id, label=new_label)

    # TODO: remove this
    def add_agent_memory_block(self, agent_id: str, create_block: CreateBlock) -> Memory:
        """
        Create and link a memory block to an agent's core memory

        Args:
            agent_id (str): The agent ID
            create_block (CreateBlock): The block to create

        Returns:
            memory (Memory): The updated memory
        """
        response = requests.post(
            f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/memory/block",
            headers=self.headers,
            json=create_block.model_dump(),
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to add agent memory block: {response.text}")
        return Memory(**response.json())

    def link_agent_memory_block(self, agent_id: str, block_id: str) -> Memory:
        """
        Link a block to an agent's core memory

        Args:
            agent_id (str): The agent ID
            block_id (str): The block ID

        Returns:
            memory (Memory): The updated memory
        """
        params = {"agent_id": agent_id}
        response = requests.patch(
            f"{self.base_url}/{self.api_prefix}/blocks/{block_id}/attach",
            params=params,
            headers=self.headers,
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to link agent memory block: {response.text}")
        return Block(**response.json())

    def remove_agent_memory_block(self, agent_id: str, block_label: str) -> Memory:
        """
        Unlike a block from the agent's core memory

        Args:
            agent_id (str): The agent ID
            block_label (str): The block label

        Returns:
            memory (Memory): The updated memory
        """
        response = requests.delete(
            f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/memory/block/{block_label}",
            headers=self.headers,
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to remove agent memory block: {response.text}")
        return Memory(**response.json())

    def get_agent_memory_blocks(self, agent_id: str) -> List[Block]:
        """
        Get all the blocks in the agent's core memory

        Args:
            agent_id (str): The agent ID

        Returns:
            blocks (List[Block]): The blocks in the agent's core memory
        """
        response = requests.get(f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/memory/block",
                                headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to get agent memory blocks: {response.text}")
        return [Block(**block) for block in response.json()]

    def get_agent_memory_block(self, agent_id: str, label: str) -> Block:
        """
        Get a block in the agent's core memory by its label

        Args:
            agent_id (str): The agent ID
            label (str): The label in the agent's core memory

        Returns:
            block (Block): The block corresponding to the label
        """
        response = requests.get(
            f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/memory/block/{label}",
            headers=self.headers,
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to get agent memory block: {response.text}")
        return Block(**response.json())

    def update_agent_memory_block(
            self,
            agent_id: str,
            label: str,
            value: Optional[str] = None,
            limit: Optional[int] = None,
    ):
        """
        Update a block in the agent's core memory by specifying its label

        Args:
            agent_id (str): The agent ID
            label (str): The label of the block
            value (str): The new value of the block
            limit (int): The new limit of the block

        Returns:
            block (Block): The updated block
        """
        # setup data
        data = {}
        if value:
            data["value"] = value
        if limit:
            data["limit"] = limit
        response = requests.patch(
            f"{self.base_url}/{self.api_prefix}/agents/{agent_id}/memory/block/{label}",
            headers=self.headers,
            json=data,
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to update agent memory block: {response.text}")
        return Block(**response.json())

    def update_block(
            self,
            block_id: str,
            label: Optional[str] = None,
            value: Optional[str] = None,
            limit: Optional[int] = None,
    ):
        """
        Update a block given the ID with the provided fields

        Args:
            block_id (str): ID of the block
            label (str): Label to assign to the block
            value (str): Value to assign to the block
            limit (int): Token limit to assign to the block

        Returns:
            block (Block): Updated block
        """
        data = {}
        if value:
            data["value"] = value
        if limit:
            data["limit"] = limit
        if label:
            data["label"] = label
        response = requests.patch(
            f"{self.base_url}/{self.api_prefix}/blocks/{block_id}",
            headers=self.headers,
            json=data,
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to update block: {response.text}")
        return Block(**response.json())
