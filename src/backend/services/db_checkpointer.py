"""
PostgreSQL-backed Checkpointer for LangGraph

This module provides a custom checkpointer that stores LangGraph state
in PostgreSQL instead of in-memory, enabling persistent chat history.
"""

import json
import logging
from typing import Optional, Any, Iterator
from datetime import datetime
from contextlib import contextmanager

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.base import SessionLocal
from db.models import Conversation, Checkpoint as CheckpointModel

logger = logging.getLogger(__name__)


class PostgresCheckpointer(BaseCheckpointSaver):
    """
    PostgreSQL-backed checkpointer for LangGraph.
    
    Stores conversation state in PostgreSQL for persistence across restarts.
    """

    def __init__(self):
        """Initialize the PostgreSQL checkpointer"""
        super().__init__()
        logger.info("✅ PostgresCheckpointer initialized")

    @contextmanager
    def _get_session(self) -> Iterator[Session]:
        """Get a database session with automatic cleanup"""
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error in checkpointer: {e}")
            raise
        finally:
            session.close()

    def _ensure_conversation_exists(self, session: Session, thread_id: str) -> None:
        """Ensure a conversation record exists for the thread"""
        conversation = session.execute(
            select(Conversation).where(Conversation.thread_id == thread_id)
        ).scalar_one_or_none()

        if not conversation:
            conversation = Conversation(thread_id=thread_id)
            session.add(conversation)
            session.flush()
            logger.info(f"📝 Created new conversation: {thread_id}")

    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> dict:
        """
        Save a checkpoint to the database.

        Args:
            config: Configuration dict with thread_id
            checkpoint: The checkpoint to save
            metadata: Checkpoint metadata

        Returns:
            Updated config dict
        """
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        
        try:
            with self._get_session() as session:
                # Ensure conversation exists
                self._ensure_conversation_exists(session, thread_id)

                # Serialize checkpoint data
                checkpoint_data = json.dumps({
                    "v": checkpoint.get("v", 1),
                    "ts": checkpoint.get("ts"),
                    "id": checkpoint.get("id"),
                    "channel_values": self._serialize_channel_values(checkpoint.get("channel_values", {})),
                    "channel_versions": checkpoint.get("channel_versions", {}),
                    "versions_seen": checkpoint.get("versions_seen", {}),
                })

                # Serialize metadata
                metadata_json = json.dumps({
                    "source": metadata.get("source", "input"),
                    "step": metadata.get("step", -1),
                    "writes": metadata.get("writes"),
                })

                # Create checkpoint record
                checkpoint_record = CheckpointModel(
                    thread_id=thread_id,
                    checkpoint_id=checkpoint.get("id", ""),
                    parent_checkpoint_id=checkpoint.get("parent_id"),
                    checkpoint_data=checkpoint_data,
                    checkpoint_metadata=metadata_json,
                )

                session.add(checkpoint_record)
                session.flush()

                logger.info(f"💾 Saved checkpoint for thread: {thread_id}")

        except Exception as e:
            logger.error(f"❌ Error saving checkpoint: {e}")
            raise

        return config

    def get(self, config: dict) -> Optional[Checkpoint]:
        """
        Retrieve the latest checkpoint for a thread.

        Args:
            config: Configuration dict with thread_id

        Returns:
            The latest checkpoint or None
        """
        thread_id = config.get("configurable", {}).get("thread_id", "default")

        try:
            with self._get_session() as session:
                # Get the latest checkpoint for this thread
                checkpoint_record = session.execute(
                    select(CheckpointModel)
                    .where(CheckpointModel.thread_id == thread_id)
                    .order_by(CheckpointModel.created_at.desc())
                    .limit(1)
                ).scalar_one_or_none()

                if not checkpoint_record:
                    logger.info(f"📭 No checkpoint found for thread: {thread_id}")
                    return None

                # Deserialize checkpoint data
                checkpoint_data = json.loads(checkpoint_record.checkpoint_data)
                
                checkpoint = {
                    "v": checkpoint_data.get("v", 1),
                    "ts": checkpoint_data.get("ts"),
                    "id": checkpoint_data.get("id"),
                    "channel_values": self._deserialize_channel_values(checkpoint_data.get("channel_values", {})),
                    "channel_versions": checkpoint_data.get("channel_versions", {}),
                    "versions_seen": checkpoint_data.get("versions_seen", {}),
                }

                logger.info(f"📬 Retrieved checkpoint for thread: {thread_id}")
                return checkpoint

        except Exception as e:
            logger.error(f"❌ Error retrieving checkpoint: {e}")
            return None

    def get_tuple(self, config: dict):
        """
        Get checkpoint tuple (config, checkpoint, metadata, parent_config, pending_writes).
        Sync version required by LangGraph.
        Returns a CheckpointTuple named tuple.
        """
        checkpoint = self.get(config)
        if checkpoint is None:
            return None
        
        # Create metadata dict
        metadata = {
            "source": "input",
            "step": -1,
            "writes": None,
        }
        parent_config = None
        pending_writes = []
        
        # Return CheckpointTuple named tuple
        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=parent_config,
            pending_writes=pending_writes
        )

    async def aget(self, config: dict) -> Optional[Checkpoint]:
        """Async version of get - delegates to sync version"""
        return self.get(config)
    
    async def aget_tuple(self, config: dict):
        """
        Get checkpoint tuple (config, checkpoint, metadata, parent_config, pending_writes).
        Required by LangGraph's async workflow.
        Returns a CheckpointTuple named tuple.
        """
        checkpoint = self.get(config)
        if checkpoint is None:
            return None
        
        # Create metadata dict
        metadata = {
            "source": "input",
            "step": -1,
            "writes": None,
        }
        parent_config = None
        pending_writes = []
        
        # Return CheckpointTuple named tuple
        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=parent_config,
            pending_writes=pending_writes
        )

    async def aput(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict = None,
    ) -> dict:
        """Async version of put - delegates to sync version"""
        # new_versions parameter is used by LangGraph but we don't need it for basic storage
        return self.put(config, checkpoint, metadata)

    async def alist(self, config: dict) -> list[Checkpoint]:
        """Async version of list - delegates to sync version"""
        return self.list(config)
    
    async def aput_writes(self, config: dict, writes: list, task_id: str):
        """
        Store intermediate writes from a task.
        This is called by LangGraph to save intermediate state.
        For now, we'll implement a no-op as we're storing full checkpoints.
        """
        # For basic implementation, we don't need to store individual writes
        # The full checkpoint is stored via aput()
        pass

    def list(self, config: dict) -> list[Checkpoint]:
        """
        List all checkpoints for a thread.

        Args:
            config: Configuration dict with thread_id

        Returns:
            List of checkpoints
        """
        thread_id = config.get("configurable", {}).get("thread_id", "default")

        try:
            with self._get_session() as session:
                checkpoint_records = session.execute(
                    select(CheckpointModel)
                    .where(CheckpointModel.thread_id == thread_id)
                    .order_by(CheckpointModel.created_at.desc())
                ).scalars().all()

                checkpoints = []
                for record in checkpoint_records:
                    checkpoint_data = json.loads(record.checkpoint_data)
                    checkpoint = {
                        "v": checkpoint_data.get("v", 1),
                        "ts": checkpoint_data.get("ts"),
                        "id": checkpoint_data.get("id"),
                        "channel_values": self._deserialize_channel_values(checkpoint_data.get("channel_values", {})),
                        "channel_versions": checkpoint_data.get("channel_versions", {}),
                        "versions_seen": checkpoint_data.get("versions_seen", {}),
                    }
                    checkpoints.append(checkpoint)

                logger.info(f"📋 Listed {len(checkpoints)} checkpoints for thread: {thread_id}")
                return checkpoints

        except Exception as e:
            logger.error(f"❌ Error listing checkpoints: {e}")
            return []

    def _serialize_channel_values(self, channel_values: dict) -> dict:
        """
        Serialize channel values for storage.
        
        Handles special types like LangChain messages.
        """
        serialized = {}
        for key, value in channel_values.items():
            if key == "messages" and isinstance(value, list):
                # Serialize LangChain messages
                serialized[key] = [
                    {
                        "type": msg.type if hasattr(msg, "type") else "unknown",
                        "content": msg.content if hasattr(msg, "content") else str(msg),
                        "additional_kwargs": getattr(msg, "additional_kwargs", {}),
                        "tool_calls": getattr(msg, "tool_calls", []),
                    }
                    for msg in value
                ]
            else:
                # For other values, try to serialize as-is
                try:
                    json.dumps(value)  # Test if serializable
                    serialized[key] = value
                except (TypeError, ValueError):
                    # If not serializable, convert to string
                    serialized[key] = str(value)
        
        return serialized

    def _deserialize_channel_values(self, channel_values: dict) -> dict:
        """
        Deserialize channel values from storage.
        
        Reconstructs LangChain messages and other special types.
        """
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

        deserialized = {}
        for key, value in channel_values.items():
            if key == "messages" and isinstance(value, list):
                # Reconstruct LangChain messages
                messages = []
                for msg_data in value:
                    msg_type = msg_data.get("type", "unknown")
                    content = msg_data.get("content", "")
                    
                    if msg_type == "human":
                        messages.append(HumanMessage(content=content))
                    elif msg_type == "ai":
                        msg = AIMessage(content=content)
                        msg.additional_kwargs = msg_data.get("additional_kwargs", {})
                        msg.tool_calls = msg_data.get("tool_calls", [])
                        messages.append(msg)
                    elif msg_type == "system":
                        messages.append(SystemMessage(content=content))
                    elif msg_type == "tool":
                        messages.append(ToolMessage(content=content, tool_call_id=msg_data.get("tool_call_id", "")))
                    else:
                        # Fallback to HumanMessage
                        messages.append(HumanMessage(content=content))
                
                deserialized[key] = messages
            else:
                deserialized[key] = value
        
        return deserialized

