from setuptools import setup

name="RcData"
desc = "Reference count torrent data for safe removal at any time"

setup(
    name=name,
    version="1.0.2",
    description=desc,
    author="Dustin Brown",
    author_email="me@dubrowgn.com",
    url="https://github.com/dubrowgn/deluge-rc-data",
    license="MIT",
    long_description=desc,

    packages=["rc_data"],

    entry_points=(
        "[deluge.plugin.core]\n"
        f"{name}=rc_data:CorePlugin\n"
    )
)
