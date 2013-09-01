from shutil import copyfile
from os import mkdir, path

from pymk.modules import BaseRecipe
from pymk.task import Task
from pymk.dependency import FileChanged, FileDoesNotExists
from pymk.extra import run_cmd


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


class CopyImage(Task):

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
        copyfile(
            self.settings['source_img_path'],
            self.settings['destination_img_path'])


class CreateMountDir(Task):
    dependencys = []

    @property
    def output_file(self):
        return self.settings['mount_dir']

    def build(self):
        mkdir(self.settings['mount_dir'])


class MountImage(Task):

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