Forking a github repo to another github repo, cloning your copy to local, then tracing the parent ("upstream") repo (https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/configuring-a-remote-for-a-fork):
1. Fork the github repo to your github account ("origin")
1. Locally, clone your fork
1. Locally, specify the parent repo as the upstream:
    `git remote add upstream https://github.com/owner/repo.git`
    
1. Branch locally:
    `git branch -c my_branch`
1. Do work, commit changes to local branch.
1. Push local branch to origin:
    `git push origin my_branch`
1. On github, create a pull request on upstream to pull your new branch from your github repo
1. Changes accepted and merged into upstream's master. Now we need to update our local and remote master branches.
1. Locally, pull the upstream master:
    `git pull upstream master` (or `git fetch upstream master` and `git merge master`)
1. Now push the local branch (which has the upstream changes) to remote (your github fork of upstream):
    `git push remote master`
1. Delete your fork locally:
    `git branch -D my_branch`
1. Delete your branch on your github repo