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
1. On github, create a pull request on the parent repo 'upstream' to pull your branch from your github repo
1. Changes accepted and merged into 'upstream's master. Now we need to update our local and 'origin' master branches to match 'upstream'.
1. Locally, rebase master to upstream/master:
    `git rebase upstream/master master` (If you're not violating the Golden Rule of rebasing https://www.atlassian.com/git/tutorials/merging-vs-rebasing - ie, you don't care about losing any local history)
1. Now push the local branch (which now matches 'upstream') to 'origin' (your github fork of 'upstream'):
    `git push origin/master master`
1. Delete your branch locally:
    `git branch -D my_branch`
1. Delete your branch on your github repo

Working on changes, want to go back but still save your changes for later reference? Stash them!

1. `git stash` - puts your local, uncommitted changes into your local-only stash
1. `git stash branch <name>` - (optional) create a new branch based on your stashed changes
1. OR `git stash pop`/`apply` - apply your last stash to current branch. `apply` applies them and leaves them in the stash, `pop` applies them and removes them from the stash.

### Create repo on github, clone local, branch, push branch to github, PR for branch to master via github, rebase and merge branch on github, BUT FORGOT to rebase & merge locally or delete the branch and create new one

Now we've got a situation where a tree shows two separate branches with duplicate commits:

1. `master(origin)`, which is also `origin/HEAD`
1. `feature(origin)`

Because we forgot to rebase the local `feature` branch but instead made new commits and pushed them to origin, `feature(origin)`'s parent remains our initial commit. `master(origin)` was updated with all our changes and now contains duplicate commits for all the history added by the earlier work on `feature`. `master(origin)` and `feature(origin)`'s comment parent is the intial commit, not the point where we rebased & merged.

This shows up in github when we push our new changes on `feature` and then go to do a Pull Request. The diffs show all the changes going back to the initial commit, instead of just going back to our first rebase and merge. 

To fix this, we need to do three things, assuming right now the local `feature` branch has our latest changes:

1. Locally, rebase `feature` onto `master`:
   * `git checkout feature`
   * `git rebase master`
   * `git checkout master` (we'll stay on `master` for future steps)
   * This moves our local `feature` branch's parent to the latest common commit with our local `master` branch
2. Delete the `feature` branch on github (easier? than trying to rebase this remote branch)
   * We'll push it again later to recreate the branch with the proper parent
3. Stop our local repo from tracking github by removing `origin` altogether:
   * `git remote rm origin`
   * Now all the refernces to `origin` are gone in the tree view. Our local repo should now have the proper graph
4. Re-add our github repo as `origin` and track it again from master:
   * `git remote add origin https://github.com/org/repo.git`
   * `git branch -u origin/master` OR `git fetch` (if `branch -u` fails, `fetch`)
   * Now our tree shows `master` tracking `origin/master` (assuming `origin/master` hasn't changed since our first rebase & merge; if it has...?)
5. Publish/push `feature` to github:
   * `git push -u origin feature`

Now both the local and remote `feature` branches should branch off of the latest common commit from `master`. You can do a pull request from github to merge `feature` to `master`, and after pulling them again locally everything should look right.

### Move current branch back a few commits but keep them as a separate branch of their own

Let's say you make a few commits working on feature C but then decide to table that feature for now. You want to keep that work for a later date, but move your branch back to where you were before you started. We'll create a new branch at the current HEAD, then rebase our original branch back to a good commit.

1. Create a new branch (`feat_c`) from the current branch (`dev`).
1. Push the new branch up to github.
1. Checkout your original branch (`dev`).
1. Do a hard reset of your current branch (`dev`) to the appropriate commit in your history.
1. Force push your current branch back to github to update `dev/origin` to our new (old) point: `git push -f`.

Now all the commits you did for feature C are saved in branch `feat_c` and you can keep working on branch `dev` from where you were before you started.