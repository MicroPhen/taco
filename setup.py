import setuptools

__packagename__ = 'taco'

def get_version():
    import os, re
    VERSIONFILE = os.path.join(__packagename__, '__init__.py')
    initfile_lines = open(VERSIONFILE, 'rt').readlines()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    for line in initfile_lines:
        mo = re.search(VSRE, line, re.M)
        if mo:
            return mo.group(1)
    raise RuntimeError('Unable to find version string in %s.' % (VERSIONFILE,))

__version__ = get_version()


setuptools.setup(name = __packagename__,
        packages = setuptools.find_packages(), # this must be the same as the name above
        version=__version__,
        description='Tool for automated cloning.',
        url='https://gitlab.fz-juelich.de/IBG-1/micropro/detl',
        download_url = 'https://gitlab.fz-juelich.de/IBG-1/micropro/detl/tarball/%s' % __version__,
        author='IBG-1',
        copyright='(c) 2020 Forschungszentrum Jülich GmbH',
        license='(c) 2020 Forschungszentrum Jülich GmbH',
        classifiers= [
            'Programming Language :: Python',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.8',
            'Intended Audience :: Developers'
        ],
        install_requires=[
            'pandas',
            'openpyxl',
            'xlrd',
            'numpy',
        ]
)

