from setuptools import setup, find_packages

setup(
    name="doormaNet",
    version="1.0.0",
    author="Masoom Verma",
    description="A network security scanner with protection features.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=["main"],
    entry_points={
        'gui_scripts': [
            'doormanet = main:main_gui_function'
        ]
    },
    install_requires=[
        "PyQt5",
        "scapy",
        "psutil"
    ]
)