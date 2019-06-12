package nl.sublim.otto;

import android.util.Log;

import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.After;

import nl.sublim.otto.HelloWorld;

import target.application.namespace.*;

@Aspect
public class SayHello {
	@After("execution(* target.application.namespace.MainActivity.onCreate(..))")
	public void Inject(JoinPoint joinPoint) {
		Log.i("SayHello", "Calling HelloWorld.sayHello()");
		HelloWorld.sayHello(target.application.namespace.Core.getApp().getApplicationContext());
	}
}
