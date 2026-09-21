from pythonforandroid.recipe import PythonRecipe

class ReportLabRecipe(PythonRecipe):
    version = "3.6.13"
    # Use the official PyPI source archive; the GitHub mirror tag URL returns 404.
    url = "https://files.pythonhosted.org/packages/source/r/reportlab/reportlab-{version}.tar.gz"
    depends = ["python3"]
    call_hostpython_via_targetpython = False

recipe = ReportLabRecipe()
