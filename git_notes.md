Forking a github repo to another github repo, cloning your copy to local, then tracking the parent ('upstream') repo (https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/configuring-a-remote-for-a-fork):
1. Fork the github repo to your github account
1. Locally, clone your fork, which automatically creates an 'origin' remote reference pointing to your fork.
1. Locally, specify the parent github repo as a remote reference named 'upstream':
    `git remote add upstream https://github.com/owner/repo.git`
    
1. Branch locally:
    `git checkout -b my_branch`
1. Do work, commit changes to local branch.
1. Push local branch to origin:
    `git push origin/my_branch my_branch`
    (or we could use a branch that is already tracking 'origin')
1. On github, create a pull request on upstream to pull your new branch from your github repo
1. Changes accepted and merged into 'upstream's master. Now we need to update our local and remote master branches to match 'upstream'.
1. Locally, rebase master to upstream/master:
    `git rebase upstream/master master` (If you're not violating the Golden Rule of rebasing https://www.atlassian.com/git/tutorials/merging-vs-rebasing - ie, you don't care about losing any local history)
1. Now push the local branch (which now matches 'upstream') to 'origin' (your github fork of 'upstream'):
    `git push origin/master master`
1. Delete your fork locally:
    `git branch -D my_branch`
1. Delete your branch on your github repo