import os
from pathlib import Path
import platform
import subprocess

class AspectJWeaver:
    def __init__(self, srcdir, codedir, dstdir):
        self.srcdir = os.path.abspath(srcdir) # Location os aspect files
        self.codedir = os.path.abspath(codedir) # Code to weave aspect files in
        self.dstdir = os.path.abspath(dstdir) # Output directory
        self.__source = "1.9"
        self.__target = "1.9"
        self.__classpath = []
        self.classpath = sorted(list(map(str, Path(os.environ.get('ANDROID_HOME')).glob('platforms/*'))), reverse=True)[0]
        self.__sourcefiles = list(map(str, Path(self.srcdir).glob('**/*.java')))
        self.__options = ['-Xlint:ignore']


    @property
    def classpath(self):
        return self.__classpath

    @classpath.setter
    def classpath(self, path):
        self.__classpath = self.__classpath + list(map(str, Path(os.path.abspath(path)).glob('**/*.jar')))

    @property
    def java_executable(self):
        ext = ''
        if (platform.system() == 'Windows'):
            ext = '.exe'
        return os.path.join(os.environ.get('JAVA_HOME'), 'bin', 'java{0}'.format(ext))

    def exec(self):
        command = [
            self.java_executable,
            '-classpath',
            ';'.join(self.classpath),
            'org.aspectj.tools.ajc.Main',
            '-sourceroots',
            self.srcdir,
            '-inpath',
            self.codedir,
            '-d',
            self.dstdir,
            '-source',
            self.__source,
            '-target',
            self.__target,
        ] + self.__options
        ret = subprocess.check_call(command, stdout=subprocess.DEVNULL)