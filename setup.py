from setuptools import setup, find_packages

setup(
    name="harpocrates-vault",
    version="1.5.1",
    packages=find_packages(),
    install_requires=[
        "cryptography",
        "argon2-cffi",
        "pyperclip",
        "colorama"
    ],
    entry_points={
        'console_scripts': [
            'harpocrates=main:main',
        ],
    },
    author="alvarofdezr",
    description="A Zero-Knowledge high-security password manager",
)