from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
import logging
from pathlib import Path
from subprocess import CalledProcessError, run, PIPE
from threading import Thread
from time import sleep

log = logging.getLogger("deluge.plugins.rc-data")

def _hard_link(src_path: Path, dest_path: Path):
    args = ["cp", "-rl", str(src_path), str(dest_path)]
    run(args, check=True, stdout=PIPE, stderr=PIPE)


class ThreadLoop():
    def __init__(self, name, target, interval_sec=1):
        self.target = target
        self.interval_sec = interval_sec
        self.should_run = False
        self.thread = Thread(name=name, target=self.loop)

    def start(self):
        self.should_run = True
        self.thread.start()

    def stop(self):
        self.should_run = False
        self.thread.join()

    def loop(self):
        while self.should_run:
            self.target()
            sleep(self.interval_sec)


class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager(
            "rc-data.conf",
            {
                "dest_dir": "/data/done",
                "ratio": 2.0,
            }
        )
        self.config.save()

        self.torrent_mgr = component.get("TorrentManager")

        self.event_mgr = component.get("EventManager")
        self.event_mgr.register_event_handler("TorrentFinishedEvent", self.on_finished)

        self.looper = ThreadLoop("rc-data.loop", self.poll_torrents, 10)
        self.looper.start()

    def disable(self):
        self.looper.stop()
        self.event_mgr.deregister_event_handler("TorrentFinishedEvent", self.on_finished)

    def on_finished(self, tid):
        try:
            torrent = self.torrent_mgr.torrents[tid]
            info = torrent.get_status(['name', 'download_location'])

            name = info["name"]
            src_path = Path(info["download_location"]) / name
            dest_path = Path(self.config["dest_dir"]) / name

            log.info(f"Hard-linking '{src_path}' -> '{dest_path}'")
            _hard_link(src_path, dest_path)
        except CalledProcessError as e:
            log.error(f"Failed to hard-link {name}: {e.stderr}")

    def poll_torrents(self):
        def should_remove(torrent):
            return (
                torrent.is_finished and
                torrent.state == "Seeding" and
                torrent.get_ratio() >= self.config["ratio"]
            )

        to_remove = filter(should_remove, self.torrent_mgr.torrents.values())
        for torrent in list(to_remove):
            name = torrent.get_name()
            try:
                log.info(f"Removing '{name}' due to ratio ({torrent.get_ratio()})")
                self.torrent_mgr.remove(torrent.torrent_id, remove_data=True)
            except Exception as e:
                log.error(f"Failed to remove {name}: {e}")

    @export
    def set_config(self, config):
        for k, v in config.items():
            self.config[k] = v

        self.config.save()

    @export
    def get_config(self):
        return self.config.config
