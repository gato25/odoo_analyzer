from setuptools import setup, find_packages

setup(
    name="odoo_analyzer",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "streamlit==1.32.0",
        "pyvis==0.3.2",
        "networkx==3.2.1",
        "pandas==2.2.1",
        "lxml==5.1.0",
        "plotly==5.18.0",
        "matplotlib==3.8.2",
        "pytest==7.4.3",
        "pydantic==2.5.2",
    ],
    python_requires=">=3.8",
)