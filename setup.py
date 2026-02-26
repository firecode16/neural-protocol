from setuptools import setup, find_packages

setup(
    name="neural-protocol",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[],  # solo stdlib
    python_requires=">=3.9",
    author="NeuralProtocol Team",
    description="Protocolo binario de comunicación entre agentes de IA",
    license="MIT",
)