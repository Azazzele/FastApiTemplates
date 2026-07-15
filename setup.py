from setuptools import setup, find_packages

setup(
    name="fastapi-endpoint-builder",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn",
        "jinja2",
    ],
    entry_points={
        "console_scripts": [
            "fastapi-builder=fastapi_builder_core.main:start_cli",
        ],
    },
)
