import openai
from typing import Dict, List, Optional

class AIChatService:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI chat service"""
        self.api_key = api_key
        if api_key:
            openai.api_key = api_key

    def get_response(self, message: str, context: Optional[List[Dict]] = None) -> str:
        """Get AI response for user message"""
        try:
            # For demo, return predefined responses
            if "product" in message.lower():
                return "I can help you with product management. Would you like to add, edit, or view products?"
            elif "sync" in message.lower():
                return "I can help you with synchronization settings. Would you like to configure platform connections or schedule syncs?"
            elif "import" in message.lower() or "export" in message.lower():
                return "I can help you with data import/export. Would you like to import new products or export your catalog?"
            elif "price" in message.lower():
                return "I can help you with price management. Would you like to update prices or set up pricing rules?"
            elif "stock" in message.lower() or "inventory" in message.lower():
                return "I can help you with stock management. Would you like to update stock levels or set up stock alerts?"
            elif "help" in message.lower():
                return "I'm your AI assistant. I can help you with:\n- Product management\n- Synchronization\n- Import/Export\n- Price management\n- Stock management\nWhat would you like help with?"
            else:
                return "I'm here to help! I can assist you with product management, synchronization, import/export, pricing, and stock management. What would you like to know?"

        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"
