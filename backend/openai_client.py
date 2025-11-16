"""
OpenAI Client for handling chat completions
Manages conversation history and LLM interactions
"""
import logging
import uuid
from typing import Dict, List, Optional
from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Handles interactions with OpenAI API"""

    def __init__(self):
        """Initialize OpenAI client"""
        logger.info("Initializing OpenAI Client...")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

        # Store conversation history in memory
        # In production, use Redis or a database
        self.conversation_history: Dict[str, List[Dict]] = {}

        logger.info("OpenAI Client initialized successfully")

    async def generate_response(
        self,
        user_message: str,
        context: str = "",
        conversation_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Generate a response using OpenAI API

        Args:
            user_message: User's message
            context: Retrieved context from RAG
            conversation_id: Optional conversation ID to maintain history

        Returns:
            Dictionary with response and conversation_id
        """
        try:
            # Create or retrieve conversation
            if conversation_id is None:
                conversation_id = str(uuid.uuid4())
                self.conversation_history[conversation_id] = []

            # Build system prompt
            system_prompt = self._build_system_prompt(context)

            # Get conversation history
            messages = self._get_conversation_messages(
                conversation_id, system_prompt, user_message
            )

            logger.info(f"Generating response for conversation {conversation_id}")

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens
            )

            # Extract response
            ai_message = response.choices[0].message.content

            # Update conversation history
            self._update_conversation_history(
                conversation_id, user_message, ai_message
            )

            logger.info("Response generated successfully")

            return {
                "response": ai_message,
                "conversation_id": conversation_id,
                "model": settings.openai_model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    def _build_system_prompt(self, context: str) -> str:
        """
        Build system prompt with optional context

        Args:
            context: Retrieved context from RAG

        Returns:
            System prompt string
        """
        base_prompt = """You are a helpful AI assistant for BNP. You provide accurate,
professional, and friendly responses to user queries."""

        if context:
            base_prompt += f"""

You have access to the following relevant information to help answer the user's question:

{context}

Use this information to provide accurate and contextual responses. If the information
provided is not relevant to the question, rely on your general knowledge. Always cite
sources when using the provided information."""

        return base_prompt

    def _get_conversation_messages(
        self, conversation_id: str, system_prompt: str, user_message: str
    ) -> List[Dict]:
        """
        Get formatted messages for OpenAI API

        Args:
            conversation_id: Conversation identifier
            system_prompt: System prompt
            user_message: Current user message

        Returns:
            List of message dictionaries
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history
        if conversation_id in self.conversation_history:
            messages.extend(self.conversation_history[conversation_id])

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _update_conversation_history(
        self, conversation_id: str, user_message: str, ai_message: str
    ):
        """
        Update conversation history

        Args:
            conversation_id: Conversation identifier
            user_message: User's message
            ai_message: AI's response
        """
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []

        # Add messages to history
        self.conversation_history[conversation_id].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_message}
        ])

        # Limit conversation history to last 10 exchanges (20 messages)
        # to avoid token limits
        max_messages = 20
        if len(self.conversation_history[conversation_id]) > max_messages:
            self.conversation_history[conversation_id] = \
                self.conversation_history[conversation_id][-max_messages:]

        logger.info(
            f"Conversation {conversation_id} updated. "
            f"History length: {len(self.conversation_history[conversation_id])}"
        )

    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear a conversation history

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if cleared successfully
        """
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
            logger.info(f"Conversation {conversation_id} cleared")
            return True
        return False

    def get_active_conversations(self) -> int:
        """Get number of active conversations"""
        return len(self.conversation_history)
