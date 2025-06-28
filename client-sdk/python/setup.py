"""
Setup script for Bot Detection Python Client SDK.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bot-detection-client",
    version="1.0.0",
    author="Bot Detection Team",
    author_email="support@botdetection.com",
    description="Python client SDK for Bot Detection API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/botdetection/bot-detection-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "typing-extensions>=3.7.4",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
        ],
        "selenium": [
            "selenium>=4.0.0",
        ],
        "playwright": [
            "playwright>=1.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bot-detection=bot_detection_client.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 