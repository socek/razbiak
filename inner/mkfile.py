from os import mkdir

from pymk.task import Task
from pymk.recipe import Recipe
from pymk.dependency import AlwaysRebuild


class RazbiakInnerRecipe(Recipe):

    default_task = 'install'

    def create_settings(self):
        super(RazbiakInnerRecipe, self).create_settings()
        self.set_path('flags', 'flags')


class FlagsDir(Task):

    dependencys = []

    @property
    def output_file(self):
        return self.paths['flags']

    def build(self):
        mkdir(self.output_file)


class Install(Task):

    name = 'install'
    dependencys = [
        FlagsDir.dependency_FileExists(),
        AlwaysRebuild(),
    ]

    def build(self):
        print 'building'
