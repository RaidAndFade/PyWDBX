import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='PyWDBX',  
    version='0.0.1',
    author="raidandfade",
    author_email="business@gocode.it",
    description="Pure Python WDBX reader",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/raidandfade/pywdbx",
    packages=["PyWDBX","PyWDBX.types","PyWDBX.utils"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
    ]
 )