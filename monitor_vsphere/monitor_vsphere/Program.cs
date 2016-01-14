﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using Vim25Api;
using VMware.Security.CredentialStore;
using AppUtil;
using MonitorPlugin;


namespace monitor_vsphere
{
    // custom MOREF comparer
    class MorefCmp : IEqualityComparer<ManagedObjectReference>
    {
        public bool Equals(ManagedObjectReference x, ManagedObjectReference y)
        {
            return (x.type == y.type) && (x.Value == y.Value);
        }

        public int GetHashCode(ManagedObjectReference obj)
        {
            return (obj.type + obj.Value).GetHashCode();
        }

        public static Dictionary<ManagedObjectReference, T> get_dict<T>(IDictionary<ManagedObjectReference, T> orig)
        {
            return new Dictionary<ManagedObjectReference, T>(orig, new MorefCmp());
        }
    }

    //data class for VCenter inventory
    class VCenter
    {
        public static string ipaddr;
        public static string username;
        public static AppUtil.AppUtil cb;
        public static VimService service { get { return cb.getConnection()._service; } }
        public static ServiceContent sic { get { return cb.getConnection()._sic; } }
        public static ServiceUtil su { get { return cb.getServiceUtil(); } }
        public static ManagedObjectReference perfMgr { get { return sic.perfManager; } }
        public static ManagedObjectReference evtCollector;
        public static List<string> instance_filters = new List<string>();
        public static string ip { get { return MonitorPlugin.Helper.info.platform_data["ipaddr"]; } }

        // property cache, retrieve by getEntitiesByType
        public static Dictionary<ManagedObjectReference, Dictionary<string, object>> entity_props =
            new Dictionary<ManagedObjectReference, Dictionary<string, object>>(new MorefCmp());

        // misc object cache, used by this app.
        public static Dictionary<ManagedObjectReference, Dictionary<string, dynamic>> entity_cache =
            new Dictionary<ManagedObjectReference, Dictionary<string, dynamic>>(new MorefCmp());

        public static Dictionary<int, Event> event_cache = new Dictionary<int, Event>();

        public static void connect()
        {
            try
            {
                ICredentialStore cs = CredentialStoreFactory.CreateCredentialStore();
                string pass = new string(cs.GetPassword(ipaddr, username));
                string url = "https://" + ipaddr + "/sdk/vimService";
                string[] args = {"--url", url,
                                 "--username", username,
                                 "--password", pass, 
                                 "--disablesso", "--ignorecert" };

                cb = AppUtil.AppUtil.initialize("monitor_vsphere", args);
                cb.connect();

                evtCollector = service.CreateCollectorForEvents(sic.eventManager, new EventFilterSpec());
                EventHelper.BuildSpec();
            }
            catch (Exception e)
            {
                Console.WriteLine(e.Message);
            }
        }

        public static void close()
        {
            cb.disConnect();
        }

        public static void publish(Metric met)
        {
            met.tags["platform"] = "vcenter";
            met.tags["platform_ip"] = VCenter.ip;
            MQ.publish(met);
        }
    }

    class Program
    {
        public static void load_config()
        {
            // load metric and plugin info json
            MonitorPlugin.Helper.plugin_info("monitor_vsphere.json");
            Dictionary<string, dynamic> config = MonitorPlugin.Helper.info.platform_data;

            string center = config["ipaddr"];
            string username = config["username"];

            VCenter.ipaddr = center;
            VCenter.username = username;

            foreach (string s in config["instance_filter"])
                VCenter.instance_filters.Add(s);
        }

        static void Main(string[] args)
        {
            load_config();
            MonitorPlugin.MQ.control_callback = TaskHelper.ProcessTask;

            VCenter.connect();
            
            MQ.setup_local_queue();
           
            // print/send platform info
            VCenter.publish(PropHelper.BuildBasicInfo());
            
            // for each entity, print/send perf items
            while (true)
            {
                // retrieve host/vm list
                PropHelper.RetrieveAllEntities();
                PropHelper.RetrieveArrays();
                // print/send entity info
                PropHelper.BuildPropMetric();

                if (true)
                {
                    Console.WriteLine("------ 性能计数 ------");
                    foreach (var it in VCenter.entity_props.Keys)
                    {
                        PropHelper.UpdatePerfInfo(it);
                    }
                    PropHelper.UpdatePerfStat();
                    EventHelper.Update();

                }

                Console.WriteLine("--------------");
                Console.WriteLine("发送: {0}, 缓存: {1}", Perf.counters["publish"], Perf.counters["unchanged"]);
                Perf.reset("publish");
                Perf.reset("unchanged");
                Console.WriteLine("--------------");
                Thread.Sleep(10000);

            }

            VCenter.close();
            
            Console.Read();
        }
    }
}
