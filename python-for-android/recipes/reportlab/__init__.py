from pythonforandroid.recipe import PythonRecipe

class ReportLabRecipe(PythonRecipe):
    # 3.6.13 is the first ReportLab release after the 2023 security fix.
    # Use the public Git mirror tag directly; the old 3.3.0 tag does not exist
    # on the mirror and caused the Android build to fail with HTTP 404.
    version = "3.6.13"
    url = "https://github.com/MrBitBucket/reportlab-mirror/archive/refs/tags/{version}.tar.gz"
    depends = ["python3"]
    call_hostpython_via_targetpython = False

recipe = ReportLabRecipe()
