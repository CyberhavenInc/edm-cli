from setuptools import setup, find_packages

setup(
    name="edmtool",
    version="0.1",
    packages=find_packages(".", ["./edmtool/tests"]),
    install_requires=['requests>=2.28.0', 'tqdm>=4.66.1', 'spookyhash>=2.1.0', 'requests_toolbelt>=1.0.0'],
    extras_require={
        'dev': [
            'yapf',
            'pre-commit'
        ]
    },
    entry_points={
        'console_scripts': [
            'edmtool=edmtool.__main__:main',
        ],
    },
    author="Konstantin Knyazev",
    author_email="konstantin.knyazev@cyberhaven.com",
    description="A set of CLI tools for EDM DB management",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/CyberhavenInc",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    license="UNLICENSED")
