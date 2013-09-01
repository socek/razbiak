from os import mkdir, path
from shutil import copy

from pymk.dependency import FileChanged, FileDoesNotExists
from pymk.extra import run_cmd
from pymk.modules import BaseRecipe
from pymk.task import Task


class RazbiakRecipe(BaseRecipe):

    def create_settings(self):
        super(RazbiakRecipe, self).create_settings()
        self.settings['source_img_path'] = 'source.img'
        self.settings['destination_img_path'] = 'destination.img'
        self.settings['mount_dir'] = 'place'
        self.settings['image'] = {
            'blocksize': 512,
            'partition_offset': 188416,
        }
        self.settings['image_address'] = self.settings['image'][
            'blocksize'] * self.settings['image']['partition_offset']
        self.settings['mounted_path_test'] = path.join(
            self.settings['mount_dir'], 'home')
        self.settings['mounted_path_innerfiles'] = path.join(
            self.settings['mount_dir'], 'inner')
        self.settings['mounted_innerfile_mkfile'] = path.join(
            self.settings['mounted_path_innerfiles'], 'mkfile.py')


class CopyImage(Task):

    hide = True

    @property
    def output_file(self):
        return self.settings['destination_img_path']

    @property
    def dependencys(self):
        return [
            FileChanged(self.settings['source_img_path']),
            FileDoesNotExists(self.settings['destination_img_path']),
        ]

    def build(self):
        print 'Copying...'
        copy(
            self.settings['source_img_path'],
            self.settings['destination_img_path'])


class CreateMountDir(Task):

    hide = True
    dependencys = []

    @property
    def output_file(self):
        return self.settings['mount_dir']

    def build(self):
        mkdir(self.output_file)


class MountImage(Task):

    hide = True

    @property
    def output_file(self):
        return self.settings['mounted_path_test']

    @property
    def dependencys(self):
        return [
            CreateMountDir.dependency_FileExists(),
            CopyImage.dependency_FileExists(),
        ]

    def build(self):
        run_cmd(
            'sudo mount -o loop,offset=%(image_address)d %(destination_img_path)s %(mount_dir)s' % self.settings)


class InnerDirectory(Task):

    hide = True
    dependencys = [
        MountImage.dependency_FileExists(),
    ]

    @property
    def output_file(self):
        return self.settings['mounted_path_innerfiles']

    def build(self):
        run_cmd('sudo mkdir %s' % (self.output_file,))
        run_cmd('sudo chmod 777 %s' % (self.output_file,))


class CopyInnerFiles(Task):

    name = 'install'

    @property
    def dependencys(self):
        return [
            InnerDirectory.dependency_FileExists(),
            # FileDoesNotExists(self.output_file),
        ]

    @property
    def output_file(self):
        return self.settings['mounted_innerfile_mkfile']

    def build(self):
        run_cmd('cp -r inner/* %s' % (InnerDirectory().output_file,))
