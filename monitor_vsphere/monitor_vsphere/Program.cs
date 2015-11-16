using System;
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

        // peoperty cache, retrieve by getEntitiesByType
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

        // original getEntitiesByType api call returns [a new moref] each call, which is undesirable
        // make the returned dict use MorefCmp
        //public static Dictionary<ManagedObjectReference, Dictionary<string, object>>
        //    getEntitiesByType_single(string type, string[] props)
        //{
        //    return new Dictionary<ManagedObjectReference, Dictionary<string, object>>(su.getEntitiesByType(type, props), new MorefCmp());
        //}
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

            VCenter.connect();
            
            MQ.setup_local_queue();
           
            // print/send platform info
            MQ.publish(PropHelper.BuildPlatformInfo().message_json);
            
            // retrieve host/vm list
            PropHelper.RetrieveAllEntities();
            PropHelper.RetrieveArrays();

      //      foreach (var k in VCenter.entity_props.Keys)
      //          EventHelper.GetAlarms(k);

            // print/send entity info
            PropHelper.BuildPropMetric();
            
            // for each entity, print/send perf items
            while (true)
            {
                Console.WriteLine("------perf info------");
                foreach (var it in VCenter.entity_props.Keys)
                {
                    PropHelper.UpdatePerfInfo(it);
                }
                EventHelper.Update();
                Thread.Sleep(20000);
            }

            VCenter.close();
            
            Console.Read();
        }
    }
}
