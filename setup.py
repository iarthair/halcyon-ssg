from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='halcyon',
    version='0.1.0',
    author='Brian Stafford',
    author_email='brian.stafford60+halcyon@gmail.com',
    description='Static website builder.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://iarthair.github.io/',
    packages=find_packages(),
    include_package_data=False,
    install_requires=[
        'pyyaml',
        'hycmark',
        'jinja2',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
    ],
    scripts=['scripts/halcyon'],
    python_requires='>=3.6',
)
