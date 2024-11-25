"""
DT-Box-Inference
Pavel Chigirev, pavelchigirev.com, 2023-2024
See LICENSE.txt for details
"""

from setuptools import setup, find_packages

setup(
    name='DT-Box-Inference',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.18.5',
        'tensorflow>=2.3.0',
        'keras>=2.3.0',
        'scikit-learn>=0.23.1'
    ],
)