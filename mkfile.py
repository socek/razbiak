# encoding: utf8
from os import mkdir
from shutil import copy

from pymk.dependency import FileChanged, FileDoesNotExists, AlwaysRebuild
from pymk.extra import run
from pymk.recipe import Recipe
from pymk.task import Task
from pymk.error import CommandAborted


class Razbiak(Recipe):

    def create_settings(self):
        super(Razbiak, self).create_settings()
        self.settings['image'] = {
            'blocksize': 512,
            'partition_offset': 188416,
        }
        self.settings['image_address'] = self.settings['image'][
            'blocksize'] * self.settings['image']['partition_offset']
        self.set_setting('pi_host', 'rouge')
        self.set_setting('pi_login', 'root')

        self.set_path('source_img', 'source.img')
        self.set_path('destination_img', 'destination.img')
        self.set_path('mount_dir', 'place')
        self.set_path('mounted_test', ['%(mount_dir)s', 'home'])
        self.set_path('mounted_innerfiles', ['%(mount_dir)s', 'inner'])
        self.set_path('mounted_innerfiles_mkfile', [
                      '%(mounted_innerfiles)s', 'mkfile.py'])
        self.set_path('device', '/dev/mmcblk0')
        self.set_path('mounted_ssh_keys', [
                      '%(mount_dir)s', 'root', '.ssh'
                      ])
        self.set_path('mounted_authorized_keys', [
                      '%(mounted_ssh_keys)s', 'authorized_keys',
                      ])
        self.set_path('public_key', '~/.ssh/id_rsa.pub')
        self.set_path('remote_inner', '/inner/')
        self.set_path('remote_initscript', ['%(remote_inner)s', 'initscript'])


class CopyImage(Task):

    hide = True

    @property
    def output_file(self):
        return self.paths['destination_img']

    @property
    def dependencys(self):
        return [
            FileChanged(self.paths['source_img']),
            FileDoesNotExists(self.paths['destination_img']),
        ]

    def build(self):
        print 'Copying...'
        copy(
            self.paths['source_img'],
            self.paths['destination_img'])


class CreateMountDir(Task):

    hide = True
    dependencys = []

    @property
    def output_file(self):
        return self.paths['mount_dir']

    def build(self):
        mkdir(self.output_file)


class MountImage(Task):

    hide = True

    @property
    def output_file(self):
        return self.paths['mounted_test']

    @property
    def dependencys(self):
        return [
            CreateMountDir.dependency_FileExists(),
            CopyImage.dependency_FileExists(),
        ]

    def build(self):
        data = dict(self.settings)
        data.update(self.paths)
        run(
            'sudo mount -o loop,offset=%(image_address)d %(destination_img)s %(mount_dir)s' % data)


class InnerDirectory(Task):

    hide = True
    dependencys = [
        MountImage.dependency_FileExists(),
    ]

    @property
    def output_file(self):
        return self.paths['mounted_innerfiles']

    def build(self):
        run('sudo mkdir %s' % (self.output_file,))
        run('sudo chmod 777 %s' % (self.output_file,))


class CopyInnerFiles(Task):
    hide = True

    @property
    def dependencys(self):
        return [
            InnerDirectory.dependency_FileChanged(),
            FileChanged(['inner/mkfile.py', 'inner/initscript']),
        ]

    @property
    def output_file(self):
        return self.paths['mounted_innerfiles_mkfile']

    def build(self):
        run('cp -r inner/* %s' % (InnerDirectory().output_file,))


class CreateSshDir(Task):
    hide = True

    @property
    def dependencys(self):
        return [
            CopyInnerFiles.dependency_FileExists(),
        ]

    @property
    def output_file(self):
        return self.paths['mounted_ssh_keys']

    def build(self):
        run('sudo mkdir %s' % (self.output_file,))
        run('sudo chmod 700 %s' % (self.output_file,))


class CopySshKeys(Task):

    name = 'image'

    dependencys = [
        CreateSshDir.dependency_FileExists(),
    ]

    @property
    def output_file(self):
        return self.paths['mounted_authorized_keys']

    def build(self):
        run('sudo cp %(public_key)s %(mounted_authorized_keys)s' % self.paths)
        run('sudo chmod 700 %s' % (self.output_file,))


class Deploy(Task):
    name = 'deploy'

    dependencys = [
        CopySshKeys.dependency_FileExists(),
        AlwaysRebuild(),
    ]

    def build(self):
        data = raw_input(
            'Are you sure you want to override %(device)s ? ' % self.paths)
        if not data.strip().lower() == 'yes':
            raise CommandAborted()
        print 'Copying...'
        run('sudo dd if=%(destination_img)s of=%(device)s' % self.paths)


class RunViaSsh(Task):
    name = 'ssh'

    dependencys = [
        AlwaysRebuild(),
    ]

    def build(self):
        data = dict(self.settings)
        data.update(self.paths)
        run('ssh %(pi_login)s@%(pi_host)s -t "%(remote_initscript)s"' %data)
