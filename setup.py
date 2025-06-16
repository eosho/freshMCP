from setuptools import setup, find_namespace_packages

setup(
    name="FreshMCP",
    version="0.1.0",
    packages=find_namespace_packages(include=["mcp*"]),
    package_dir={"mcp": "mcp"},
    install_requires=[
        "fastapi==0.115.12",
        "uvicorn==0.34.0",
        "python-dotenv==1.1.0",
        "mcp==1.9.0",
        "azure.identity==1.21.0",
        "sse-starlette==2.2.1",
        "starlette==0.46.0",
        "azure-cosmos==4.9.0",
    ],
    python_requires=">=3.11",
)