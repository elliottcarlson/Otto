# Otto

## About

Otto is an automated toolset for Modifying and Injecting custom code in to a third party APK file. It rests on the shoulders of giants in terms of tools it incorporates.

Otto uses `recipe` folders that contain structures for custom Java source files, AspectJ post-compile aspect weaving files, and libraries you would like to inject in to the APK.

## Examples

Note: The aspect files for these recipes uses a generic namespace as an example -- you need to change this to match your target APK's namespace for the MainActivity.


### Hello World

A `hello_world` sample recipe folder is provided. This recipe will compile a new HelloWorld.java class in to the passed in APK. This class provides a static method called sayHello().
This recipe also includes an AspectJ file, that will inject code after the MainActivity.onCreate has completed - this injected code will log a message as well as call our injected Java code.

### Inject Frida

The `inject_frida` sample recipe folder adds the `libfrida-gadget.so` file in to the APK. It then uses an AspectJ file to inject a System.load of the Frida Gadget before the MainActivity.onCreate starts.
This allows you to use Frida for further inspection of the APK during run time. Now when you load the app, it will hang until you connect with `frida -R Gadget`.

## Warning

This is very much an alpha upload, and everything has only been tested in one environment. As this project progresses, further testing will occur and additional functionality will be added.
APK's recreated in this manner have only been tested on emulators and not on physical devices.

## Instructions

```
$ python run.py target-apk.apk recipes/hello_world
```

For full help, just run

```
$ python run.py --help
```