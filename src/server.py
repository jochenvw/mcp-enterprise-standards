from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Annotated
import os
from dotenv import load_dotenv
import logging

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(name="enterprise-standards", description="Assesses Azure infrastructure code against enterprise standards.")

# Load environment variables from .env file
load_dotenv()

@mcp.tool()
async def assess_code_for_enterprise_standards(
    code: Annotated[str, Field(description="Infrastructure code to be assessed against enterprise standards.")]) -> str:
    """Assesses code against enterprise standards using Azure OpenAI.

    This function takes a code snippet and evaluates it against enterprise coding standards
    using Azure OpenAI's GPT-4.5 model. It uses a system prompt from system_prompt.md to
    guide the assessment.

    Args:
        code (str): The code snippet to be assessed against enterprise standards.

    Returns:
        str: A detailed assessment of the code against enterprise standards, including
             recommendations for improvement if needed.

    Example:
        >>> result = await assess_code_for_enterprise_standards("def hello(): print('world')")
        >>> print(result)
        "Assessment of code against enterprise standards..."
    """
    logger.info("Starting code assessment")
    kernel = Kernel()

    chat_completion = AzureChatCompletion(
        deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
        endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
    )
    kernel.add_service(chat_completion)

    # Read the system prompt from the file system_prompt - relative to the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_files = {
        'system_prompt': 'system_prompt.md',
        'naming_convention': 'naming_convention.md',
        'shared_resources': 'shared_resources.md',
        'security_standards': 'security_standards.md'
    }
    
    prompts = {}
    for key, filename in prompt_files.items():
        with open(os.path.join(current_dir, filename), "r") as file:
            prompts[key] = file.read()
    
    system_prompt = prompts['system_prompt'].format(
        naming_convention=prompts['naming_convention'],
        shared_resources=prompts['shared_resources'],
        security_standards=prompts['security_standards']
    )
    
    chat_history = ChatHistory()
    chat_history.add_system_message(system_prompt)
    chat_history.add_user_message(code)

    execution_settings = AzureChatPromptExecutionSettings()
    execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    result = await chat_completion.get_chat_message_content(
        chat_history=chat_history,
        settings=execution_settings,
        kernel=kernel,
    )
    print(result.content)
    logger.info("Assessment completed")
    return result.content

if __name__ == "__main__":
    logger.info("Starting server...")
    mcp.run(transport="streamable-http")
