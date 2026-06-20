"""templates/ 配下の .tmpl を string.Template で穴埋めする。"""

from pathlib import Path
from string import Template

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def render(template_name, mapping):
    text = (_TEMPLATE_DIR / template_name).read_text(encoding="utf-8")
    return Template(text).substitute(mapping)
