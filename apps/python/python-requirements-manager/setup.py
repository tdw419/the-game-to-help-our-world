from setuptools import setup, find_packages

setup(
    name='python-requirements-manager',
    version='2.2',
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'uvicorn',
        'click',
        'rich',
        'pydantic'
    ],
    entry_points={
        'console_scripts': [
            'prm = main:cli'
        ]
    },
)
