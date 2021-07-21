import os
import shutil
from pathlib import Path

from .console import Console


class HAC(Console):

    ENV_PATH = Path(os.getenv("DEVKITPRO"))

    COMMANDS = {
        "zip": "cd {src}; zip -r -9 {out}/game.love .",
        "meta": "nacptool --create \"{name}\" \"{author}\" \"{version}\" {dst}.nacp",
        "binary": "elf2nro {elf} {dst}.nro --icon={icon} --nacp={dst}.nacp --romfsdir={out}/romfs"
    }

    def __init__(self, data):
        super().__init__(data)

    def build(self):
        super().build()

        self.build_directory.mkdir(parents=True, exist_ok=True)

        (self.output_directory / "romfs"/ "shaders").mkdir(parents=True, exist_ok=True)
        for x in ["color_fsh.dksh", "texture_fsh.dksh", "transform_vsh.dksh"]:
            shutil.copy(Path(__file__).parents[1] / "romfs" / x, self.output_directory / "romfs" / "shaders")

        command = HAC.COMMANDS["zip"].format(src=self.source_directory,
                                             out=Path.cwd() / self.output_directory)

        self._run_command(command)

        command = HAC.COMMANDS["meta"].format(name=self.name,
                                              author=self.author,
                                              version=self.version,
                                              dst=self.output_directory / self.target_name.name)

        self._run_command(command)

        command = HAC.COMMANDS["binary"].format(elf=self.get_binary(),
                                                icon=self.get_icon(),
                                                dst=self.output_directory / self.target_name.name,
                                                out=self.output_directory)

        self._run_command(command)

        nro = open((self.output_directory / self.target_name.name).with_suffix(".nro"), "rb").read() + open(self.output_directory / "game.love", "rb").read()
        with open((self.output_directory / self.target_name.name).with_suffix(".nro"), "wb") as f:
            f.write(nro)

    def __str__(self):
        return "Nintendo Switch"
