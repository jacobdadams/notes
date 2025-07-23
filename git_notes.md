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

### Create a new repo containing only a subset of commits (ie, only the commits for a certain branch)

Impetuous: The housing-unit-inventory repo had a bunch of large GDB files in its history that were bloating the repo. I wanted to trim the repo history to exclude those blobs. We also had to create a new repo for this since it was a fork and git-guardian can't do forks.

Basic steps:

1. Create a new empty repo on github and clone it locally. To avoid merge conflicts later and make things easier, delete any template files that are also in the commits we'll be pulling over (.gitignore, license, etc etc)
2. Add the old repo as a remote. If you've got it cloned locally, you can use that repo instead of going out to github ("remotes" can be on your local machine). `git remote add old \path\to\old\repo`
3. git fetch the old remote to load its history.
4. This is the meat: git cherry-pick the commits you want in your new repo.

  - Perhaps the easiest way is to have a branch pointing at the latest commit and a branch pointing at the last commit you don't want- ie, make it looks like you branched off the old repo, did some work, and now you want to pull that branch into its own repo, keep the history of that branch, but discard the history of everything else. The first commit of that branch now becomes the starting point.
  - With your branch pointers set (remember, a git branch is just a pointer to a commit), you can use double-dot notation to say "give me everything in branch "dev" that's not in branch "main": `git cherry-pick old\main..old\dev`. Note that I'm using the remote name in the branch names for clarity.
  - cherry-pick takes a commit, figures out the diff between it and HEAD, and uses this to apply the commit to HEAD. Specifying a range of commits applies them one at a time, in order, replicating the development history of that range.

5. The cherry-pick process of sequentially applying diffs onto HEAD may lead to a commit that has a non-trivial conflict. The general idea is to fix the conflict and run `git cherry-pick --continue` to resume the process.

  - In this instance, there was a commit deleting files from the old repo that weren't created by any of the selected commits. Therefore, the commit does nothing and becomes an empty commit. The message helpfully prompts you to do an empty commit with `git commit --allow-empty`, after which you continue the cherry pick.
  - You may also get merge conflicts. This is very similar to merge conflicts in a rebase—the process of applying commits on top of a certain commit is basically the same. Assuming you're pulling the commits into a new, empty repo the best way to avoid these is to make sure there aren't any files in the new empty repo that any of the incoming commits alter. I tried this whole process twice- the first time, there were template files in the repo that led to a merge conflict, and in resolving that I created new conflicts down the line. I started over, nuked those files before cherry-picking, and then it ran fine. 

6. Once the cherry-pick is finished, you should now have a working tree that is identical to your branch in the old repo. Now run `git remote rm old` to remove the remote references to the old repo.
7. To remove all the blobs and trees from old in the new repo, force git's garbage collection to prune unreferenced objects. All the blobs from the old repo that are only referenced by commits that weren't part of the cherry pick are now orphaned and will be nuked. In this example, I went from 2+ GB to 17 MB.

Output:

```bash
#: Clone the new, empty repo from github
me@my-machine /c/gis/git
$ git clone https://github.com/agrc/housing-unit-inventory
Cloning into 'housing-unit-inventory'...
remote: Enumerating objects: 5, done.
remote: Counting objects: 100% (5/5), done.
remote: Compressing objects: 100% (5/5), done.
remote: Total 5 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
Receiving objects: 100% (5/5), done.

me@my-machine /c/gis/git
$ cd housing-unit-inventory

#: Add the old repo as a (local) remote
me@my-machine /c/gis/git/housing-unit-inventory (main)
$ git remote add old /c/gis/git/housing-unit-inventory_old/

#: Fetch the history of the old remote into our new repo
me@my-machine /c/gis/git/housing-unit-inventory (main)
$ git fetch old
remote: Enumerating objects: 3816, done.
remote: Counting objects: 100% (3816/3816), done.
remote: Compressing objects: 100% (1257/1257), done.
Receiving objects: 100% (3816/3816), 1.10 GiB | 39.35 MiB/s, done.
remote: Total 3816 (delta 2562), reused 3527 (delta 2370), pack-reused 0
Resolving deltas: 100% (2562/2562), done.
From C:/gis/git/housing-unit-inventory_old
 * [new branch]      dev        -> old/dev
 * [new branch]      main       -> old/main

#: cherry-pick all commits in old/dev that aren't in old/main (dev branched from main and had a ton of work that was
#: never merged back in)
me@my-machine /c/gis/git/housing-unit-inventory (main)
$ git cherry-pick remotes/old/main..remotes/old/dev
[main 7b62bc8] chore: dev framework
 Date: Fri Jan 21 09:32:19 2022 -0700
 9 files changed, 207 insertions(+)
 create mode 100644 .coveragerc
 create mode 100644 .editorconfig
 create mode 100644 .gitignore
 create mode 100644 .vscode/extensions.json
 create mode 100644 .vscode/launch.json
 create mode 100644 .vscode/settings.json
 create mode 100644 pylintrc
 create mode 100644 setup.cfg
 create mode 100644 setup.py
[main 9e84ba2] chore: make pip install work
 Date: Fri Jan 21 11:09:27 2022 -0700
 2 files changed, 8 insertions(+), 3 deletions(-)
 create mode 100644 src/housing_characteristics/main.py

# <snipping out a long series of commits>

#: This commit removed a file that was never introduced by the chosen commits, so it's empty. We allow the empty commit
#: and continue the cherry-pick (I guess we could have skipped this one, but oh well)
[main 1151e03] chore: dont forget to save
 Date: Wed Feb 9 14:24:02 2022 -0700>
 1 file changed, 1 insertion(+), 1 deletion(-)
The previous cherry-pick is now empty, possibly due to conflict resolution.
If you wish to commit it anyway, use:

    git commit --allow-empty

Otherwise, please use 'git cherry-pick --skip'
On branch main
Your branch is ahead of 'origin/main' by 27 commits.
  (use "git push" to publish your local commits)

Cherry-pick currently in progress.
  (run "git cherry-pick --continue" to continue)
  (use "git cherry-pick --skip" to skip this patch)
  (use "git cherry-pick --abort" to cancel the cherry-pick operation)

nothing to commit, working tree clean

me@my-machine /c/gis/git/housing-unit-inventory (main|CHERRY-PICKING)
$ git commit --allow-empty
[main e92d7f5] chore: delete non-housing stuff
 Date: Wed Feb 9 14:43:17 2022 -0700

me@my-machine /c/gis/git/housing-unit-inventory (main|CHERRY-PICKING)
$ git cherry-pick --continue
[main c5a4c60] chore: add centroids to parcels for spatial join
 Date: Wed Feb 9 18:00:40 2022 -0700
 1 file changed, 44 insertions(+), 4 deletions(-)

# <snip>

#: Because I had nuked the template README.md from the repo before cherry-picking, git doesn't know how to add lines
#: to a deleted file. Since the working tree now includes the desired README.md, I just git add that and continue 
CONFLICT (modify/delete): README.md deleted in HEAD and modified in 37f0b49 (docs: readme).  Version 37f0b49 (docs: readme) of README.md left in tree.
error: could not apply 37f0b49... docs: readme
hint: After resolving the conflicts, mark them with
hint: "git add/rm <pathspec>", then run
hint: "git cherry-pick --continue".
hint: You can instead skip this commit with "git cherry-pick --skip".
hint: To abort and get back to the state before "git cherry-pick",
hint: run "git cherry-pick --abort".

me@my-machine /c/gis/git/housing-unit-inventory (main|CHERRY-PICKING)
$ git add README.md

me@my-machine /c/gis/git/housing-unit-inventory (main|CHERRY-PICKING)
$ git cherry-pick --continue
[main 4620307] docs: readme
 Date: Mon Apr 18 15:52:06 2022 -0600
 1 file changed, 31 insertions(+)
 create mode 100644 README.md

# <snip>

[main 32be1c9] chore: various prototyping in notebooks
 Date: Tue Jul 22 17:33:46 2025 -0600
 5 files changed, 16319 insertions(+), 787 deletions(-)
 create mode 100644 docs/washco.ipynb
 create mode 100644 docs/wfrc2024update.ipynb

#: Now that the cherry pick is completed, remove the remote reference to the old repo
me@my-machine /c/gis/git/housing-unit-inventory (main)
$ git remote rm old

#: Prune our new repo to remove all objects orphaned by removing the remote reference 
#: The only stuff kept is objects referenced by the commits we cherry-picked.
me@my-machine /c/gis/git/housing-unit-inventory (main)
$ git gc --prune=now
Enumerating objects: 979, done.
Counting objects: 100% (979/979), done.
Delta compression using up to 16 threads
Compressing objects: 100% (474/474), done.
Writing objects: 100% (979/979), done.
Total 979 (delta 527), reused 688 (delta 391), pack-reused 0

me@my-machine /c/gis/git/housing-unit-inventory (main)
```
