import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.stub.StreamObserver;

import java.io.IOException;
import java.util.*;
import java.util.logging.Logger;

import static java.lang.Math.abs;

public class ServiceServer {

    private static final Logger logger = Logger.getLogger(ServiceServer.class.getName());
    private Server server;
    private static Map<ServiceOuterClass.Currency, Double> exchange = new HashMap<>();
    private Random rand = new Random();

    ServiceServer() {
        super();
        exchange.put(ServiceOuterClass.Currency.EUR, 4.0);
        exchange.put(ServiceOuterClass.Currency.USD, 5.0);
        exchange.put(ServiceOuterClass.Currency.PLN, 3.0);
    }

    public void valueUpdate(){
        List<ServiceOuterClass.Currency> updated = new LinkedList<>();
        for (Map.Entry<ServiceOuterClass.Currency, Double> entry: exchange.entrySet()){
            Double changeFactor = 1 + this.rand.nextFloat()*0.2 - 0.1;
            if(abs(changeFactor) - 1 > 0.05) {
                exchange.put(entry.getKey(), entry.getValue() * changeFactor);
                updated.add(entry.getKey());
            }
        }
    }


    private void start() throws IOException {
        /* The port on which the server should run */
        int port = 50051;
        server = ServerBuilder.forPort(port)
                .addService(new ServiceImpl())
                .build()
                .start();
        logger.info("ServiceServer started, listening on " + port);
        Runtime.getRuntime().addShutdownHook(new Thread() {
            @Override
            public void run() {
                System.err.println("*** shutting down gRPC server since JVM is shutting down");
                ServiceServer.this.stop();
                System.err.println("*** server shut down");
            }
        });
    }

    private void trackCurrencies(){
        CurrencyUpdater updater = new CurrencyUpdater(this);
        Thread updaterThread = new Thread(updater);
        updaterThread.start();
    }

    private void stop() {
        if (server != null) {
            server.shutdown();
        }
    }

    private void blockUntilShutdown() throws InterruptedException {
        if (server != null) {
            server.awaitTermination();
        }
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        final ServiceServer server = new ServiceServer();
        server.start();
        server.trackCurrencies();
        server.blockUntilShutdown();
    }

    static class ServiceImpl extends ServiceGrpc.ServiceImplBase {

        private void streamCurrency(StreamObserver<ServiceOuterClass.CurrencyRate> responseObserver,
                                      ServiceOuterClass.Currency currency,
                                      Double rate){
            ServiceOuterClass.CurrencyRate currencyRate =
                    ServiceOuterClass.CurrencyRate.newBuilder()
                            .setCurrency(currency)
                            .setRate(rate)
                            .build();
            responseObserver.onNext(currencyRate);
        }

        @Override
        public void subscribeCurrency(ServiceOuterClass.CurrencySubscription req, StreamObserver<ServiceOuterClass.CurrencyRate> responseObserver) {
            Map<ServiceOuterClass.Currency, Double> previousValues;
            Map<ServiceOuterClass.Currency, Double> currentValues = new HashMap<>(exchange);
            for (ServiceOuterClass.Currency currency : req.getRequestedList()) {
                Double rate = currentValues.get(currency);
                streamCurrency(responseObserver, currency, rate);
            }
            previousValues = currentValues;
            while(true) {
                System.out.println(currentValues);
                try {
                    Thread.sleep(1000);
                } catch (Exception e) {
                    e.printStackTrace();
                }
                currentValues = new HashMap<>(exchange);
                for (ServiceOuterClass.Currency currency : req.getRequestedList()) {
                    Double currentRate = currentValues.get(currency);
                    Double previousRate = previousValues.get(currency);
                    if(previousRate.compareTo(currentRate) != 0) {
                        streamCurrency(responseObserver, currency, currentRate);
                    }
                }
                previousValues = currentValues;
            }
        }
    }
}
