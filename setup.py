from setuptools import setup, find_packages

setup(
    name="cloud_llm",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flet>=0.21.0",
        "sentence-transformers>=2.2.2",
        "torch>=2.0.0",
        "numpy>=1.24.0",
        "sounddevice>=0.4.6",
        "vosk>=0.3.44",
        "pyaudio>=0.2.13",
        "gtts>=2.3.2",
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "sqlalchemy>=2.0.25",
        "psycopg2-binary>=2.9.9",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.3",
        "supabase>=2.3.0",
        "asyncpg>=0.29.0"
    ]
)

APP = ['main.py']
DATA_FILES = ['static']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['flet', 'supabase', 'python-dotenv'],
    'iconfile': 'static/icons/cloud_icon.icns',
    'plist': {
        'CFBundleName': 'Cloud AI',
        'CFBundleDisplayName': 'Cloud AI',
        'CFBundleGetInfoString': 'Cloud AI Uygulaması',
        'CFBundleIdentifier': 'com.cloudai.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024, Cloud AI',
        'NSHighResolutionCapable': True,
    },
    'includes': ['flet', 'supabase', 'python-dotenv'],
    'excludes': ['tkinter'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 