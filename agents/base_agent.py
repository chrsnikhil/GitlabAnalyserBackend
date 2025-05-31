from abc import ABC, abstractmethod
from typing import Any, Dict, List
import os
from dotenv import load_dotenv
import openai
import asyncio
from datetime import datetime, timedelta

# Load environment variables if not already loaded
load_dotenv()

# Configure Gemini API (moved from main.py to base_agent)
# We'll configure it here to ensure agents can use it directly if needed
# However, we'll primarily use it via the _call_gemini method

class BaseAgent(ABC):
    def __init__(self):
        """Initialize the base agent with common utilities."""
        # self.api_key = os.getenv("GOOGLE_API_KEY")
        # if not self.api_key:
             # This check is also in main.py, but good to have here too
            # print("Warning: GOOGLE_API_KEY environment variable is not set.")
            # We won't raise an error here to allow non-AI agents to initialize

        # No direct model initialization here, use _call_gemini which handles it.
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Default to 3.5-turbo
        if not self.openai_api_key:
            print("Warning: OPENAI_API_KEY environment variable is not set.")
        # Set OpenAI API key globally for the SDK
        openai.api_key = self.openai_api_key
        
        # Rate limiting setup
        self.last_request_time = datetime.now()
        self.min_request_interval = 1.0  # Minimum seconds between requests
        self.request_queue = asyncio.Queue()
        self.processing = False

    def _format_error(self, error: Exception) -> Dict[str, Any]:
        """Format error response"""
        print(f"Agent Error: {error}") # Log the error server-side
        return {
            "status": "error",
            "message": str(error),
            "data": None
        }
    
    def _format_success(self, message: str, data: Any) -> Dict[str, Any]:
        """Format success response"""
        return {
            "status": "success",
            "message": message,
            "data": data,
        }
    
    def _get_template(self, template_name: str) -> str:
        """Get a template by name"""
        try:
            # Assumes templates are in a 'templates' subdirectory within the agent's directory
            # This path logic might need adjustment based on actual project structure
            template_path = os.path.join(
                os.path.dirname(__file__),
                "templates",
                f"{template_name}.yaml",
            )
            with open(template_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Template not found: {template_path}")
        except Exception as e:
            raise Exception(f"Error reading template {template_name}: {e}")
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main logic
        
        Args:
            context: Dictionary containing the context and input data
            
        Returns:
            Dictionary containing the results of the agent's execution
        """
        pass 

    async def _process_queue(self):
        """Process queued requests with rate limiting"""
        while True:
            if not self.request_queue.empty():
                future, prompt, system_prompt = await self.request_queue.get()
                try:
                    # Ensure minimum time between requests
                    now = datetime.now()
                    time_since_last = (now - self.last_request_time).total_seconds()
                    if time_since_last < self.min_request_interval:
                        await asyncio.sleep(self.min_request_interval - time_since_last)
                    
                    result = await self._make_openai_request(prompt, system_prompt)
                    future.set_result(result)
                    self.last_request_time = datetime.now()
                except Exception as e:
                    future.set_exception(e)
                finally:
                    self.request_queue.task_done()
            await asyncio.sleep(0.1)

    async def _make_openai_request(self, prompt: str, system_prompt: str = None) -> str:
        """Make the actual OpenAI API request"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: openai.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                max_tokens=1024,  # Reduced from 2048
                temperature=0.2,
            )
        )
        return response.choices[0].message.content.strip()

    async def _call_openai(self, prompt: str, system_prompt: str = None) -> str:
        """Call OpenAI's chat completion API with rate limiting"""
        if not hasattr(self, '_queue_processor'):
            self._queue_processor = asyncio.create_task(self._process_queue())
        
        future = asyncio.Future()
        await self.request_queue.put((future, prompt, system_prompt))
        return await future 