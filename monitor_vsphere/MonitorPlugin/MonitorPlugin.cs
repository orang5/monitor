using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.IO;
using System.Net;
using Newtonsoft.Json;
using RabbitMQ.Client;

namespace MonitorPlugin
{
    // metric types
    public class MetricDesc
    {
        public string name;
        public string type;
        public int interval;
        public string cmd;
        public Dictionary<string, string> args;

        public MetricDesc() { name = ""; type = ""; interval = -1; cmd = ""; args = new Dictionary<string, string>(); }
        public override string ToString()
        {
            // cropped cmd, args
            return string.Format("name = {0}, type = {1}, interval = {2}", name, type, interval);
        }

        public MetricDesc set(MetricDesc x)
        {
            this.name = x.name;
            this.type = x.type;
            this.interval = x.interval;
            this.cmd = x.cmd;
            this.args = x.args;
            return this;
        }
    }

    public class PluginDesc
    {
        public string name;
        public string description;
        public string type;
        public Dictionary<string, string> cmd_list;
        public List<MetricDesc> metrics;
        public Dictionary<string, dynamic> platform_data;
    }

    public class Metric : MetricDesc
    {
        public bool enabled;
        public Dictionary<string, long> ts;
        public dynamic value;
        public Dictionary<string, string> tags;
        

        public Metric()
        {
            enabled = true;
            ts = new Dictionary<string, long>();
            tags = new Dictionary<string, string>();
            ts["latest"] = Helper.to_timestamp(DateTime.Now);
        }

        public MetricDesc metric
        {
            get { return (MetricDesc)this; }
            set {
                this.name = value.name;
            }
        }

        public long timestamp { get { return ts["latest"]; } }

        //public string message
        //{
        //    get
        //    {
        //        StringBuilder sb = new StringBuilder(base.ToString());
        //        sb.Append(string.Format(", {0}, {1}", timestamp, JsonConvert.SerializeObject(value)));
        //        foreach (KeyValuePair<string, string> kv in tags)
        //            sb.Append(string.Format(", {0} = {1}", kv.Key, kv.Value));
        //        return sb.ToString();
        //    }
        //}
        public Dictionary<string, dynamic> message_dict
        {
            get
            {
                Dictionary<string, dynamic> dict = new Dictionary<string, dynamic>() { { "name", name }, { "timestamp", timestamp }, { "type", type }, { "value", value }, { "tags", tags } };
                return dict;
            }
        }
        public string message_json { get { return JsonConvert.SerializeObject(message_dict); } }

        /// <summary>
        /// name+tags (flattened)
        /// unique id string for a metric ( without value and timestamp )
        /// example:
        /// "name=cpu_usage DeviceID=cpu0 host=host1"
        /// </summary>
        public string Tag
        {
            get {
                StringBuilder sb = new StringBuilder();
                foreach (var kv in tags)
                    sb.Append(kv.Key + "=" + kv.Value + " ");
                sb.Append(name);
                return sb.ToString();
            }
        }
    }

    public class MQ
    {
        public static ConnectionFactory factory;
        public static IConnection conn;
        public static IModel channel, request_chn, reply_chn;
        public static QueueingBasicConsumer consumer;
        public static Thread th;
        public static bool restart_flag = false;
        public static string pid;
        public delegate void control_delegate(Dictionary<string, string> args);
        public static control_delegate control_callback = null;

        public static void setup_local_queue()
        {
            restart_flag = true;
            factory = new ConnectionFactory();
            factory.Uri = @"amqp://monitor:root@" + Helper.get_ip() + ":5672";
            conn = factory.CreateConnection();
            channel = conn.CreateModel();
            request_chn = conn.CreateModel();
            reply_chn = conn.CreateModel();

            // data channel. exchange: m.exc, queue: m.local.dat, routing key: ld
            channel.ExchangeDeclare("m.exc", "direct", true);
            channel.QueueDeclare("m.local.dat", true, false, false, null);
            channel.QueueBind("m.local.dat", "m.exc", "ld");

            pid = Process.GetCurrentProcess().Id.ToString();
            string request_queue = "m.local." + pid;
            string reply_queue = "m.local.reply";
            
            // request ( agent -> here ) channel. queue: m.local.[pid], routing_key: pid
            request_chn.QueueDeclare(request_queue, false, false, true, null);
            request_chn.QueueBind(request_queue, "m.exc", pid);
            // reply (here -> agent) channel. queue: m.local.reply, routing_key: lr
            reply_chn.QueueDeclare(reply_queue, false, false, true, null);
            reply_chn.QueueBind(reply_queue, "m.exc", "lr");

            consumer = new QueueingBasicConsumer(request_chn);
            request_chn.BasicConsume(request_queue, false, consumer);

            // start consumer
            th = new Thread(new ThreadStart(consumer_thread));
            th.Start();
            restart_flag = false;
            Console.WriteLine("[MonitorPlugin] MQ 连接就绪.");
        }

        public static void consumer_thread()
        {
            try
            {
                Console.WriteLine("[MonitorPlugin] 控制线程已启动.");
                while (!restart_flag)
                {
                    var recv = consumer.Queue.Dequeue();
                    string msg = Encoding.UTF8.GetString(recv.Body);
                    Dictionary<string, string> d = JsonConvert.DeserializeObject<Dictionary<string, string>>(msg);
                    Debug.WriteLine("++++++++++++++++++　[vsphere] 控制消息: {0}", msg);
                    //  publish_con("{\"reply\" : \"[vsphere] received control message.\", \"pid\" : " + pid.ToString() + "}");
                    if (control_callback != null)
                        control_callback(d);
                }
            }
            catch (Exception e)
            {
                Debug.WriteLine(e.Message);
            }
            restart_flag = true;
        }

        public static void publish(string msg, bool debug=false)
        {
            Perf.inc("publish");
            check_conn();
            try {
                if (!debug)
                    channel.BasicPublish("m.exc", "ld", null, Encoding.UTF8.GetBytes(msg));
                else
                {
                    Console.WriteLine("[publish] {0}", msg);
                //    Exception e = new Exception("test");
                 //   throw e;
                }
            }
            catch (Exception e)
            {
                Console.WriteLine(e.Message);
                restart_flag = true;
                check_conn();
            }
        }

        public static void publish(Metric met, bool check=true, bool debug=false)
        {
            if (!check)
                publish(met.message_json, debug);
            else if (Helper.metric_changed(met))
            {
                Helper.save_metric(met);        //add to cache
                publish(met.message_json, debug);
            }
            else { Perf.inc("unchanged"); }
        }

        public static void publish_con(string msg, bool debug = false)
        {
            if (!debug)
                reply_chn.BasicPublish("m.exc", "lr", null, Encoding.UTF8.GetBytes(msg));
            else
                Console.WriteLine("[control] {0}", msg);
        }

        // check connection, if screwed, restart it
        // only call it in main thread. if child thread fails, leave it
        public static void check_conn()
        {
            if (restart_flag)
            {
                Console.WriteLine("*** MonitorPlugin MQ 连接异常 ***");
                try
                {
                    th.Abort();
                }
                catch { }
                consumer = null;
                channel = null;
                conn = null;
                factory = null;
                GC.Collect();

                Console.WriteLine("*** 等待3秒 ***");
                Thread.Sleep(3000);

                Console.WriteLine("*** MonitorPlugin: 尝试恢复MQ ***");
                setup_local_queue();
            }
        }

        public static void close()
        {
            channel.Close();
            conn.Close();
        }

    }

    public class Helper
    {
        public static PluginDesc info;
        public static Dictionary<int, List<Metric>> metrics = new Dictionary<int, List<Metric>>();
        public static Dictionary<int, long> ts = new Dictionary<int, long>();
        public static Dictionary<string, Metric> metric_cache = new Dictionary<string, Metric>();

        public static void plugin_info(string filename)
        {
            info = JsonConvert.DeserializeObject<PluginDesc>(File.ReadAllText(filename, Encoding.UTF8));

            foreach (MetricDesc m in info.metrics)
            {
                if (!metrics.ContainsKey(m.interval))
                {
                    metrics[m.interval] = new List<Metric>();
                    ts[m.interval] = 0;
                }
                Metric met = new Metric();
                met.set(m);
                metrics[m.interval].Add(met);
            }
        }

        public static string get_ip()
        {
            string hostname = Dns.GetHostName();
            foreach (var addr in Dns.GetHostAddresses(hostname))
                if (addr.AddressFamily.ToString() == "InterNetwork")
                    return addr.ToString();
            return null;
        }

        private static DateTime start_time = TimeZone.CurrentTimeZone.ToLocalTime(new DateTime(1970, 1, 1));
        public static long to_timestamp(DateTime dt)
        {
            // http://www.cnblogs.com/TankXiao/p/3130820.html
            return (long)((dt - start_time).TotalSeconds);
        }

        public static long now() { return to_timestamp(DateTime.Now); }
        public static Dictionary<string, long> default_timestamp()
        { return new Dictionary<string, long>() { { "latest", now() } };  }

        public delegate void MetricWorker(Metric met);

        // check if current metric value has changed
        public static bool metric_changed(Metric met)
        {
            // metrics remains unchanged only if:
            // (1) cached, AND then
            // (2) value equals OR (3) json value equals
            // otherwise changed.
            try
            {
                //return true;
                return !(metric_cache.ContainsKey(met.Tag) && (
                    (metric_cache[met.Tag].value == met.value) ||
                    JsonConvert.SerializeObject(metric_cache[met.Tag].value) == JsonConvert.SerializeObject(met.value))
                    );

            }
            catch { 
                return JsonConvert.SerializeObject(metric_cache[met.Tag].value) == JsonConvert.SerializeObject(met.value);
                //return true;
            }
        }
        
        // wrapper for Helper.metric_cache[met.Tag] = met
        public static void save_metric(Metric met)
        {
            metric_cache[met.Tag] = met;
        }

        // check metric list
        public static void update_metrics(MetricWorker worker, bool publish=true)
        {
            long t = to_timestamp(DateTime.Now);
            foreach (int i in metrics.Keys)
            {
                if (i > 0 && t > ts[i] + i)
                {
                    ts[i] = t;
                    foreach (Metric met in metrics[i])
                    {
                        met.ts["execute"] = to_timestamp(DateTime.Now);
                        met.tags.Clear();

                        worker(met);

                        met.ts["latest"] = to_timestamp(DateTime.Now);
                        if (publish)
                            MQ.publish(met);
                        else
                            Debug.Print("[update] {0}", met.message_json);
                    }
                }
            }
        }

    }

    public class Perf
    {
        public static Dictionary<string, int> counters = new Dictionary<string, int>();
        public static Dictionary<string, int> totals = new Dictionary<string, int>();

        public static void reset() { counters.Clear(); totals.Clear(); }
        public static void reset(string name) { counters[name] = 0; }
        public static void inc(string name, int value = 1)
        {
            try { counters[name] += 1; totals[name] += 1; }
            catch { counters[name] = totals[name] = 1; }
        }
    }
}
