package nl.sublim.otto;

import android.widget.Toast;
import android.content.Context;

public class HelloWorld {
    public static void sayHello(Context AppContext) {
        Toast.makeText(AppContext, "Hello World", Toast.LENGTH_SHORT).show();
    }
}
