from enigma import eTimer
from Components.config import config
from Components.Console import Console
from Screens.MessageBox import MessageBox

from . import _
from Softcam import getcamcmd, stopcam

class RestartCam:
	def __init__(self, session):
		self.session = session

	def restart(self):
		cam = config.plugins.AltSoftcam.actcam.value
		if cam != "none":
			self.session.open(MessageBox, _("Restarting %s") % cam, 
				type = MessageBox.TYPE_INFO, timeout = 4)
			stopcam(cam)
			service = self.session.nav.getCurrentlyPlayingServiceReference()
			if service:
				self.session.nav.stopService()
			cmd = getcamcmd(cam)
			print "[Alternative SoftCam Manager]", cmd
			Console().ePopen(cmd)
			if service:
				self.session.nav.playService(service)


class StartCamOnStart:
	def __init__(self):
		self.Console = Console()
		self.Timer = eTimer()
		self.Timer.timeout.get().append(self.__camnotrun)

	def start(self):
		self.Timer.start(2000, False)

	def __camnotrun(self):
		self.Timer.stop()
		self.Console.ePopen("ps", self.checkprocess)

	def checkprocess(self, result, retval, extra_args):
		processes = result.lower()
		camlist = ["oscam", "mgcamd", "wicard", "camd3", "mcas", "cccam",
			"gbox", "mpcs", "mbox", "newcs", "vizcam", "rucam"]
		camlist.insert(0, config.plugins.AltSoftcam.actcam.value)
		for cam in camlist:
			if cam in processes:
				print "[Alternative SoftCam Manager] ERROR in start cam! In processes find:", cam
				break
		else:
			cmd = getcamcmd(config.plugins.AltSoftcam.actcam.value)
			print "[Alternative SoftCam Manager]", cmd
			Console().ePopen(cmd)

startcamonstart = StartCamOnStart()

