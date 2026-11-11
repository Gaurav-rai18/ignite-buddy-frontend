"""Things policy never allows. Matching them here gives a deterministic refusal instead of a model guess."""
from ..model import Refuse
from ..parser import rule

_MSG = "I'm not allowed to format disks, install software or edit the registry."


@rule(r"(?:delete|remove|erase|wipe)\s+(?:(?:all|every|of|the|my)\s+)+(?:files|folders|directories)\b.*"
      r"|(?:delete|remove|erase|wipe)\s+(?:files|folders)\b.*",
      examples=("delete all my files",))
def _no_mass_delete(m, b):
    raise Refuse("I won't delete files or folders in bulk. Name one file or folder if your administrator allows deleting.")


@rule(r"format\s+(?:the\s+|my\s+)?(?:disk|drive|hard drive|c:).*")
def _no_format(m, b):
    raise Refuse(_MSG)


@rule(r"(?:install|uninstall)\s+(?:the\s+|a\s+|an\s+)?(?:software|app|application|program)\b.*")
def _no_install(m, b):
    raise Refuse(_MSG)


@rule(r"(?:edit|change|modify|open)\s+(?:the\s+|my\s+)?registry.*")
def _no_registry(m, b):
    raise Refuse(_MSG)
