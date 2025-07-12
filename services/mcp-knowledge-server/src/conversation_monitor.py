"""
Conversation Monitor for FindersKeepers v2 MCP Knowledge Server

Monitors conversation messages for exit commands and triggers graceful session termination.
Part of the robust session management system.
"""

import logging
import asyncio
import re
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationMonitor:
    """Monitors conversation messages for exit commands and session management"""
    
    # Exit command patterns
    EXIT_PATTERNS = [
        r'^/exit\s*$',
        r'^/quit\s*$', 
        r'^/bye\s*$',
        r'^exit\s*$',
        r'^\s*exit\s*$',
        r'goodbye.*exit|exit.*goodbye',
        r'end.*session|session.*end',
        r'stop.*session|session.*stop'
    ]
    
    def __init__(self, activity_logger, exit_callback: Optional[Callable] = None):
        self.activity_logger = activity_logger
        self.exit_callback = exit_callback
        self.monitoring = False
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.EXIT_PATTERNS]
        
    def start_monitoring(self):
        """Start conversation monitoring"""
        self.monitoring = True
        logger.info("👁️ Conversation monitoring started - watching for exit commands")
        
    def stop_monitoring(self):
        """Stop conversation monitoring"""
        self.monitoring = False
        logger.info("👁️ Conversation monitoring stopped")
        
    async def process_message(self, message: str, message_type: str = "user_message") -> bool:
        """
        Process a conversation message and check for exit commands
        
        Args:
            message: The message content to analyze
            message_type: Type of message (user_message, ai_response, etc.)
            
        Returns:
            bool: True if exit command was detected and processed
        """
        if not self.monitoring:
            return False
            
        try:
            # Only check user messages for exit commands
            if message_type != "user_message":
                return False
                
            # Clean and normalize the message
            cleaned_message = message.strip().lower()
            
            # Check against all exit patterns
            for pattern in self.patterns:
                if pattern.search(cleaned_message):
                    logger.info(f"🚪 Exit command detected: '{message.strip()}'")
                    
                    # Log the exit detection
                    if self.activity_logger.initialized:
                        await self.activity_logger.log_action(
                            action_type="user_exit_command",
                            description="User requested session termination",
                            details={
                                "exit_message": message.strip(),
                                "detection_time": datetime.utcnow().isoformat(),
                                "pattern_matched": pattern.pattern
                            }
                        )
                    
                    # Trigger graceful shutdown
                    await self._handle_exit_command(message.strip())
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error processing message for exit detection: {e}")
            return False
            
    async def _handle_exit_command(self, original_message: str):
        """Handle detected exit command with graceful shutdown"""
        try:
            logger.info("🚪 Initiating graceful session termination due to user exit command")
            
            # Call custom exit callback if provided
            if self.exit_callback:
                await self.exit_callback()
                
            # Trigger graceful shutdown through activity logger
            if self.activity_logger.initialized:
                await self.activity_logger.shutdown("user_exit")
                
            # Stop monitoring
            self.stop_monitoring()
            
            logger.info("✅ Graceful session termination completed")
            
        except Exception as e:
            logger.error(f"Error during exit command handling: {e}")


class MessageBuffer:
    """Buffer recent conversation messages for context and analysis"""
    
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.messages = []
        
    def add_message(self, message: str, message_type: str, timestamp: Optional[datetime] = None):
        """Add a message to the buffer"""
        if timestamp is None:
            timestamp = datetime.utcnow()
            
        message_entry = {
            "content": message,
            "type": message_type,
            "timestamp": timestamp,
        }
        
        self.messages.append(message_entry)
        
        # Maintain buffer size
        if len(self.messages) > self.max_size:
            self.messages = self.messages[-self.max_size:]
            
    def get_recent_messages(self, count: int = 10) -> list:
        """Get the most recent messages"""
        return self.messages[-count:] if count <= len(self.messages) else self.messages
        
    def search_messages(self, pattern: str, message_type: Optional[str] = None) -> list:
        """Search messages for a pattern"""
        regex = re.compile(pattern, re.IGNORECASE)
        matches = []
        
        for msg in self.messages:
            if message_type and msg["type"] != message_type:
                continue
                
            if regex.search(msg["content"]):
                matches.append(msg)
                
        return matches
        
    def clear(self):
        """Clear all messages from buffer"""
        self.messages = []


# Integration helper function
async def setup_conversation_monitoring(activity_logger, custom_exit_callback=None):
    """
    Set up conversation monitoring with the activity logger
    
    Args:
        activity_logger: ActivityLogger instance
        custom_exit_callback: Optional custom callback for exit handling
        
    Returns:
        ConversationMonitor: Configured monitor instance
    """
    monitor = ConversationMonitor(
        activity_logger=activity_logger,
        exit_callback=custom_exit_callback
    )
    
    monitor.start_monitoring()
    
    logger.info("🔧 Conversation monitoring setup complete")
    return monitor