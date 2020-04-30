# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os

from autosynth import github


def _get_repo_list_from_sloth(gh):
    contents = gh.get_contents("googleapis/sloth", "repos.json")
    repos = json.loads(contents)["repos"]
    return repos


def _is_python_synth_repo(gh, repo):
    """Finds Python repositories with synth files in the top-level directory."""
    # Only python repos.
    if repo["language"] != "python":
        return False
    # No private repos.
    if "private" in repo["repo"]:
        return False
    # Only repos with a synth.py in the top-level directory.
    if not gh.check_for_file(repo["repo"], "synth.py"):
        return False

    return True


def list_repositories():
    """Finds repositories with a `synth.py` in the top-level"""
    gh = github.GitHub(os.environ["GITHUB_TOKEN"])

    repos = _get_repo_list_from_sloth(gh)
    repos = [repo for repo in repos if _is_python_synth_repo(gh, repo)]

    repo_list = [
        {"name": repo["repo"].split("/")[-1], "repository": repo["repo"]}
        for repo in repos
    ]

    return repo_list


if __name__ == "__main__":
    import yaml

    print(yaml.dump(list_repositories()))
