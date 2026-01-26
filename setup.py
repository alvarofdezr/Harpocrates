from setuptools import setup, find_packages

setup(
    name="harpocrates-vault",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "cryptography",
        "argon2-cffi",
        "python-dotenv",
        "pyperclip"
    ],
    entry_points={
        'console_scripts': [
            'harpocrates=main:main',
        ],
    },
    author="alvarofdezr",
    description="A Zero-Knowledge high-security password manager",
)