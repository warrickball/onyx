import setuptools

exec(open("metadbclient/version.py").read())

setuptools.setup(
    name="metadbclient",
    author="Thomas Brier",
    version=__version__, # type: ignore
    packages=setuptools.find_packages(),
    entry_points = {
        "console_scripts": "metadbclient = metadbclient.main:run"
    }
)
