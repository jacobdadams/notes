# Backing up files via rsync

1. Install rsync for windows via chocolatey: `choco install rsync`
1. Create a list of directories to backup relative to `c:\`. For example, `gis/Projects`
1. Create a directory in the destination to put everything
1. Run rsync in archive mode
1. `rsync -avur --files-from=/cygdrive/c/gis/git/notes/rsync_files.txt /cygdrive/c/ /cygdrive/d/backup/rolling`
