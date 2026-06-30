# 1. In cron.tab, use $HOME/scripts/... instead of hardcoded /Users/northridge/...
#    if usernames may differ.
# 2. Turn off sleep on ONL Audio (System Settings > Energy) so cron/jobs won’t miss
#    Sunday runs.
# 3. Run one manual full test before Sunday:
#    /usr/bin/python3 ~/scripts/hyperdeck_pipeline/bin/master_sync_upload.py --no-email

# 1) Paths + files
echo "HOME=$HOME"
pwd
ls -l \
  ~/scripts/hyperdeck_pipeline/bin/master_sync_upload.py \
  ~/scripts/hyperdeck_pipeline/bin/hyperdeck_sync.py \
  ~/scripts/hyperdeck_pipeline/bin/rename_files.py \
  ~/scripts/hyperdeck_pipeline/bin/copy_to_gdrive.py \
  ~/scripts/hyperdeck_pipeline/bin/cleanup_hyperdeck.py \
  ~/scripts/legacy/hyperdeck_bash/master_sync_upload.sh \
  ~/scripts/legacy/hyperdeck_bash/hyperdeck_sync.sh \
  ~/scripts/legacy/hyperdeck_bash/rename_files.sh \
  ~/scripts/legacy/hyperdeck_bash/copy_to_gdrive.sh \
  ~/scripts/legacy/hyperdeck_bash/cleanup_hyperdeck.sh

# 2) Create required dirs
mkdir -p ~/HyperDeckDownloads
sudo mkdir -p /usr/local/var/log/hyperdeck
sudo touch /usr/local/var/log/hyperdeck/sync_upload.log /usr/local/var/log/hyperdeck/cron.log
sudo chown -R "$USER":staff /usr/local/var/log/hyperdeck

# 3) Tooling check
command -v lftp nc rclone mail
rclone version
rclone listremotes

# 4) HyperDeck connectivity check
nc -vz 10.20.193.141 21
nc -vz 10.20.193.141 9993
nc -vz 10.20.193.113 21
nc -vz 10.20.193.113 9993

# 5) Script smoke tests
/usr/bin/python3 ~/scripts/hyperdeck_pipeline/bin/hyperdeck_sync.py HD1 ~/HyperDeckDownloads --dry-run
/usr/bin/python3 ~/scripts/hyperdeck_pipeline/bin/hyperdeck_sync.py HD2 ~/HyperDeckDownloads --dry-run
/usr/bin/python3 ~/scripts/hyperdeck_pipeline/bin/rename_files.py --dry-run ~/HyperDeckDownloads

# 6) Cron install (review first)
cat ~/scripts/cron.tab.onlaudio
crontab -l
# crontab ~/scripts/cron.tab.onlaudio
# crontab -l

# 7) Verify timezone + clock
date
systemsetup -gettimezone
