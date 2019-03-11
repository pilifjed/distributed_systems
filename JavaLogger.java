import java.io.File;
import java.io.FileOutputStream;
import java.io.PrintWriter;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.Arrays;

public class JavaLogger {

    public static void main(String args[])
    {
        System.out.println("JAVA LOGGER");
        DatagramSocket socket = null;
        int portNumber = 8080;

        try{
            socket = new DatagramSocket(portNumber, InetAddress.getByName("127.0.0.1"));
            byte[] receiveBuffer = new byte[1024];

            while(true) {
                Arrays.fill(receiveBuffer, (byte)0);
                DatagramPacket receivePacket = new DatagramPacket(receiveBuffer, receiveBuffer.length);
                socket.receive(receivePacket);
                String msg = new String(receivePacket.getData());
                System.out.println("LOG: " + msg);
                PrintWriter writer = new PrintWriter(new FileOutputStream(new File("log.txt"), true));
                writer.println("LOG: " + msg);
                writer.close();
            }
    }
        catch(Exception e){
            e.printStackTrace();
        }
        finally {
            if (socket != null) {
                socket.close();
            }
        }
    }
}