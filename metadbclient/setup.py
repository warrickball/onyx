import setuptools

exec(open("metadbclient/version.py").read())

setuptools.setup(
    name="metadb",
    author="Thomas Brier",
    version=__version__,  # type: ignore
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": "metadb = metadbclient.cli:main"},
)
