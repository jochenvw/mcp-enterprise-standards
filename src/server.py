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

# Configure logging to ensure consistent format across all components
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
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

@mcp.tool()
async def get_boilerplate_template(
    query: Annotated[str, Field(description="Description of the infrastructure template needed (e.g., 'web application', 'virtual machine', 'kubernetes cluster')")]) -> str:
    """Provides boilerplate Azure Bicep templates based on user query.

    This function scans available templates and uses Azure OpenAI to find the best match
    for the user's infrastructure needs. It returns the complete Bicep template code
    that can be used as a starting point for Azure infrastructure deployment.

    Args:
        query (str): Description of the infrastructure template needed.

    Returns:
        str: The complete Bicep template code for the requested infrastructure.

    Example:
        >>> result = await get_boilerplate_template("I need a web application template")
        >>> print(result)
        "// Azure Web App with App Service Plan..."
    """
    logger.info(f"Processing template request for: {query}")
    
    # Get the templates directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(os.path.dirname(current_dir), 'templates')
    
    # Scan for available templates
    available_templates = []
    template_descriptions = {
        'azure-webapp.bicep': 'Azure Web App with App Service Plan - for hosting web applications, APIs, and websites with scalable hosting environment',
        'azure-vm.bicep': 'Azure Virtual Machine - for creating secure Linux virtual machines with managed disks and network security',
        'azure-aks.bicep': 'Azure Kubernetes Service (AKS) cluster - for container orchestration and microservices deployment with production-ready features'
    }
    
    try:
        if os.path.exists(templates_dir):
            for filename in os.listdir(templates_dir):
                if filename.endswith('.bicep'):
                    available_templates.append(filename)
        
        if not available_templates:
            return "No templates found. Please ensure the templates directory contains .bicep files."
        
        # Check if Azure OpenAI is properly configured
        azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        azure_key = os.getenv('AZURE_OPENAI_API_KEY')
        
        selected_template = None
        
        if azure_endpoint and azure_key and azure_endpoint != 'your_endpoint_here' and azure_key != 'your_api_key_here':
            # Use LLM to find the best matching template
            logger.info("Using Azure OpenAI for template selection")
            kernel = Kernel()
            
            # Create custom HTTP client with SSL verification disabled
            http_client = httpx.AsyncClient(verify=False)
            
            try:
                # Create Azure OpenAI client
                azure_client = AsyncAzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=azure_key,
                    api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
                    azure_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
                    http_client=http_client
                )

                chat_completion = AzureChatCompletion(
                    async_client=azure_client,
                    deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
                )
                kernel.add_service(chat_completion)
                
                # Create prompt to match query to best template
                template_list = "\n".join([f"- {filename}: {template_descriptions.get(filename, 'Azure infrastructure template')}" for filename in available_templates])
                
                system_prompt = f"""You are an Azure infrastructure expert. Based on the user's query, select the MOST APPROPRIATE template from the available options.

Available templates:
{template_list}

Instructions:
1. Analyze the user's query to understand their infrastructure needs
2. Select the single best matching template filename
3. Respond with ONLY the filename (e.g., "azure-webapp.bicep")
4. Do not include any explanation or additional text

User query: {query}"""
                
                chat_history = ChatHistory()
                chat_history.add_system_message(system_prompt)
                chat_history.add_user_message(f"Select the best template for: {query}")

                execution_settings = AzureChatPromptExecutionSettings()
                execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

                result = await chat_completion.get_chat_message_content(
                    chat_history=chat_history,
                    settings=execution_settings,
                    kernel=kernel,
                )
                
                # Extract selected template filename
                selected_template = result.content.strip()
                
                # Validate the selected template exists
                if selected_template not in available_templates:
                    # Fallback to keyword matching if LLM response is invalid
                    logger.warning(f"LLM returned invalid template '{result.content}', using keyword matching fallback")
                    selected_template = None
                
            finally:
                await http_client.aclose()
        
        # Fallback to keyword matching if Azure OpenAI is not configured or failed
        if not selected_template:
            logger.info("Using keyword matching for template selection")
            query_lower = query.lower()
            
            # Simple keyword matching logic
            if any(keyword in query_lower for keyword in ['web', 'webapp', 'app', 'website', 'api', 'http']):
                selected_template = 'azure-webapp.bicep'
            elif any(keyword in query_lower for keyword in ['vm', 'virtual machine', 'server', 'compute', 'linux']):
                selected_template = 'azure-vm.bicep'
            elif any(keyword in query_lower for keyword in ['aks', 'kubernetes', 'k8s', 'container', 'cluster', 'microservice']):
                selected_template = 'azure-aks.bicep'
            else:
                # Default to first available template
                selected_template = available_templates[0]
        
        # Validate the selected template exists
        if selected_template not in available_templates:
            selected_template = available_templates[0]
        
        # Read and return the template content
        template_path = os.path.join(templates_dir, selected_template)
        with open(template_path, 'r') as file:
            template_content = file.read()
        
        logger.info(f"Selected template: {selected_template}")
        return f"Selected template: {selected_template}\n\n{template_content}"
            
    except Exception as e:
        logger.error(f"Error processing template request: {str(e)}")
        return f"Error processing template request: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting MCP Enterprise Standards Server")
    logger.info("Transport: streamable-http for GitHub Copilot integration")
    
    # Configure uvicorn logging format before starting the server
    import uvicorn.config
    
    # Override uvicorn's default logging config to use consistent format
    uvicorn_log_config = uvicorn.config.LOGGING_CONFIG
    uvicorn_log_config["formatters"]["default"]["fmt"] = "%(levelname)s:%(name)s:%(message)s"
    uvicorn_log_config["formatters"]["access"]["fmt"] = "%(levelname)s:%(name)s:%(message)s"
    
    mcp.run(transport="streamable-http")
