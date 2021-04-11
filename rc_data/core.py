from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from pathlib import Path
from subprocess import CalledProcessError, run, PIPE
from twisted.internet.task import LoopingCall


def _hard_link(src_path: Path, dest_path: Path):
    args = ["cp", "-rl", str(src_path), str(dest_path)]
    run(args, check=True, stdout=PIPE, stderr=PIPE)


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

        self.poll_timer = LoopingCall(self.poll_torrents)
        self.poll_timer.start(10)

    def disable(self):
        self.poll_timer.stop()
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
