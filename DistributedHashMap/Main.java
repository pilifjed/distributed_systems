import java.util.Scanner;

public class Main {
    public static void main(String args[]) throws Exception{
        System.setProperty("java.net.preferIPv4Stack","true");
        DistributedMap map = new DistributedMap("MyCluster");
        Scanner scanner = new Scanner(System.in);
        String currentString, key;
        Integer value;
        do{
            currentString = scanner.next();
            switch(currentString){
                case "get":
                    key = scanner.next();
                    System.out.println(map.get(key));
                    break;
                case "set":
                    key = scanner.next();
                    value = scanner.nextInt();
                    map.put(key, value);
                    break;
                case "contains":
                    key = scanner.next();
                    System.out.println(map.containsKey(key));
                    break;
                case "remove":
                    key = scanner.next();
                    map.remove(key);
                    break;
                case "display":
                    map.display();
            }
        }
        while(!currentString.equals("disconnect"));
    }
}
