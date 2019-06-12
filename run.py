#!/usr/bin/env python3
"""
Otto -- Inject code and perform AOP modifications to an APK file.
"""

import argparse, os, sys, errno, shutil, subprocess, platform
from halo import Halo
from JavaCompiler import JavaCompiler
from AspectJWeaver import AspectJWeaver
from pathlib import Path
from distutils.dir_util import copy_tree
if sys.version_info >= (3, 6):
    import zipfile
else:
    import zipfile36 as zipfile

class Otto:
    def __init__(self, config):
        ''' Constructor. '''
        self.config = config
        self.root = os.path.dirname(os.path.realpath(__file__))
        self.base_apk = os.path.basename(self.config.apk_file)
        if (platform.system() == 'Windows'):
            self.shell_ext = '.bat'
            self.exec_ext = '.exe'
        else:
            self.shell_ext = '.sh'
            self.exec_ext = ''


        print('Performing initial setup of build environment...')
        self.setup()

        print('Decoding APK file...')
        self.decode()

        print('Compile and inject recipe classes...')
        self.compile()
        
        print('Weaving AOP aspects in to APK classes...')
        self.weave()

        print('Repackaging APK file...')
        self.repackage()

        print('Done.')

    def setup(self):
        ''' Set up the build environment with the extracted APK '''
        build_dir = os.path.join(self.root, 'build')

        if os.path.isdir(build_dir):
            shutil.rmtree(build_dir)

        with Halo(text='Creating build directory structure...', spinner='dots') as spinner:
            os.mkdir(build_dir)
            os.mkdir(os.path.join(build_dir, 'output'))
            os.mkdir(os.path.join(build_dir, 'staging'))
            os.mkdir(os.path.join(build_dir, 'decoded'))
            spinner.succeed()

        with Halo(text='Extracting {0}...'.format(self.base_apk), spinner='dots') as spinner:
            zf = zipfile.ZipFile(self.config.apk_file, 'r')
            zf.extractall(os.path.join(build_dir, 'staging'))
            zf.close()

            meta_inf = os.path.join(build_dir, 'staging', 'META-INF')
            if os.path.isdir(meta_inf):
                shutil.rmtree(meta_inf)
            spinner.succeed()

    def decode(self):
        ''' Convert the extracted APK to JAR files. '''
        jar_file = os.path.join(self.root, 'build', 'tmp', 'decoded.jar')

        with Halo(text='Converting {0} via dex2jar...'.format(self.base_apk ), spinner='dots') as spinner:
            try:
                ret = subprocess.check_call([
                    os.path.join(self.root, 'tools', 'dex2jar', 'd2j-dex2jar{0}'.format(self.shell_ext)),
                    '-f',
                    '-o',
                    jar_file,
                    self.config.apk_file
                ], stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                spinner.fail('dex2jar returned a non-zero exit status: {0}'.format(e.returncode))
                sys.exit(e.returncode)
            finally:
                spinner.succeed()


        with Halo(text='Verifying jar...'.format(self.base_apk ), spinner='dots') as spinner:
            try:
                ret = subprocess.check_call([
                    os.path.join(self.root, 'tools', 'dex2jar', 'd2j-asm-verify{0}'.format(self.shell_ext)),
                    jar_file
                ], stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                spinner.fail('asm-verify returned a non-zero exit status: {0}'.format(e.returncode))
                sys.exit(e.returncode)
            finally:
                spinner.succeed()

        with Halo(text='Extracting jar file...', spinner='dots') as spinner:
            zf = zipfile.ZipFile(jar_file, 'r')
            zf.extractall(os.path.join(self.root, 'build', 'decoded'))
            zf.close()
            spinner.succeed()

    def compile(self):
        ''' Compile the custom Java files. '''
        code_path = os.path.join(self.root, 'build', 'tmp', 'code')

        with Halo(text='Copying decoded java files...', spinner='dots') as spinner:
            shutil.copytree(os.path.join(self.root, 'build', 'decoded'), code_path)

        if not bool(sorted(Path(os.path.join(self.config.recipe_dir, 'source')).rglob('*'))):
            print('Skipping code compilation - no custom classes found in recipe source.')
            return

        with Halo(text='Compiling custom classes...'.format(self.base_apk ), spinner='dots') as spinner:
            try:
                compiler = JavaCompiler(os.path.join(self.config.recipe_dir, 'source'), code_path)
                compiler.classpath = os.path.join(self.root, 'tools', 'aspectj')
                compiler.exec()
                spinner.succeed()
            except Exception as e:
                spinner.fail('asm-verify returned a non-zero exit status: {0}'.format(e))
                sys.exit(1)

    def weave(self):
        ''' Weave AOP aspects in to the existing code base. '''
        with Halo(text='Weaving aspect files...', spinner='dots') as spinner:
            weaver = AspectJWeaver(
                srcdir=os.path.join(self.config.recipe_dir, 'aspects'),
                codedir=os.path.join(self.root, 'build', 'tmp', 'code'),
                dstdir=os.path.join(self.root, 'build', 'tmp', 'woven')
            )
            weaver.classpath = os.path.join(self.root, 'tools', 'aspectj')
            weaver.exec()

            os.mkdir(os.path.join(self.root, 'build', 'tmp', 'woven', 'libs'))
            shutil.copyfile(
                os.path.join(self.root, 'tools', 'aspectj', 'aspectjrt.jar'), 
                os.path.join(self.root, 'build', 'tmp', 'woven', 'libs', 'aspectjrt.jar')
            )

    def repackage(self):
        build_tools = sorted(list(map(str, Path(os.environ.get('ANDROID_HOME')).glob('build-tools/*'))), reverse=True)[0]
        dx_exec = os.path.join(build_tools, 'dx{0}'.format(self.shell_ext))

        with Halo(text='Converting .java files to .dex...', spinner='dots') as spinner:
            Path(os.path.join(self.root, 'build', 'tmp', 'dex')).mkdir(exist_ok=True)

            try:
                ret = subprocess.check_call([
                    os.path.join(build_tools, 'dx{0}'.format(self.shell_ext)),
                    '--dex',
                    '--no-locals',
                    '--min-sdk-version=28',
                    '--output',
                    os.path.join(self.root, 'build', 'tmp', 'dex', 'classes.dex'),
                    os.path.join(self.root, 'build', 'tmp', 'woven')
                ], stdout=subprocess.DEVNULL)
                spinner.succeed()
            except subprocess.CalledProcessError as e:
                spinner.fail('asm-verify returned a non-zero exit status: {0}'.format(e.returncode))
                sys.exit(e.returncode)

            os.remove(os.path.join(self.root, 'build', 'staging', 'classes.dex'))
            shutil.copyfile(
                os.path.join(self.root, 'build', 'tmp', 'dex', 'classes.dex'),
                os.path.join(self.root, 'build', 'staging', 'classes.dex')
            )

        with Halo(text='Copying library files...', spinner='dots') as spinner:
            copy_tree(os.path.join(self.config.recipe_dir, 'libraries'), os.path.join(self.root, 'build', 'staging', 'lib'))
            spinner.succeed()

        with Halo(text='Packaging APK...', spinner='dots') as spinner:
            base_path = os.path.join(self.root, 'build', 'staging')
            zf = zipfile.ZipFile(os.path.join(self.root, 'build', 'tmp', 'app_unsigned.apk'), "w")
            for dirname, subdirs, files in os.walk(base_path):
                if dirname == '.':
                    continue
                zf.write(dirname, os.path.relpath(dirname, base_path))
                for filename in files:
                    real_file = os.path.join(dirname, filename)
                    zf.write(real_file, os.path.relpath(real_file, base_path))
            zf.close()
            spinner.succeed()

        with Halo(text='Signing APK...', spinner='dots') as spinner:
            try:
                ret = subprocess.check_call([
                    os.path.join(self.config.java_home, 'bin', 'jarsigner{0}'.format(self.exec_ext)),
                    '-sigalg',
                    'SHA1withRSA',
                    '-digestalg',
                    'SHA1',
                    '-keystore',
                    self.config.key_store,
                    '-storepass',
                    self.config.key_store_password,
                    '-tsa',
                    'http://timestamp.comodoca.com/rfc3161',
                    os.path.join(self.root, 'build', 'tmp', 'app_unsigned.apk'),
                    self.config.key_store_alias
                ], stdout=subprocess.DEVNULL)
                spinner.succeed()
            except subprocess.CalledProcessError as e:
                spinner.fail('asm-verify returned a non-zero exit status: {0}'.format(e.returncode))
                sys.exit(e.returncode)

        with Halo(text='Aligning APK...', spinner='dots') as spinner:
            build_tools = sorted(list(map(str, Path(os.environ.get('ANDROID_HOME')).glob('build-tools/*'))), reverse=True)[0]
            zipalign_exec = os.path.join(build_tools, 'zipalign{0}'.format(self.exec_ext))
            try:
                ret = subprocess.check_call([
                    zipalign_exec,
                    '4',
                    os.path.join(self.root, 'build', 'tmp', 'app_unsigned.apk'),
                    os.path.join(self.root, 'build', 'tmp', 'app_signed.apk')
                ], stdout=subprocess.DEVNULL)
                spinner.succeed()
            except subprocess.CalledProcessError as e:
                spinner.fail('asm-verify returned a non-zero exit status: {0}'.format(e.returncode))
                sys.exit(e.returncode)

if __name__ == '__main__':
    def to_absolute_path(path):
        if os.access(os.path.abspath(path), os.R_OK):
            return os.path.abspath(path)

        raise Exception 

    parser = argparse.ArgumentParser(
        description='Inject an Otto recipe folder in to an APK file.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('apk_file',
        help='The APK file that you want to alter.',
        type=to_absolute_path
 	)

    parser.add_argument('recipe_dir',
        help='The directory of the recipe you want to inject.',
        type=to_absolute_path
    )

    parser.add_argument('-java-home',
        help='The path to the JDK.',
        metavar='PATH',
        default=os.getenv('JAVA_HOME'),
        type=to_absolute_path
    )

    parser.add_argument('-android-sdk',
        help=('The path to the Android SDK.'),
        metavar='PATH',
        default=os.getenv('ANDROID_HOME'),
        type=to_absolute_path
    )

    parser.add_argument('-key-store',
        help=('The keystore used to sign the output APK.'),
        metavar='FILE',
        default=to_absolute_path('test_key_store.jks'),
        type=to_absolute_path
    )

    parser.add_argument('-key-store-password',
        help=('The password to the key store.'),
        metavar='PASSWORD',
        default='password'
    )

    parser.add_argument('-key-store-alias',
        help=('The alias to use in the key store'),
        metavar='NAME',
        default='test_alias'
    )

    parser.add_argument('-key-store-alias-password',
        help=('The password of the alias in the key store.'),
        metavar='PASSWORD',
        default='password'
    )

    args = parser.parse_args()
    app = Otto(args)
