from __future__ import print_function

from enigma import eTimer

from Components.config import config, ConfigSubsection, ConfigText, ConfigYesNo
from Components.Console import Console
from Plugins.Plugin import PluginDescriptor

from . import _, svg_support
from .Softcam import checkconfigdir, getcamcmd, stopcam


config.plugins.AltSoftcam = ConfigSubsection()
config.plugins.AltSoftcam.actcam = ConfigText(default="none")
config.plugins.AltSoftcam.camconfig = ConfigText(default="/var/keys",
		visible_width=100, fixed_size=False)
config.plugins.AltSoftcam.camdir = ConfigText(default="/var/emu",
		visible_width=100, fixed_size=False)
config.plugins.AltSoftcam.restartext = ConfigYesNo(default=True)


checkconfigdir()


class StartCamOnStart():
	def __init__(self):
		self.Console = Console()
		self.Timer = eTimer()
		self.Timer.timeout.callback.append(self.camnotrun)
		self.Timer.start(2000, True)

	def start(self):
		self.Timer.start(2000, True)

	def camnotrun(self):
		self.Console.ePopen("ps", self.checkprocess)

	def checkprocess(self, result, retval, extra_args):
		processes = result.decode("utf-8").lower()
		camlist = ["oscam", "mgcamd", "wicard", "camd3", "mcas", "cccam",
				"gbox", "mpcs", "mbox", "newcs", "vizcam", "rucam"]
		camlist.insert(0, config.plugins.AltSoftcam.actcam.value)
		for cam in camlist:
			if cam in processes:
				print("[Alternative SoftCam Manager] ERROR in start cam! In processes find", cam)
				break
		else:
			cmd = getcamcmd(config.plugins.AltSoftcam.actcam.value)
			print("[Alternative SoftCam Manager]", cmd)
			Console().ePopen(cmd)


startcamonstart = StartCamOnStart()


def main(session, **kwargs):
	from .Manager import AltCamManager
	session.open(AltCamManager)


def restartcam(session, **kwargs):
	cam = config.plugins.AltSoftcam.actcam.value
	if cam != "none":
		from Screens.MessageBox import MessageBox
		session.open(MessageBox, _("Restarting %s") % cam,
				type=MessageBox.TYPE_INFO, timeout=4)
		stopcam(cam)
		service = session.nav.getCurrentlyPlayingServiceReference()
		if service:
			session.nav.stopService()
		cmd = getcamcmd(cam)
		print("[Alternative SoftCam Manager]", cmd)
		Console().ePopen(cmd)
		if service:
			session.nav.playService(service)


EnigmaStart = False


def startcam(reason, **kwargs):
	if config.plugins.AltSoftcam.actcam.value != "none":
		global EnigmaStart
		if reason == 0 and not EnigmaStart:  # Enigma start and not use reloadPlugins
			EnigmaStart = True
			startcamonstart.start()
		elif reason == 1:  # Enigma stop
			stopcam(config.plugins.AltSoftcam.actcam.value)


def Plugins(**kwargs):
	plugin_list = [PluginDescriptor(
			name=_("Alternative SoftCam Manager"),
			description=_("Start, stop, restart SoftCams, change settings."),
			where=[PluginDescriptor.WHERE_PLUGINMENU,
					PluginDescriptor.WHERE_EXTENSIONSMENU],
			icon="images/softcam.%s" % ("svg" if svg_support else "png"),
			fnc=main),
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			needsRestart=True,
			fnc=startcam)]

	if config.plugins.AltSoftcam.restartext.value:
		plugin_list.append(PluginDescriptor(
				name=_("Restart softcam"),
				where=PluginDescriptor.WHERE_EXTENSIONSMENU,
				fnc=restartcam))

	return plugin_list
