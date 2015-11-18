using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;
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

        public string message_json
        {
            get
            {
//              Dictionary<string, dynamic> dict = new Dictionary<string, dynamic>()
           //       {   { "name", name }, { "timestamp", timestamp }, { "type", type }, { "value", value } };
       //       return Regex.Replace(JsonConvert.SerializeObject(dict), "}$", ", tags=" + JsonConvert.SerializeObject(tags) + "}");

                Dictionary<string, dynamic> dict = new Dictionary<string, dynamic>()
                {   { "name", name }, { "timestamp", timestamp }, { "type", type }, { "value", value }, { "tags", tags } };
                return JsonConvert.SerializeObject(dict);
            }
        }

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
        public static IModel channel;
        public static QueueingBasicConsumer consumer;
        public static bool ready = false;

        public static void setup_local_queue()
        {
            factory = new ConnectionFactory();
            factory.Uri = @"amqp://monitor:root@localhost:5672";
            conn = factory.CreateConnection();
            channel = conn.CreateModel();

            channel.ExchangeDeclare("m.exc", "direct", true);
            channel.QueueDeclare("m.local.dat", true, false, false, null);
            channel.QueueBind("m.local.dat", "m.exc", "l");
            //todo: add consumer
            ready = true;
        }

        public static void publish(string msg, bool debug=false)
        {
            if (!debug)
                channel.BasicPublish("m.exc", "l", null, Encoding.UTF8.GetBytes(msg));
            else
                Console.WriteLine("[publish] {0}", msg);
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

        private static DateTime start_time = TimeZone.CurrentTimeZone.ToLocalTime(new DateTime(1970, 1, 1));
        public static long to_timestamp(DateTime dt)
        {
            // http://www.cnblogs.com/TankXiao/p/3130820.html
            return (long)((dt - start_time).TotalSeconds);
        }

        public static long now() { return to_timestamp(DateTime.Now); }

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
                return !(metric_cache.ContainsKey(met.Tag) && (
                    (metric_cache[met.Tag].value == met.value) ||
                    JsonConvert.SerializeObject(metric_cache[met.Tag].value) == JsonConvert.SerializeObject(met.value))
                    );
            }
            catch { return true; }
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
}
