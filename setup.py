import os
import platform

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext as build_ext_orig
from wheel.bdist_wheel import bdist_wheel


class bdist_wheel_abi3(bdist_wheel):
    def get_tag(self):
        python, abi, plat = super().get_tag()

        if python.startswith("cp"):
            # on CPython, our wheels are abi3 and compatible back to 3.9
            return "cp39", "abi3", plat

        return python, abi, plat

class build_ext(build_ext_orig):
    def get_export_symbols(self, ext):
        # For CTypes extensions, do not require to export a `PyInit_` function
        if isinstance(ext, CTypes):
            return ext.export_symbols
        return super().get_export_symbols(ext)

    def get_ext_filename(self, fullname):
        # For CTypes extensions, force to use the default system prefix and extension for shared libraries.
        # This avoids file extensions like `.cpython-312-x86_64-linux-gnu.so`.
        if isinstance(self.ext_map[fullname], CTypes):
            shared_lib_prefix = {
                "Windows": "",
            }.get(platform.system(), "lib")
            shared_lib_ext = {
                "Darwin": ".dylib",
                "Windows": ".dll",
            }.get(platform.system(), ".so")
            fullname_components = fullname.split(".")
            ext_fullname = "".join(
                (
                    (
                        os.path.join(*fullname_components[:-1]),
                        os.path.sep,
                    )
                    if len(fullname_components) > 1
                    else tuple()
                )
                + (
                    shared_lib_prefix,
                    fullname_components[-1],
                    shared_lib_ext,
                )
            )
            return ext_fullname
        return super().get_ext_filename(fullname)


class CTypes(Extension):
    pass

setup(
    ext_modules=[
        CTypes(
            "hyperhyphen.hyphenate",
            sources=["./lib/hnjalloc.c", "./lib/hyphen.c", "./lib/hyphenate.c"],
            define_macros=[("Py_LIMITED_API", "0x03090000")],
            py_limited_api=True,
        ),
    ],
    cmdclass={"build_ext": build_ext, "bdist_wheel": bdist_wheel_abi3}
)