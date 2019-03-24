import org.jgroups.*;
import org.jgroups.protocols.*;
import org.jgroups.protocols.pbcast.*;
import org.jgroups.stack.ProtocolStack;
import org.jgroups.util.Util;

import java.io.*;
import java.net.InetAddress;
import java.util.HashMap;
import java.util.List;
import java.util.Vector;


final class Put implements Serializable {
    String key;
    Integer value;

    Put(String key, Integer value) {
        this.key = key;
        this.value = value;
    }
}

final class Remove implements Serializable {
    String key;
    Remove(String key) {
        this.key = key;
    }
}

public class DistributedMap extends ReceiverAdapter implements SimpleStringMap {

    private final HashMap<String, Integer> contents;
    private JChannel channel;

    public DistributedMap(String clusterName) throws Exception {
        contents = new HashMap<>();
        channel = new JChannel(false);
        ProtocolStack stack = new ProtocolStack();
        channel.setProtocolStack(stack);
        stack.addProtocol(new UDP().setValue("mcast_group_addr", InetAddress.getByName("224.225.226.228")))
                .addProtocol(new PING())
                .addProtocol(new MERGE3())
                .addProtocol(new FD_SOCK())
                .addProtocol(new FD_ALL()
                        .setValue("timeout", 12000)
                        .setValue("interval", 3000))
                .addProtocol(new VERIFY_SUSPECT())
                .addProtocol(new BARRIER())
                .addProtocol(new NAKACK2())
                .addProtocol(new UNICAST3())
                .addProtocol(new STABLE())
                .addProtocol(new GMS())
                .addProtocol(new UFC())
                .addProtocol(new MFC())
                .addProtocol(new FRAG2())
                .addProtocol(new STATE());
        stack.init();
        channel.setReceiver(this);
        channel.setDiscardOwnMessages(true);
        channel.connect(clusterName);
        channel.getState(null,0);
    }

    private void notifyAll(Object message){
        try {
            channel.send(new Message(null, message));
        }
        catch(Exception e){
            System.err.println("Notification error\n" + e.toString());
        }
    }

    @Override
    public void viewAccepted(View view){
        if(view instanceof MergeView) {
            ViewHandler handler = new ViewHandler(this.channel, (MergeView) view);
            handler.start();
        }
    }

    @Override
    public void receive(Message msg){
        Object message = msg.getObject();
        if(message instanceof Put){
            Put p = (Put) message;
            put(p.key,p.value);
        }
        else if(message instanceof Remove){
            Remove r = (Remove) message;
            remove(r.key);
        }
    }

    @Override
    public void getState(OutputStream output) throws Exception {
        synchronized(contents) {
            Util.objectToStream(contents, new DataOutputStream(output));
        }
    }

    @Override
    public void setState(InputStream input) throws Exception {
        HashMap<String, Integer> unpackedContents;
        unpackedContents=(HashMap<String, Integer>)Util.objectFromStream(new DataInputStream(input));
        synchronized(contents){
            contents.clear();
            contents.putAll(unpackedContents);
        }
    }

    @Override
    public boolean containsKey(String key){
        return contents.containsKey(key);
    }

    @Override
    public Integer get(String key){
        return contents.get(key);
    }

    @Override
    public void put(String key, Integer value){
        notifyAll(new Put(key, value));
        contents.put(key, value);
    }

    @Override
    public Integer remove(String key){
        notifyAll(new Remove(key));
        return contents.remove(key);
    }

    public void display(){
        System.out.println(contents);
    }

    private static class ViewHandler extends Thread {
        JChannel ch;
        MergeView view;

        private ViewHandler(JChannel ch, MergeView view) {
            this.ch = ch;
            this.view = view;
        }

        public void run() {
            List<View> subgroups = view.getSubgroups();
            View tmp_view = subgroups.get(0); // picks the first
            Address local_addr = ch.getAddress();

            if (!tmp_view.getMembers().contains(local_addr)) {
                try {
                    ch.getState(null, 0);
                } catch (Exception e) {
                    System.err.println("Merging clusters\n" + e.toString());
                }

            }
        }
    }
}

