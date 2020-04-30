import os
import re
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

from ..data.constants import LOGGER, LOVEPOTION_3DS
from .console import Console


class CTR(Console):

    ENV_PATH = Path(os.getenv("DEVKITARM"))

    VALID_TEXTURE_EXTS = [".png", ".jpg", ".jpeg"]
    VALID_FONT_EXTS = [".ttf", ".otf"]
    VALID_SRC_EXTS = [".lua"]

    TEX3DS_CMD = "tex3ds '{}' --format=rgba8888 -z auto -o '{}.t3x'"
    MKBCFNT_CMD = "mkbcfnt '{}' -o {}.bcfnt"
    SMDH_CMD = 'smdhtool --create "{}" "{}" "{}" "{}" "{}.smdh"'
    TDSXTOOL_CMD = "3dsxtool {} {name}.3dsx --smdh={name}.smdh --romfs=build"

    def __init__(self, config, is_fused):
        super().__init__(config, is_fused)

    def _copy_file(self, path):
        """
            Copies source file from @path to the build directory.\n
            This is necessary to complete the build process.
        """

        out_path = self._ensure_path_exists(path)
        LOGGER.info("Copying source file '%s' to '%s'..", path.name, out_path)

        if out_path:
            shutil.copy(path, out_path)

    def _ensure_path_exists(self, path):
        """
            Creates the directories necessary for things.\n
            Shortcut for code re-use.
        """

        try:
            # we only want the paths after the game directory
            out = re.findall("game/(.+)", str(path.parent))

            if len(out) > 0:
                out_path = super().BUILD_DIR / out[0]
            else:
                out_path = super().BUILD_DIR

            # make the directories for the item
            out_path.mkdir(parents=True, exist_ok=True)

            return out_path
        except IndexError as e:
            LOGGER.error(str(e))

    def _convert_texture(self, path):
        """
            Converts a texture from @path to a t3x file.\n
            Can be a jp(e)g or png texture.
        """

        out_path = self._ensure_path_exists(path)
        LOGGER.info("Converting texture '%s' to '%s.t3x'..",
                    path.name, out_path / path.stem)

        if out_path:
            # format the tex3ds command and run it
            fmt_cmd = CTR.TEX3DS_CMD.format(path, out_path / path.stem)
            subprocess.run(fmt_cmd, shell=True)

    def _convert_font(self, path):
        """
            Converts a font from @path to a t3x file.\n
            Can be a ttf or otf font.
        """

        out_path = self._ensure_path_exists(path)
        LOGGER.info("Converting font '%s' to '%s.bcfnt'..",
                    path.name, out_path / path.stem)

        if out_path:
            # format the mkbcfnt command and run it
            fmt_cmd = CTR.MKBCFNT_CMD.format(path, out_path / path.stem)
            subprocess.run(fmt_cmd, shell=True)

    def clean(self):
        EXTENSIONS = [".3dsx", ".smdh"]

        for item in Console.TOP_DIR.iterdir():
            if item.suffix in EXTENSIONS:
                item.unlink()

        super().clean()

    def zip_artifacts(self):
        ARTIFACT = f"{self.name}.3dsx"

        if not self.is_fused:
            ARTIFACT = super().SRC_DIR

        with ZipFile(f"{self.name}.zip", "w") as zfile:
            zfile.write(ARTIFACT)

    def build_meta(self):
        LOGGER.info("Building smdh meta file")

        icon_path = self.get_icon()

        fmt_cmd = CTR.SMDH_CMD.format(self.name, self.description,
                                      self.author, icon_path,
                                      super().TOP_DIR / self.name)

        try:
            subprocess.run(fmt_cmd, shell=True,
                           check=True)
        except subprocess.CalledProcessError as error:
            raise Exception(error)

        LOGGER.info("Building 3dsx executable file")

        fmt_cmd = CTR.TDSXTOOL_CMD.format(LOVEPOTION_3DS,
                                          name=super().TOP_DIR / self.name)

        try:
            subprocess.run(fmt_cmd, shell=True,
                           check=True, capture_output=True)
        except subprocess.CalledProcessError as error:
            raise Exception(error)

    def build(self):
        LOGGER.info("Building for Nintendo 3DS..")

        if not LOVEPOTION_3DS.exists():
            raise FileNotFoundError(f"Missing {LOVEPOTION_3DS}?")

        for item in super().SRC_DIR.glob("**/*"):
            if item.suffix in CTR.VALID_TEXTURE_EXTS:
                self._convert_texture(item)
            elif item.suffix in CTR.VALID_FONT_EXTS:
                self._convert_font(item)
            elif item.suffix in CTR.VALID_SRC_EXTS:
                self._copy_file(item)

        if not self.is_fused:
            return

        self.build_meta()

    @staticmethod
    def name():
        return "Nintendo 3DS"