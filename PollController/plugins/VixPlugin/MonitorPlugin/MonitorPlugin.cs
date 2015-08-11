using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.IO;
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

        public MetricDesc() { name = ""; type = ""; interval = -1; cmd = ""; }
        public override string ToString()
        {
            // cropped cmd
            return string.Format("name = {0}, type = {1}, interval = {2}", name, type, interval);
        }

        public MetricDesc set(MetricDesc x)
        {
            this.name = x.name;
            this.type = x.type;
            this.interval = x.interval;
            this.cmd = x.cmd;
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
        public Dictionary<string, string> args;

        public Metric()
        {
            enabled = true;
            ts = new Dictionary<string, long>();
            tags = new Dictionary<string, string>();
            args = new Dictionary<string, string>();
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

        public string message
        {
            get
            {
                StringBuilder sb = new StringBuilder(base.ToString());
                sb.Append(string.Format(", {0}, {1}", timestamp, JsonConvert.SerializeObject(value)));
                foreach (KeyValuePair<string, string> kv in tags)
                    sb.Append(string.Format(", {0} = {1}", kv.Key, kv.Value));
                return sb.ToString();
            }
        }

        public string json_message
        {
            get
            {
                Dictionary<string, dynamic> dict = new Dictionary<string, dynamic>()
                {   { "name", name }, { "timestamp", timestamp }, { "type", type }, { "value", value } };
                foreach (KeyValuePair<string, string> kv in tags)
                    dict[kv.Key] = kv.Value;

                return JsonConvert.SerializeObject(dict);
            }
        }
    }

    public class MQ
    {
        public static ConnectionFactory factory;
        public static IConnection conn;
        public static IModel channel;
        public static QueueingBasicConsumer consumer;
        public static bool ready = false;

        public static void setup_local_queue()
        {
            factory = new ConnectionFactory();
            factory.Uri = @"amqp://monitor:root@localhost:5672";
            conn = factory.CreateConnection();
            channel = conn.CreateModel();

            channel.ExchangeDeclare("monitor.exc", "direct", true);
            channel.QueueDeclare("monitor.local", true, false, false, null);
            channel.QueueBind("monitor.local", "monitor.exc", "local");
            //todo: add consumer
            ready = true;
        }

        public static void publish(string msg, bool debug=false)
        {
            if (!debug)
                channel.BasicPublish("monitor.exc", "local", null, Encoding.UTF8.GetBytes(msg));
            else
                Console.WriteLine("[publish] {0}", msg);
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

        private static DateTime start_time = TimeZone.CurrentTimeZone.ToLocalTime(new DateTime(1970, 1, 1));
        public static long to_timestamp(DateTime dt)
        {
            // http://www.cnblogs.com/TankXiao/p/3130820.html
            return (long)((dt - start_time).TotalSeconds);
        }

        public delegate void MetricWorker(Metric met);

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
                            MQ.publish(met.json_message);
                        else
                            Debug.Print("[update] {0}", met.json_message);
                    }
                }
            }
        }

    }
}
