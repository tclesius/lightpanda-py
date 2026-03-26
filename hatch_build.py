from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class BinaryDownloadHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:
        build_data["pure_python"] = False
        build_data["infer_tag"] = True
