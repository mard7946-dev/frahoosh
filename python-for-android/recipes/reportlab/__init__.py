import os
from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.util import current_directory, touch

class ReportLabRecipe(CompiledComponentsPythonRecipe):
    # Use the public GitHub mirror instead of the legacy Mercurial host.
    # The p4a recipe is based on ReportLab 3.3.0, whose setup patch matches
    # this source tree and is sufficient for Frahoosh's canvas/TTF exports.
    version = "3.3.0"
    url = "https://github.com/MrBitBucket/reportlab-mirror/archive/refs/tags/{version}.tar.gz"
    depends = ["freetype"]
    call_hostpython_via_targetpython = False

    def prebuild_arch(self, arch):
        if self.is_patched(arch):
            return
        super().prebuild_arch(arch)
        recipe_dir = self.get_build_dir(arch.arch)
        self.apply_patch("patches/fix-setup.patch", arch.arch)
        ft = self.get_recipe("freetype", self.ctx)
        ft_dir = ft.get_build_dir(arch.arch)
        ft_lib_dir = os.environ.get("_FT_LIB_", os.path.join(ft_dir, "objs", ".libs"))
        ft_inc_dir = os.environ.get("_FT_INC_", os.path.join(ft_dir, "include"))
        setup = os.path.join(recipe_dir, "setup.py")
        if os.path.isfile(setup):
            text = open(setup, "r", encoding="utf-8").read()
            text = text.replace("_FT_LIB_", ft_lib_dir).replace("_FT_INC_", ft_inc_dir)
            open(setup, "w", encoding="utf-8").write(text)
        touch(os.path.join(recipe_dir, ".patched"))

recipe = ReportLabRecipe()
