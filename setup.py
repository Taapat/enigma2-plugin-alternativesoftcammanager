from distutils.core import setup
import setup_translate


setup(name='enigma2-plugin-extensions-alternativesoftcammanager',
		version='1.0',
		author='Taapat',
		author_email='taapat@gmail.com',
		package_dir={'Extensions.AlternativeSoftCamManager': 'src'},
		packages=['Extensions.AlternativeSoftCamManager'],
		package_data={'Extensions.AlternativeSoftCamManager': ['images/*.png']},
		description='Start, stop, restart SoftCams, change setting path',
		cmdclass=setup_translate.cmdclass,
	)

