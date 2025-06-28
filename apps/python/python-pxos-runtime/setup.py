
from setuptools import setup, find_packages

setup(
    name="pxos",
    version="1.0.0",
    description="PXOS Native Runtime — a reflexive, pixel-native operating substrate",
    author="Your Name",
    packages=find_packages(),
    install_requires=["numpy", "pillow"],
    entry_points={
        "console_scripts": [
            "pxos=cli.pxos:main"
        ]
    },
    include_package_data=True,
    python_requires=">=3.8",
)
