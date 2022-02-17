from os import environ
from gettext import bindtextdomain, dgettext, gettext

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS


def localeInit():
	environ["LANGUAGE"] = language.getLanguage()[:2]
	bindtextdomain("AlternativeSoftCamManager", resolveFilename(SCOPE_PLUGINS,
			"Extensions/AlternativeSoftCamManager/locale"))


def _(txt):
	t = dgettext("AlternativeSoftCamManager", txt)
	if t == txt:
		t = gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)


try:
	# Check functions for full svg and scaling support
	from enigma import loadSVG  # noqa: F401
	from skin import applySkinFactor  # noqa: F401
	svg_support = True
except ImportError:
	svg_support = False
