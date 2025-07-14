from setuptools import setup, find_packages
import os

def read_requirements():
    """Read requirements.txt and return a list of requirements."""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def read_readme():
    """Read README.md file."""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Multisensory Stimulus Presentation and Data Collection System"

setup(
    name="eeg-stimulus-project",
    version="1.0.0",
    description="Software system for presenting and synchronizing multisensory stimuli while collecting EEG, eye tracking, and behavioral data",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Research Team",
    author_email="",
    url="https://github.com/SonnyS10/Multisensory-Stimulus-Presentation-and-Data-Collection-System",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    python_requires='>=3.8',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Operating System :: OS Independent",
    ],
    package_data={
        'eeg_stimulus_project': [
            'assets/Images/*',
            'config/*',
            'utils/*.bat',
        ],
    },
    entry_points={
        'console_scripts': [
            'eeg-stimulus=eeg_stimulus_project.main.main:main',
        ],
    },
)