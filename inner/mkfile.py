from os import mkdir

from pymk.task import Task
from pymk.recipe import Recipe
from pymk.dependency import AlwaysRebuild
from pymk.extra import run, touch


class RazbiakInnerRecipe(Recipe):

    default_task = 'install'

    def create_settings(self):
        super(RazbiakInnerRecipe, self).create_settings()
        self.set_path('flags', 'flags')

        # bin
        self.set_path('pacman', '/usr/bin/pacman')
        self.set_path('yaourt', '/usr/bin/yaourt')
        self.set_path('xbmc', '/usr/bin/xbmc')
        self.set_path('startx', '/usr/bin/startx')
        self.set_path('X', '/usr/bin/X')

        # conf
        self.set_path('pacman_conf', '/etc/pacman.conf')

        # drivers
        self.set_path('xf86-video-fbdev', '/usr/lib/xorg/modules/drivers/fbdev_drv.so')

        # flag
        self.set_path('pacman_conf_flag', ['%(flags)s', 'pacman.conf'])
        self.set_path('xbmc_start_at_boot', ['%(flags)s', 'xbmc'])


class InstallTask(Task):
    base = True

    package_name = None

    def build(self):
        run('yaourt -S --noconfirm %s' % (self.package_name,))


class FlagTask(Task):
    base = True

    flag_name = None

    @property
    def output_file(self):
        return self.paths[self.flag_name]

    def build(self):
        self.build_flag()
        touch(self.output_file)


class FlagsDir(Task):

    dependencys = []

    @property
    def output_file(self):
        return self.paths['flags']

    def build(self):
        mkdir(self.output_file)


class PacmanConf(FlagTask):

    dependencys = []
    flag_name = 'pacman_conf_flag'

    def build_flag(self):
        fp = open(self.paths['pacman_conf'], 'a')
        fp.write('''
[aur]
Include = /etc/pacman.d/mirrorlist
''')


class UpdatePacman(FlagTask):
    dependencys = [
        FlagsDir.dependency_FileChanged(),
        PacmanConf.dependency_FileChanged(),
    ]

    flag_name = 'pacman'

    def build_flag(self):
        run('pacman -Syu --noconfirm')


class YaourtInstall(Task):
    dependencys = [
        UpdatePacman.dependency_FileExists(),
    ]

    @property
    def output_file(self):
        return self.paths['yaourt']

    def build(self):
        run('pacman -S yaourt --noconfirm')

class VideDriver(InstallTask):
    dependencys = [
        YaourtInstall.dependency_FileExists(),
    ]
    package_name = 'xf86-video-fbdev'

    @property
    def output_file(self):
        return self.paths['xf86-video-fbdev']

class Xorg(InstallTask):
    dependencys = [
        YaourtInstall.dependency_FileExists(),
    ]

    package_name = 'xorg-server'

    @property
    def output_file(self):
        return self.paths['X']

class XorgInit(InstallTask):
    dependencys = [
        Xorg.dependency_FileExists(),
    ]

    package_name = 'xorg-xinit'

    @property
    def output_file(self):
        return self.paths['startx']


class Xbmc(InstallTask):
    dependencys = [
        YaourtInstall.dependency_FileExists(),
        VideDriver.dependency_FileExists(),
        XorgInit.dependency_FileExists(),
    ]

    package_name = 'xbmc'

    @property
    def output_file(self):
        return self.paths['xbmc']


class StartXbmcAtBoot(FlagTask):
    dependencys = [
        Xbmc.dependency_FileExists(),
    ]
    flag_name = 'xbmc_start_at_boot'

    def build_flag(self):
        run('systemctl enable xbmc')


class Install(Task):

    name = 'install'
    dependencys = [
        StartXbmcAtBoot.dependency_Link(),
        AlwaysRebuild(),
    ]

    def build(self):
        print 'building'
