#!/usr/bin/env python3.6
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import subprocess
import sys
import tempfile
import typing
from abc import ABC, abstractmethod
from autosynth.log import logger


class AbstractSynthesizer(ABC):
    """Makes invoking synthtool abstract.

    synthesize() is called from the bottom of the call stack, and takes 5
    parameters, and it's a hassle to pass 4 of the 5 parameters from the
    top to the bottom of the call stack.  So wrap them all in this neat
    little bundle, which also happens to make testing with mocks easier.
    """

    @abstractmethod
    def synthesize(self, environ: typing.Mapping[str, str] = None) -> str:
        """
        Keyword Arguments:
            environ {[type]} -- Environment variables. (default: {None})

        Returns:
            The log of the call to synthtool.
        """
        pass

    def synthesize_and_catch_exception(
        self, environ: typing.Mapping[str, str] = None
    ) -> typing.Union[bool, str]:
        try:
            return self.synthesize(environ)
        except subprocess.CalledProcessError:
            return False


class Synthesizer(AbstractSynthesizer):
    """The real synthesizer that calls synthesize()."""

    def __init__(
        self,
        metadata_path: str,
        extra_args: list,
        deprecated_execution: bool = False,
        synth_py_path: str = None,
    ):
        """
        Arguments:
            metadata_path {str} -- Path to synth.metadata file to write.
            extra_args {list} -- Extra args to pass to synth.py.

        Keyword Arguments:
            deprecated_execution {bool} -- Call synth.py directly instead of invoking synthtool. (default: {False})
            synth_py_path {str} -- Path to synth.py. [description] (default: {None})
        """
        self.metadata_path = metadata_path
        self.extra_args = extra_args
        self.deprecated_execution = deprecated_execution
        self.synth_py_path = synth_py_path or "synth.py"

    def synthesize(self, environ: typing.Mapping[str, str] = None) -> str:
        """
        Returns:
            The log of the call to synthtool.
        """
        logger.info("Running synthtool")
        if not self.deprecated_execution:
            command = [
                sys.executable,
                "-m",
                "synthtool",
                "--metadata",
                self.metadata_path,
                self.synth_py_path,
                "--",
            ]
        else:
            # Execute the synthesis script directly (deprecated)
            command = [sys.executable, self.synth_py_path]

        logger.info(command)
        # Use a temporary file to tee the output, so we can see the output line
        # by line and still return it as a string.
        with tempfile.NamedTemporaryFile("wt+") as synth_log_file:
            tee_proc = subprocess.Popen(
                ["tee", synth_log_file.name], stdin=subprocess.PIPE
            )
            # Invoke synth.py.
            synth_proc = subprocess.run(
                command + self.extra_args,
                stderr=subprocess.STDOUT,
                stdout=tee_proc.stdin,
                env=(environ or os.environ),
                universal_newlines=True,
            )
            if synth_proc.returncode:
                logger.error("Synthesis failed")
                synth_proc.check_returncode()  # Raise an exception.
            synth_log_file.seek(0)
            return synth_log_file.read()
