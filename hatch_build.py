import json
import platform
import urllib.request
from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

GITHUB_RELEASES = "https://api.github.com/repos/lightpanda-io/browser/releases"
RELEASE_TAG = "nightly"

PLATFORMS = {
    "Darwin": "macos",
    "Linux": "linux",
}
ARCHITECTURES = {
    "arm64": "aarch64",
    "aarch64": "aarch64",
    "x86_64": "x86_64",
    "AMD64": "x86_64",
}


class BinaryDownloadHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:
        os_name, arch = self._detect_platform()
        bin_dir = Path(self.root) / "src" / "lightpanda" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        binary_path = bin_dir / f"lightpanda-{arch}-{os_name}"

        if not binary_path.is_file() or binary_path.stat().st_size == 0:
            url = self._find_release_url(os_name, arch)
            self._download_file(url, binary_path)

    def _detect_platform(self) -> tuple[str, str]:
        system, machine = platform.system(), platform.machine()
        if system not in PLATFORMS:
            raise RuntimeError(f"Unsupported OS: {system}")
        if machine not in ARCHITECTURES:
            raise RuntimeError(f"Unsupported arch: {machine}")
        return PLATFORMS[system], ARCHITECTURES[machine]

    def _find_release_url(self, os_name: str, arch: str) -> str:
        binary_name = f"lightpanda-{arch}-{os_name}"
        request = urllib.request.Request(GITHUB_RELEASES)
        request.add_header("Accept", "application/vnd.github.v3+json")
        with urllib.request.urlopen(request, timeout=30) as response:
            releases = json.loads(response.read().decode())

        for r in releases:
            if r.get("tag_name") == RELEASE_TAG:
                for asset in r.get("assets", []):
                    if asset.get("name") == binary_name:
                        return asset["browser_download_url"]
                raise RuntimeError(f"Binary '{binary_name}' not found in release")
        raise RuntimeError(f"Release '{RELEASE_TAG}' not found")

    def _download_file(self, url: str, dest: Path) -> None:
        with urllib.request.urlopen(url, timeout=300) as response:
            dest.write_bytes(response.read())
        dest.chmod(0o755)
