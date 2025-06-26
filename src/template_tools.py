from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Annotated
import os
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

logger = logging.getLogger(__name__)

# This function can be imported and registered as a tool in your main server file
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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(os.path.dirname(current_dir), 'templates')
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
        azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        azure_key = os.getenv('AZURE_OPENAI_API_KEY')
        selected_template = None
        if azure_endpoint and azure_key and azure_endpoint != 'your_endpoint_here' and azure_key != 'your_api_key_here':
            logger.info("Using Azure OpenAI for template selection")
            kernel = Kernel()
            http_client = httpx.AsyncClient(verify=False)
            try:
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
                template_list = "\n".join([f"- {filename}: {template_descriptions.get(filename, 'Azure infrastructure template')}" for filename in available_templates])
                system_prompt = f"""You are an Azure infrastructure expert. Based on the user's query, select the MOST APPROPRIATE template from the available options.\n\nAvailable templates:\n{template_list}\n\nInstructions:\n1. Analyze the user's query to understand their infrastructure needs\n2. Select the single best matching template filename\n3. Respond with ONLY the filename (e.g., \"azure-webapp.bicep\")\n4. Do not include any explanation or additional text\n\nUser query: {query}"""
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
                selected_template = result.content.strip()
                if selected_template not in available_templates:
                    logger.warning(f"LLM returned invalid template '{result.content}', using keyword matching fallback")
                    selected_template = None
            finally:
                await http_client.aclose()
        if not selected_template:
            logger.info("Using keyword matching for template selection")
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in ['web', 'webapp', 'app', 'website', 'api', 'http']):
                selected_template = 'azure-webapp.bicep'
            elif any(keyword in query_lower for keyword in ['vm', 'virtual machine', 'server', 'compute', 'linux']):
                selected_template = 'azure-vm.bicep'
            elif any(keyword in query_lower for keyword in ['aks', 'kubernetes', 'k8s', 'container', 'cluster', 'microservice']):
                selected_template = 'azure-aks.bicep'
            else:
                selected_template = available_templates[0]
        if selected_template not in available_templates:
            selected_template = available_templates[0]
        template_path = os.path.join(templates_dir, selected_template)
        with open(template_path, 'r') as file:
            template_content = file.read()
        logger.info(f"Selected template: {selected_template}")
        return f"Selected template: {selected_template}\n\n{template_content}"
    except Exception as e:
        logger.error(f"Error processing template request: {str(e)}")
        return f"Error processing template request: {str(e)}"
