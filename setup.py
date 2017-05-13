try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='winnow-filters',
    packages=['winnow'],
    version='0.0.5',
    description='Winnow is a framework for server-side filtering of data.',
    author='Brian Schiller',
    author_email='bgschiller@gmail.com',
    url='https://github.com/bgschiller/winnow',
    download_url='https://github.com/bgschiller/winnow/archive/0.0.1.tar.gz',
    keywords=['sql', 'jinja2', 'filters'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
    ],
    install_requires=[
        'jinjasql',
        'python-dateutil',
        'six',
    ],
)
