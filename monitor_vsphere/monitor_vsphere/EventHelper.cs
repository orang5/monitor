using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using Vim25Api;
using AppUtil;
using VMware.Security.CredentialStore;
using System.Web.Services.Protocols;
using MonitorPlugin;

namespace monitor_vsphere
{
    class EventHelper
    {
        public static PropertyFilterSpec[] pfs;
        public static void BuildSpec()
        {
            PropertySpec[] ps = new PropertySpec[] {
                new PropertySpec() { all=false, allSpecified=true, pathSet=new string[] { "latestPage" }, type=VCenter.evtCollector.type }
            };
            ObjectSpec[] os = new ObjectSpec[] {
                new ObjectSpec() { obj = VCenter.evtCollector, skip=false, skipSpecified=true, selectSet=new SelectionSpec[] {} }
            };
            pfs = new PropertyFilterSpec[] { 
                new PropertyFilterSpec() { propSet=ps, objectSet=os }
            };
        }

        public static void Update()
        {
            ObjectContent[] contents = VCenter.su.retrievePropertiesEx(VCenter.sic.propertyCollector, pfs);
            if (contents != null)
            {
                Event[] events = (Event[])contents[0].propSet[0].val;
                foreach (Event e in events)
                {
                    if (!VCenter.event_cache.ContainsKey(e.key))
                    {
                        try
                        {
                            VCenter.event_cache[e.key] = e;
                            Metric met = new Metric()
                            {
                                name = PropHelper.undottify(e.GetType().ToString()),
                                type = "metric",
                                ts = new Dictionary<string, long>() { { "latest", Helper.to_timestamp(e.createdTime) } },
                                value = e.fullFormattedMessage,
                                tags = new Dictionary<string,string>() {
                                    { "key", e.key.ToString() }, { "user", e.userName }
                                }
                            };
                            if (e.net != null) met.tags["mo"] = e.net.name;
                            if (e.host != null)
                            {
                                met.tags["mo"] = e.host.name;
                                met.tags["uuid"] = PropHelper.GetMac(e.host.host);
                            }
                            if (e.vm != null)
                            {
                                met.tags["mo"] = e.vm.name;
                                met.tags["uuid"] = PropHelper.GetMac(e.vm.vm);
                            }
                            if (e.dvs != null) met.tags["mo"] = e.dvs.name;
                            

                            VCenter.publish(met);
                            //Console.WriteLine("Event {0} [{1}] host={2} vm={3} | {4}", e.GetType(), e.createdTime, e.host.name, e.vm.name, e.fullFormattedMessage);
                        }
                        catch (Exception exc)
                        {
                            Console.WriteLine("Event {0} [{1}] | {2} id={3}", e.GetType(), e.createdTime, e.fullFormattedMessage, e.key);
                        }
                    }
                }
            }
        }

        public static void GetAlarms(ManagedObjectReference moref)
        {
            var alarms = VCenter.service.GetAlarm(VCenter.sic.alarmManager, moref);
            foreach (var a in alarms)
            {
                var ret = VCenter.su.getEntitiesInContainerByType(a, "Alarm", new string[] { "info" });
            }

        }
    }
}
