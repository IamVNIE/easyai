from setuptools import setup,find_packages

about = {}
with open("easyai/__about__.py") as fp:
    exec(fp.read(), about)


with open('README.md') as readme_file:
	readme = readme_file.read()


	
setup(name='easyai',
      version=about['__version__'],
      description='Easy-AI is a AI framework for making it easier to perform deep learning experiments',
      url='https://github.com/IamVNIE/easyai',
      author=about['__author__'],
      author_email='vj338@nyu.edu',
      license=about['__license__'],
	  install_requires=['pandas','tensorflow','numpy', 'matplotlib', 'plotly', 'pandas', 'seaborn', 'sklearn'],
      packages=find_packages(),
	  include_package_data=True,
	  package_data={
	  '': ['*.pyd',
			#'*.pyc', 
			'*.h5', '*.json','*.txt' ],
	  },
	  long_description=readme,
      classifiers=[
          'Development Status :: 1 - Development/Stable',
          'Intended Audience :: Science/Research',
          'Topic :: General/Engineering',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
      ],
      zip_safe=True,
	  python_requires='>=3.5, <3.8',
      extras_require={
          'test': ['pytest'],
      },
	  )
