from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .exceptions import (
    OMCCommandError,
    OMCNotFoundError,
    MustGatherError,
)


class OMCClient:

    def __init__(self, omc_path: str = "omc"):
        """
        Initialize the OMC client.

        Args:
            omc_path:
                Path/name of the omc executable.
                Defaults to 'omc', assuming it is available in PATH.
        """

        self.omc_path = omc_path

    def _check_omc(self) -> None:
        """
        Verify that the omc executable exists.
        """

        if shutil.which(self.omc_path) is None:
            raise OMCNotFoundError(
                f"OMC executable '{self.omc_path}' was not found "
                "in PATH."
            )

    def run(self, args: list[str]) -> str:
        """
        Execute an OMC command.

        Example:

            client.run(["get", "nodes"])

        becomes:

            omc get nodes
        """

        self._check_omc()

        command = [self.omc_path, *args]

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

        except OSError as exc:

            raise OMCCommandError(
                f"Failed to execute OMC command: "
                f"{' '.join(command)}"
            ) from exc

        if result.returncode != 0:

            error = result.stderr.strip()

            if not error:
                error = result.stdout.strip()

            raise OMCCommandError(
                f"OMC command failed.\n"
                f"Command: {' '.join(command)}\n"
                f"Exit code: {result.returncode}\n"
                f"Output:\n{error}"
            )

        return result.stdout.strip()

    def version(self) -> str:
        """
        Return the installed OMC version.
        """

        return self.run(["version"])

    def use(self, must_gather_path: str | Path) -> str:
        """
        Load an extracted must-gather into OMC.

        Equivalent command:

            omc use <must-gather>
        """

        path = Path(must_gather_path).expanduser().resolve()

        if not path.exists():

            raise MustGatherError(
                f"Must-gather path does not exist: {path}"
            )

        if not path.is_dir():

            raise MustGatherError(
                f"Must-gather path is not a directory: {path}"
            )

        return self.run(
            [
                "use",
                str(path),
            ]
        )