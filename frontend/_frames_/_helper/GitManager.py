# pages/qframes/helper/GitManager.py

import os
from git import Repo, GitCommandError

class GitManager:
    """
    Manages Git version control operations.
    """
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        if not os.path.exists(os.path.join(repo_path, '.git')):
            self.repo = Repo.init(repo_path)
            print("Initialized new Git repository.")
        else:
            self.repo = Repo(repo_path)
            print("Existing Git repository found.")

    def commit_changes(self, message: str):
        """
        Commits all changes in the repository with the provided commit message.
        """
        try:
            self.repo.git.add(A=True)
            if self.repo.index.diff("HEAD") or self.repo.untracked_files:
                self.repo.index.commit(message)
                print("Changes committed successfully.")
            else:
                print("No changes to commit.")
        except GitCommandError as e:
            print(f"Git commit failed: {e}")

    def get_diff(self) -> str:
        """
        Returns the current diff of the repository.
        """
        try:
            return self.repo.git.diff()
        except GitCommandError as e:
            print(f"Git diff failed: {e}")
            return ""
