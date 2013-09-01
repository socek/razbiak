from os import mkdir

from pymk.task import Task
from pymk.modules import BaseRecipe


class RazbiakInnerRecipe(BaseRecipe):

    def create_settings(self):
        super(RazbiakInnerRecipe, self).create_settings()
        self.settings['flags'] = 'flags'


class FlagsDir(Task):

    dependencys = []

    @property
    def output_file(self):
        return self.settings['flags']

    def build(self):
        mkdir(self.output_file)
