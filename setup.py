from setuptools import setup, find_packages

setup(
    name="arrow",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'arrow=arrow:main',
        ],
    },
    python_requires='>=3.6',
    author="Arrow Developer",
    description="Arrow programming language interpreter",
)
