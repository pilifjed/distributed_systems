import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.TimeUnit;


public class CurrencyUpdater implements Runnable{
    private ServiceServer serviceServer;
    private Random rand;

    CurrencyUpdater(ServiceServer serviceServer){
        this.serviceServer = serviceServer;
    }

    public void run() {
        while(true){
            serviceServer.valueUpdate();
            try{
                TimeUnit.SECONDS.sleep(5);
            }
            catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }
}
