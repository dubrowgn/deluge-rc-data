# Deluge RcData Plugin

Reference count torrent data for safe removal at any time.

## Explanation

This is a Deluge plugin that does 2 things:
1. On torrent download completion, recursively hard-links files to `dest_dir`.
2. On seeding torrent ratio > `ratio`, automatically remove torrent with original data.

This allows your seedbox to automatically clean up when a target ratio is reached without worrying about whether it's safe to do so. Conversely, when you're done with the files, you can safely remove them from `dest_dir` without worrying about whether the seedbox is done with the data yet.

## Example config

Enabling the plugin creates a default config, which you can modify to suit your needs.

```json
// rc-data.conf
{
    "dest_dir": "/data/done",
    "ratio": 2.0
}
```

## Building

```bash
python3 ./setup.py bdist_egg
```

## Known Issues

* Linux is unable to hard-link across mount points or file systems.
* If you are using Deluge in a docker container, both `dest_dir` and your data directory must be in the same docker volume.
* No Windows support.
