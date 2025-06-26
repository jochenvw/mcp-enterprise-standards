from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Annotated
import os
from dotenv import load_dotenv
import logging
import httpx

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory
from openai.lib.azure import AsyncAzureOpenAI

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(name="enterprise-standards", description="Assesses Azure infrastructure code against enterprise standards.")

# Load environment variables from .env file
load_dotenv()
logger.info("Environment variables loaded from .env file")

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
    logger.info("Starting enterprise standards assessment")
    logger.info(f"Code length: {len(code)} characters")
    kernel = Kernel()

    # Create custom HTTP client with SSL verification disabled
    # This is required for enterprise environments with SSL inspection
    logger.info("Creating HTTP client with SSL verification disabled for enterprise compatibility")
    http_client = httpx.AsyncClient(verify=False)
    
    try:
        # Create Azure OpenAI client with SSL verification disabled
        logger.info("Initializing Azure OpenAI client connection")
        azure_client = AsyncAzureOpenAI(
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            azure_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
            http_client=http_client
        )

        logger.info("Setting up Semantic Kernel chat completion service")
        chat_completion = AzureChatCompletion(
            async_client=azure_client,
            deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        )
        kernel.add_service(chat_completion)

        # Read the system prompt from the file system_prompt - relative to the current file
        logger.info("Loading enterprise standards prompts and templates")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_files = {
            'system_prompt': 'system_prompt.md',
            'naming_convention': 'naming_convention.md',
            'shared_resources': 'shared_resources.md',
            'security_standards': 'security_standards.md'
        }
        
        prompts = {}
        for key, filename in prompt_files.items():
            logger.info(f"Reading {filename} for enterprise standards validation")
            with open(os.path.join(current_dir, filename), "r") as file:
                prompts[key] = file.read()
        
        logger.info("Constructing system prompt with enterprise standards")
        system_prompt = prompts['system_prompt'].format(
            naming_convention=prompts['naming_convention'],
            shared_resources=prompts['shared_resources'],
            security_standards=prompts['security_standards']
        )
        
        logger.info("Preparing chat conversation with enterprise context")
        chat_history = ChatHistory()
        chat_history.add_system_message(system_prompt)
        chat_history.add_user_message(code)

        logger.info("Configuring execution settings for AI assessment")
        execution_settings = AzureChatPromptExecutionSettings()
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        logger.info("Sending code to AI for enterprise standards analysis")
        result = await chat_completion.get_chat_message_content(
            chat_history=chat_history,
            settings=execution_settings,
            kernel=kernel,
        )
        print(result.content)
        logger.info("Enterprise standards assessment completed successfully")
        return result.content
    except Exception as e:
        logger.error(f"Assessment failed: {str(e)}")
        raise
    finally:
        # Ensure HTTP client is closed properly
        logger.info("Cleaning up HTTP client connection")
        await http_client.aclose()

if __name__ == "__main__":
    logger.info("Starting MCP Enterprise Standards Server")
    logger.info("Transport: streamable-http for GitHub Copilot integration")
    mcp.run(transport="streamable-http")
