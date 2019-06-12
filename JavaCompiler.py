import os
from pathlib import Path
import platform
import subprocess

class JavaCompiler:
    def __init__(self, srcdir, dstdir):
        self.srcdir = os.path.abspath(srcdir)
        self.dstdir = os.path.abspath(dstdir)
        self.__classpath = []
        self.__baseclasspath = []
        self.baseclasspath = sorted(list(map(str, Path(os.environ.get('ANDROID_HOME')).glob('platforms/*'))), reverse=True)[0]
        self.__sourcefiles = list(map(str, Path(self.srcdir).glob('**/*.java')))
        self.__options = ['-g:none', '-Xlint:unchecked']

    @property
    def classpath(self):
        return self.__classpath

    @classpath.setter
    def classpath(self, path):
        self.__classpath = list(map(str, Path(os.path.abspath(path)).glob('**/*.jar')))

    @property
    def baseclasspath(self):
        return self.__baseclasspath

    @baseclasspath.setter
    def baseclasspath(self, path):
        self.__baseclasspath = list(map(str, Path(os.path.abspath(path)).glob('*.jar')))

    @property
    def java_executable(self):
        ext = ''
        if (platform.system() == 'Windows'):
            ext = '.exe'
        return os.path.join(os.environ.get('JAVA_HOME'), 'bin', 'javac{0}'.format(ext))

    def exec(self):
        command = [
            self.java_executable,
            '-d',
            self.dstdir,
            '-classpath',
            ';'.join(self.classpath),
            '-sourcepath',
            self.srcdir,
            '-bootclasspath',
            ';'.join(self.baseclasspath),
        ] + self.__options + self.__sourcefiles
        ret = subprocess.check_call(command, stdout=subprocess.DEVNULL)