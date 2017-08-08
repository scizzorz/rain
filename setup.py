from setuptools import setup

setup(name='rain',
      version='0.1',
      description='A programming language.',
      url='https://github.com/scizzorz/rain',
      author='John Weachock',
      author_email='jweachock@gmail.com',
      license='MIT',
      packages=['rain'],
      scripts=[
        'bin/rain',
        'bin/rain-help',
        'bin/rain-compile'
      ],
      include_package_data=True,
      install_requires=[
        'camel',
        'orderedset',
        'termcolor',
      ],
      zip_safe=False)
