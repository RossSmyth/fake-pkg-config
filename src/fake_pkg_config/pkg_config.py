import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from shutil import which
from subprocess import run

from libs import Lib


class BasePkgConfig(ABC):
    @abstractmethod
    def get_libs(self, lib: Lib) -> str:
        """Get a pkg-config modules --libs output"""

    @abstractmethod
    def get_cflags(self, lib: Lib) -> str:
        """Get a pkg-config modules --cflags output"""

    @abstractmethod
    def get_modversion(self, lib: Lib) -> str:
        """Get a pkg-config modules --modversion output"""

    @abstractmethod
    def get_variable(self, lib: Lib, var: str) -> str:
        """Get a pkg-config modules --variable=var output"""


class FakePkgConfig(BasePkgConfig):
    fake_root: Path

    def __init__(self) -> None:
        self.fake_root = Path(tempfile.mkdtemp(prefix="nixpkgs")) / "fake"

        super().__init__()

    def get_cflags(self, lib: Lib) -> str:
        return f"-I{self.fake_root}/{lib.name}/include"

    def get_libs(self, lib: Lib) -> str:
        return f"-L{self.fake_root}/{lib.name}/lib -l{lib.name}"

    def get_modversion(self, lib: Lib) -> str:
        # Is this a good value?
        return "1.0.0"

    def get_variable(self, lib: Lib, var: str) -> str:
        output = f"{self.fake_root}/{lib.name}"

        # Output some sane values for common variables
        match var:
            case "prefix":
                # Prefix is already set
                pass
            case "libdir":
                output += "/lib"
            case "includedir":
                output += "/include"
            case var:
                output += f"/{var}"

        return output


class RealPkgConfig(BasePkgConfig):
    pkg_config: str | None

    def __init__(self) -> None:
        probe_pkg_config = which("pkg-config")
        probe_pkgconf = which("pkgconf")

        # Note that we cannot really read PKG_CONFIG env var as we set it outself.
        # Though we could disambiguate as we do below.

        if probe_pkgconf is not None:
            self.pkg_config = "pkgconf"
        elif probe_pkg_config is not None:
            # We have a symlink called "pkg-config",
            # so we must ignore ourselves.
            path = Path(probe_pkg_config)

            # We should be directly next to it.
            fake_config = path.with_name("fake-pkg-config")

            if fake_config.exists():
                self.pkg_config = None
            else:
                self.pkg_config = "pkg-config"
        else:
            self.pkg_config = None

        super().__init__()

    def _run(self, lib: Lib, *args: str) -> str:
        if self.pkg_config is None:
            return ""

        # Else just run pkg-config
        return run(
            [self.pkg_config, *args, lib.name],
            capture_output=True,
            encoding="utf-8",
        ).stdout

    def exists(self, lib: Lib) -> bool:
        """Checks if a pkg-config module actually exists or not"""
        if self.pkg_config is None:
            return False

        # pkg-config return code when it doesn't exist
        code = run([self.pkg_config, "--exists", lib.name]).returncode
        return code == 0

    def get_cflags(self, lib: Lib) -> str:
        return self._run(lib, "--cflags")

    def get_libs(self, lib: Lib) -> str:
        return self._run(lib, "--libs")

    def get_modversion(self, lib: Lib) -> str:
        return self._run(lib, "--modversion")

    def get_variable(self, lib: Lib, var: str) -> str:
        return self._run(lib, f"--variable={var}")
