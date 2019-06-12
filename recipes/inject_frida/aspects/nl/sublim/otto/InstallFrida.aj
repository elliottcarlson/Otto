package nl.sublim.otto;

import android.util.Log;
import java.util.Arrays;
import java.util.Calendar;

import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;
import target.apk.namespace.MainActivity.*;

@Aspect
public class InstallFrida {
	@Before("execution(* target.apk.namespace.MainActivity.onCreate(..))")
	public void Inject(JoinPoint joinPoint) {
		System.loadLibrary("frida-gadget");
	}
}
