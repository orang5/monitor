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
    class PropHelper
    {
        // python type / identifier helper     
        // --------------------------
        public static string dottify(string str)
        {
            return str.Replace("_", ".").Replace("..", "_");
        }

        public static string undottify(string str)
        {
            return str.Replace("_", "..").Replace(".", "_");
        }

        // prop retrivers
        // call vSphere API to retrieve props and cache them
        // --------------------------

        /// <summary>
        /// retrieve data in each turn, call this for update
        /// </summary>
        public static void RetrieveUpdate()
        {
            // backup existing moref list
            var morefs = VCenter.entity_props.Keys.ToList();
            // first, update two main caches
            RetrieveAllEntities();
            RetrieveArrays();

        }

        // get groups of moref+props as described in monitor_vsphere.json
        // for each kind of entities, invoke one call of getEntitiesByType to retrieve all listed props in JSON.
        // then flatten the nested dictionary into entity_props
        public static void RetrieveAllEntities()
        {
            var entity_result = from met in MonitorPlugin.Helper.info.metrics
                                where met.args.ContainsKey("entity")
                                group met by met.args["entity"] into g
                                select VCenter.su.getEntitiesByType(g.Key, (from met in g select dottify(met.name)).ToArray());
            foreach (var item in entity_result)
            {
                foreach (var k in item.Keys)
                {
                    // special judge for Datastore
                    if (k.type == "Datastore" && item[k]["summary.accessible"].Equals(true))
                    {
                        string[] ds_props = new string[] {"summary.freeSpace", "summary.capacity", "summary.uncommitted"};
                        foreach (string s in ds_props)
                            item[k][s] = VCenter.su.getProp(k, s);                           
                    }

                    VCenter.entity_props[k] = item[k];
                }
            }
        }

        // get prop arrays, which cannot process uniformly in entity_props
        // unfortunately, we cannot easily parse deeply nested attributes from dynamic types in arrays
        // so can only cast them, and hard-coded here
        // store these arrays in entity_cache
        public static void RetrieveArrays()
        {
            // host arrays
            var host_arrays = VCenter.su.getEntitiesByType("HostSystem", new string[] {
                "config.network.netStackInstance",          // net stack inst array
                "config.network.vnic",                      // host virtual nic array
                "vm"                                        // vm moref array
            });
            foreach (var item in host_arrays)
            {
                Dictionary<string, dynamic> dict = new Dictionary<string, dynamic>() {
                    { "nsi", (HostNetStackInstance[])item.Value["config.network.netStackInstance"] },
                    { "vnic", (HostVirtualNic[])item.Value["config.network.vnic"] },
                    { "vm", (ManagedObjectReference[])item.Value["vm"] }
                };

                // hard-coded type definitions instead of dynamic
                List<HostNetStackInstance> t_nsi = new List<HostNetStackInstance>(dict["nsi"]);
                List<HostVirtualNic> t_pn = new List<HostVirtualNic>(dict["vnic"]);
                List<ManagedObjectReference> t_vm = new List<ManagedObjectReference>(dict["vm"]);
                dict["nsi.key"] = t_nsi.Select(x => x.key).ToList();
                dict["nsi.name"] = t_nsi.Select(x => x.name).ToList();
                dict["nsi.ipRouteConfig.defaultGateway"] = t_nsi.Select(x => x.ipRouteConfig.defaultGateway).ToList();
                dict["vnic.spec.mac"] = t_pn.Select(x => x.spec.mac).ToList();
                dict["vnic.spec.ip"] = t_pn.Select(x => x.spec.ip).ToList();
                dict["vm.name"] = t_vm.Select(x => Get(x, "name")).ToList();

                VCenter.entity_cache[item.Key] = dict;
            }

            // can call GetMac/GetIP for HostSystem from here on
            //----------------------------------------------------------------------------------------------------

            // vm arrays
            var vm_arrays = VCenter.su.getEntitiesByType("VirtualMachine", new string[] {
                "runtime.host",          // host moref (not an array!)
                "layoutEx.file",         // file list
                "guest.net",             // guest nic info
                "guest.disk",            // guest disk info
            });

            foreach (var item in vm_arrays)
            {
                Dictionary<string, dynamic> dict = new Dictionary<string, dynamic>() {
                    { "host", (ManagedObjectReference)item.Value["runtime.host"] },
                    { "filelist", ((VirtualMachineFileLayoutExFileInfo[])item.Value["layoutEx.file"]).ToList() },
                    { "net", ((GuestNicInfo[])item.Value["guest.net"]).ToList() },
                    { "disk", ((GuestDiskInfo[])item.Value["guest.disk"]).ToList() },
                };
                
                // hard-coded type definitions instead of dynamic
                List<GuestNicInfo> t_gn = new List<GuestNicInfo>(dict["net"]);
                dict["host.name"] = Get(dict["host"], "name");
                dict["host.mac"] = GetMac(dict["host"]);
                dict["guest.net.mac"] = t_gn.Select(x => x.macAddress).ToList();
                dict["guest.net.ip"] = t_gn.Select(x => x.ipConfig).ToList();

                VCenter.entity_cache[item.Key] = dict;
            }

            // can call GetMac/GetIP for VirtualMachine from here on
            //----------------------------------------------------------------------------------------------------

            foreach (var item in host_arrays)
            {
                List<ManagedObjectReference> t_vm = new List<ManagedObjectReference>((ManagedObjectReference[])item.Value["vm"]);
                VCenter.entity_cache[item.Key]["vm.info"] = t_vm.Select(x => new Dictionary<string, string>() {
                    { "uuid", GetMac(x) },
                    { "mo", Get(x, "name") },
                    { "is_template", IsTemplate(x).ToString() },
                    { "ip", GetIP(x) },
                    { "power", Get(x, "power")},
                    { "os", Get(x, "os")}
                }).ToList();
            }

            // ClusterComputeResource arrays
            var cl_arrays = VCenter.su.getEntitiesByType("ClusterComputeResource", new string[] {
                "datastore", "host", "network", "resourcePool"
            });

            // specify comparator!
            var pool_arrays = new Dictionary<ManagedObjectReference, Dictionary<string, object>>(VCenter.su.getEntitiesByType("ResourcePool", new string[] {
                    "resourcePool", "vm"
                }), new MorefCmp());

            foreach (var item in cl_arrays)
            {
                // define type info
                Dictionary<string, dynamic> dict = new Dictionary<string, dynamic>() {
                    { "datastore", ((ManagedObjectReference[])item.Value["datastore"]).ToList() },
                    { "host", ((ManagedObjectReference[])item.Value["host"]).ToList() },
                    { "net", ((ManagedObjectReference[])item.Value["network"]).ToList() },
                    { "pool", (ManagedObjectReference)item.Value["resourcePool"] },
                };
                dict["pool_props"] = VCenter.entity_props[dict["pool"]];
                dict["pool_arrays"] = pool_arrays[dict["pool"]];
                dict["vm"] = (ManagedObjectReference[])dict["pool_arrays"]["vm"];

                VCenter.entity_cache[item.Key] = dict;
            }

            var dvs_arrays = VCenter.su.getEntitiesByType("DistributedVirtualSwitch", new string[] {
                "summary.host", "summary.vm"
            });

            foreach (var item in dvs_arrays)
            {
                Dictionary<string, dynamic> dict = new Dictionary<string, dynamic>() {
                    { "host", ((ManagedObjectReference[])item.Value["summary.host"]).ToList() }, 
                    { "vm", ((ManagedObjectReference[])item.Value["summary.vm"]).ToList() }
                };
                VCenter.entity_cache[item.Key] = dict;
            }

            var net_arrays = VCenter.su.getEntitiesByType("Network", new string[] {
                "host", "vm"
            });

            foreach (var item in net_arrays)
            {
                Dictionary<string, dynamic> dict = new Dictionary<string, dynamic>() {
                    { "host", ((ManagedObjectReference[])item.Value["host"]).ToList() }, 
                    { "vm", ((ManagedObjectReference[])item.Value["vm"]).ToList() }
                };
                VCenter.entity_cache[item.Key] = dict;
            }

        }

        // get info of perf monitors for given moref
        // infos cached in entity_cache
        public static void RetrievePerfInfo(ManagedObjectReference moref)
        {
            // find all metrics for given entity(moref)
            List<PerfMetricId> pmid_all = new List<PerfMetricId>();
            int interval = 20;
            // try to get 20sec metric. if failed, try 300sec instead
            try
            {
                pmid_all = VCenter.service.QueryAvailablePerfMetric(VCenter.perfMgr, moref,
                                DateTime.Now.AddHours(-1), true, DateTime.Now, true, interval, true).ToList();
            }
            catch {
                interval = 300;
                pmid_all = VCenter.service.QueryAvailablePerfMetric(VCenter.perfMgr, moref,
                                DateTime.MinValue, false, DateTime.MinValue, false, interval, true).ToList();
            }

            // filter by regex, defined in monitor_vsphere.json platform_info["instance_filters"]
            PerfMetricId[] pmid = (from p in pmid_all
                                   where p.instance == "" || VCenter.instance_filters.Any(s => Regex.IsMatch(p.instance, s))
                                   orderby p.instance, p.counterId
                                   select p).ToArray();
            if (!VCenter.entity_cache.ContainsKey(moref)) VCenter.entity_cache[moref] = new Dictionary<string, dynamic>();

            if (pmid.Length > 0)
            {
                // find all counter info for each DISTINCT metrics.counterId
                PerfCounterInfo[] cts = VCenter.service.QueryPerfCounter(VCenter.perfMgr,
                    new List<PerfMetricId>(pmid).Select(p => p.counterId).Distinct().ToArray());
                Dictionary<int, PerfCounterInfo> counters = new Dictionary<int, PerfCounterInfo>();
                foreach (PerfCounterInfo p in cts)
                    counters[p.key] = p;

                Console.WriteLine("-- PerfMetricId: {0}, PerfCounterInfo: {1} --", pmid.Length, cts.Length);

                // build pqs for all metrics for given entity
                PerfQuerySpec spec = new PerfQuerySpec()
                {
                    entity = moref,
                    maxSample = 1,
                    maxSampleSpecified = true,
                    intervalId = interval,
                    intervalIdSpecified = true,
                    metricId = pmid
                };

                // save
                //      VCenter.entity_cache[moref]["pmid"] = pmid;
                VCenter.entity_cache[moref]["pcs"] = counters;
                VCenter.entity_cache[moref]["pspec"] = spec;
            }
            else
            {
                VCenter.entity_cache[moref]["pspec"] = null;
            }
        }

        // prop getters
        // helper method to get CACHED props
        // --------------------------
        
        // generic getter, short version
        // dictionary. todo: in text file?
        static Dictionary<string, Dictionary<string, string>> shortcut = new Dictionary<string, Dictionary<string, string>>()
        {
            { "HostSystem", new Dictionary<string, string>() {
                {"name", "summary.config.name"},
                {"uuid", "summary.hardware.uuid"}
            } },
            { "VirtualMachine", new Dictionary<string, string>() {
                {"name", "summary.config.name"},
                {"uuid", "summary.config.uuid"},
                {"power","runtime.powerState"},
                {"os", "summary.config.guestFullName"}
            } },
            { "ResourcePool", new Dictionary<string, string>() {
                {"name", "summary.name"}                
            } },
            { "Datastore", new Dictionary<string, string>() {
                {"name", "summary.name"}                
            } },
            { "DistributedVirtualSwitch", new Dictionary<string, string>() {
                {"name", "summary.name"}
            } },
            { "Network", new Dictionary<string, string>() },
            { "ClusterComputeResource", new Dictionary<string, string>() },
            { "Datacenter", new Dictionary<string, string>() }
        };

        public static string Get(ManagedObjectReference moref, string key)
        {
            if (shortcut[moref.type].ContainsKey(key))
            {
                return VCenter.entity_props[moref][shortcut[moref.type][key]].ToString();
            }
            else
                return VCenter.entity_props[moref][key].ToString();
        }

        /// <summary>
        /// get unique identifier for moref
        /// </summary>
        /// <param name="moref">given moref</param>
        /// <returns>
        /// host / running VM:  mac
        /// VM template:        uuid
        /// other (VM w/o tools and not running): "n/a"
        /// other moref:        "empty/type"
        /// </returns>
        public static string GetMac(ManagedObjectReference moref)
        {
            if (moref.type == "HostSystem")
                return VCenter.entity_cache[moref]["vnic.spec.mac"][0].Replace(":", "");
            else if (moref.type == "VirtualMachine")
                try
                {
                    if (IsTemplate(moref))
                        return (string)VCenter.entity_props[moref]["summary.config.uuid"];
                    else return VCenter.entity_cache[moref]["guest.net.mac"][0].Replace(":", "");
                }
                catch (Exception e)
                {
                    return "n/a";
                }
            else return "empty/" + moref.type;
        }

        /// <summary>
        /// return IP of given moref
        /// </summary>
        /// <param name="moref">given moref</param>
        /// <returns>string: ip address. WARNING: when value==null, returns "n/a" .</returns>
        public static string GetIP(ManagedObjectReference moref)
        {
            if (moref.type == "HostSystem")
            {
                List<HostIpConfig> hip = VCenter.entity_cache[moref]["vnic.spec.ip"];
                if (hip[0].ipAddress == null)
                    return "n/a";
                else return hip[0].ipAddress;
            }
            else if (moref.type == "VirtualMachine")
            {
                try
                {
                    string ret = (string)VCenter.entity_props[moref]["guest.ipAddress"];
                    if (ret == null) ret = "n/a";
                    return ret;
                }
                catch { return "n/a"; }
            }
            else return "empty/" + moref.type;
        }

        public static bool IsTemplate(ManagedObjectReference moref)
        {
            return (moref.type == "VirtualMachine" && (bool)VCenter.entity_props[moref]["summary.config.template"]);
        }
        
        // Metric object builders
        // --------------------------
        // build the platform_info metric
        // send basic platform info when first connect to vcenter
        public static Metric BuildBasicInfo()
        {
            AboutInfo ai = VCenter.sic.about;
            Console.WriteLine("虚拟化平台: {0} IP {1}", ai.fullName, VCenter.ip);
            Console.WriteLine("API版本: {0} {1}", ai.apiType, ai.version);
            return new Metric() {
                name = "platform_info_basic",
                type = "inventory",
                ts = MonitorPlugin.Helper.default_timestamp(), 
                value = new Dictionary<string, string>() {
                    { "full_name", ai.fullName },
                    { "ip", VCenter.ip },
                    { "api_type", ai.apiType },
                    { "version", ai.version }
                }, 
                tags = new Dictionary<string, string>()
            };
        }

        // build summary metric for platform dashboard view.
        // difference from BuildPlatformInfo: can only call this after all Retrieve() methods
        public static Metric BuildPlatformInfo()
        {
            AboutInfo ai = VCenter.sic.about;
            Dictionary<string, dynamic> v = new Dictionary<string, dynamic>();

            // basic info
            v["full_name"] = ai.fullName;
            v["ip"] = VCenter.ip;
            v["api_type"] = ai.apiType;
            v["version"] = ai.version;

            //TODO:
            return new Metric()
            {
                name = "platform_info",
                type = "inventory",
                ts = MonitorPlugin.Helper.default_timestamp(),
                value = v,
                tags = new Dictionary<string, string>() {}
            };
        }

        // get cached full name of perf metric
        // id_[inst]_[group]_[name]
        public static string PerfMetricFullName(string instance, string group, string name)
        {
            return "id_" + instance + "_" + group + "_" + name;
        }

        // build perf(type:metric) metrics
        // name = [group]_[name]
        // DeviceID = id_[inst]_[group]
        static Metric BuildPerfMetric(ManagedObjectReference moref, PerfCounterInfo pci, long v, DateTime ts, string instance)
        {
            Metric met = new Metric()
            {
                name = string.Format("{0}_{1}", pci.groupInfo.key, pci.nameInfo.key),
                value = v,
                type = "metric",
                tags = new Dictionary<string, string>()
                {
                    { "mo_type", moref.type },
                    { "ref", moref.Value },
                    { "mo", Get(moref, "name") },
                    { "inst", instance.Replace('/', '_') },
                    { "uuid", GetMac(moref) },
                },
                ts = new Dictionary<string, long>()
                {
                    { "latest", Helper.to_timestamp(ts) }
                }
            };
            // deviceid is metric group identifier
            met.tags["DeviceID"] = "id_" + met.tags["inst"] + "_" + pci.groupInfo.key;
            return met;
        }

        // build/send config (type:inventory) metrics
        // and build lists for each main morefs
        public static void BuildPropMetric()
        {
            // entity_list: all morefs, basic information
            Metric met = new Metric()
            {
                name = "entity_list",
                type = "inventory", //todo: change type to RUNTIME
                value = VCenter.entity_props.Keys.Select(x => new Dictionary<string, string>() {
                    { "uuid", GetMac(x) },
                    { "mo", Get(x, "name") },
                    { "ref", x.Value },
                    { "mo_type", x.type },
                    }).ToArray(),
                ts = new Dictionary<string, long>() { { "latest", Helper.now() } }
            };
            VCenter.publish(met);

            foreach (var it in VCenter.entity_props)
            {
                foreach (KeyValuePair<string, object> kv in it.Value)
                {
                    // Console.WriteLine("{0} : {1}", undottify(kv.Key), kv.Value);
                    met = new Metric()
                    {
                        name = undottify(kv.Key),
                        type = "inventory",
                        value = kv.Value,
                        ts = new Dictionary<string, long>() { { "latest", Helper.now() } },
                        tags = new Dictionary<string, string>()
                        {
                            { "mo", (string)Get(it.Key, "name") },
                            { "mo_type", it.Key.type },
                            { "ref", it.Key.Value },
                            { "uuid", GetMac(it.Key) }
                        }
                    };
                    // print/send metric
                    //Console.WriteLine(met.message_json);
                    VCenter.publish(met);
                }

                switch (it.Key.type)
                {
                    case "HostSystem":
                        BuildHostArrays(it.Key); break;
                    case "VirtualMachine":
                        BuildVMArrays(it.Key); break;
                    case "ClusterComputeResource":
                        BuildClusterInfo(it.Key); break;
                    case "DistributedVirtualSwitch":
                        BuildNetArrays(it.Key); break;
                    case "Network":
                        BuildNetArrays(it.Key); break;
                }

              //  Console.WriteLine("-------------------------");
            }
        }

        // build list metrics for HostSystem.
        // vm_list, 
        public static void BuildHostArrays(ManagedObjectReference moref)
        {
            var cache = VCenter.entity_cache[moref];
            // vm list for host
            Metric met = new Metric()
            {
                name = "vm_list",
                type = "config",
                ts = new Dictionary<string, long>() { { "latest", Helper.now() } },
                value = cache["vm.info"],
                tags = new Dictionary<string, string>()
                {
                    { "mo", Get(moref, "name") },
                    { "mo_type", moref.type },
                    { "ref", moref.type },
                    { "uuid", GetMac(moref) }
                }
            };
            VCenter.publish(met);

            // host ip summary
            met.name = "host_ip";
            List<HostIpConfig> hip = cache["vnic.spec.ip"];     // assign type info
            met.value = new Dictionary<string, string>() {
             //   { "dhcp", hip[0].dhcp.ToString() }, // poison!
                { "ip", hip[0].ipAddress },
                { "mask", hip[0].subnetMask },
           //     { "gateway", cache["nsi.ipRouteConfig.defaultGateway"][0] }
            };
           // VCenter.publish(met);

            // host ip list
            met.name = "host_ipConfig";
            met.value = new List<Dictionary<string, string>>();
            for (int i = 0; i < hip.Count; ++i)
            {
                try
                {
                    Dictionary<string, string> v = new Dictionary<string, string>() {
                        { "ip", hip[i].ipAddress },
                        { "mask", hip[i].subnetMask },
                        { "mac", cache["vnic.spec.mac"][i] },
                //        { "gateway", cache["nsi.ipRouteConfig.defaultGateway"][i] } // poison!
                    };
                    try
                    {
                        v["dhcp"] = hip[i].dhcp.ToString();
                    }
                    catch (NullReferenceException e)
                    {
                        v["dhcp"] = "false";
                    }

                    met.value.Add(v);
                }
                catch { }
            }
           // VCenter.publish(met);

        }

        public static void BuildVMArrays(ManagedObjectReference moref)
        {
            var cache = VCenter.entity_cache[moref];
            // host
            Metric met = new Metric()
            {
                name = "vm_host",
                type = "config",
                ts = new Dictionary<string, long>() { { "latest", Helper.now() } },
                value = GetMac(cache["host"]),
                tags = new Dictionary<string, string>()
                {
                    { "mo", Get(moref, "name") },
                    { "mo_type", moref.type },
                    { "ref", moref.Value },
                    { "uuid", GetMac(moref) }
                }
            };
            //VCenter.publish(met);

            // ip summary
            if (!IsTemplate(moref) && GetMac(moref) != "no_data")
            {
                met.name = "vm_ip";
                met.value = "0.0.0.0";
                try
                {
                    List<NetIpConfigInfo> ip = cache["guest.net.ip"];   //assign type info
                    met.value = new Dictionary<string, string>() {
                        { "ip", (string)VCenter.entity_props[moref]["guest.ipAddress"] },
                        { "mac", cache["guest.net.mac"][0].Replace(":", "") }
                    };
                    //VCenter.publish(met);
                }
                catch { }

                // disk info
                met.name = "vm_disk";
                met.value = new List<Dictionary<string, string>>();
                for (int i = 0; i < cache["disk"].Count; ++i)
                {
                    Dictionary<string, string> f = new Dictionary<string, string>() {
                        { "capacity", cache["disk"][i].capacity.ToString() },
                        { "diskPath", cache["disk"][i].diskPath },
                        { "freeSpace", cache["disk"][i].freeSpace.ToString() },
                    };
                    met.value.Add(f);
                }
                VCenter.publish(met);
            }

            // file list
            met.name = "vm_files";
            met.value = new List<Dictionary<string, string>>();
            List<VirtualMachineFileLayoutExFileInfo> info = cache["filelist"];
            for (int i = 0; i < cache["filelist"].Count; ++i)
            {
                Dictionary<string, string> f = new Dictionary<string, string>() {
                        { "name", info[i].name },
                        { "type", info[i].type },
                    };
                met.value.Add(f);
            }
            VCenter.publish(met);
        }

        // build cluster list
        public static void BuildClusterInfo(ManagedObjectReference moref)
        {
            var cache = VCenter.entity_cache[moref];
            Dictionary<string, dynamic> v = new Dictionary<string, dynamic>();

            // combine CpmputeResource and ResourcePool info into one metric
            // add ComputeResource info
            foreach (var kv in VCenter.entity_props[moref])
                v[kv.Key] = kv.Value;

            // add ResourcePool info
            foreach (var kv in VCenter.entity_props[(ManagedObjectReference)cache["pool"]])
                v[kv.Key] = kv.Value;

            Metric met = new Metric()
            {
                name = "cluster_info",
                type = "inventory",
                ts = MonitorPlugin.Helper.default_timestamp(),
                value = v,
                tags = new Dictionary<string, string>()
                {
                    { "mo", Get(moref, "name") },
                    { "mo_type", moref.type },
                    { "ref", moref.Value },
                }
            };
            VCenter.publish(met);

            var host_list = new List<Dictionary<string, string>>();
            var ds_list = new List<Dictionary<string, string>>();
            var vm_list = new List<Dictionary<string, string>>();

            // host_list
            foreach (var hostmor in cache["host"])
                host_list.Add(new Dictionary<string, string>() {
                    { "uuid", GetMac(hostmor) },
                    { "mo", Get(hostmor, "name") },
                    { "ref", hostmor.Value },
                    { "ip", GetIP(hostmor) },
                });
            met.name = "host_list";
            met.value = host_list;
            VCenter.publish(met);

            foreach (var vmmor in cache["vm"])
                vm_list.Add(new Dictionary<string, string>() {
                    { "uuid", GetMac(vmmor) },
                    { "mo", Get(vmmor, "name") },
                    { "ref", vmmor.Value },
                    { "is_template", IsTemplate(vmmor).ToString() },
                    { "ip", GetIP(vmmor) },
                    { "power", Get(vmmor, "power")},
                    { "os", Get(vmmor, "os")}
                });
            met.name = "vm_list";
            met.value = vm_list;
            VCenter.publish(met);

            foreach (var dsmor in cache["datastore"])
            {
                var ds_props = new Dictionary<string, string>() {
                    { "mo", Get(dsmor, "name") },
                    { "ref", dsmor.Value },
                    { "url", Get(dsmor, "summary.url") },
                    { "accessible", Get(dsmor, "summary.accessible") }
                };
                if (ds_props["accessible"].Equals(true))
                {
                    ds_props["freeSpace"] = Get(dsmor, "summary.freeSpace");
                    ds_props["capacity"] = Get(dsmor, "summary.capacity");
                    ds_props["uncommitted"] = Get(dsmor, "summary.uncommitted");
                }
                ds_list.Add(ds_props);
            }
            met.name = "ds_list";
            met.value = ds_list;
            VCenter.publish(met);

        }

        public static void BuildNetArrays(ManagedObjectReference moref)
        {
            var cache = VCenter.entity_cache[moref];
            var host_list = new List<Dictionary<string, string>>();
            var vm_list = new List<Dictionary<string, string>>();

            // host_list
            foreach (var hostmor in cache["host"])
                host_list.Add(new Dictionary<string, string>() {
                    { "uuid", GetMac(hostmor) },
                    { "mo", Get(hostmor, "name") },
                    { "ref", hostmor.Value },
                    { "ip", GetIP(hostmor) },
                });
            foreach (var vmmor in cache["vm"])
                vm_list.Add(new Dictionary<string, string>() {
                    { "uuid", GetMac(vmmor) },
                    { "mo", Get(vmmor, "name") },
                    { "ref", vmmor.Value },
                    { "is_template", IsTemplate(vmmor).ToString() },
                    { "ip", GetIP(vmmor) },
                    { "power", Get(vmmor, "power")},
                    { "os", Get(vmmor, "os")}
                });

            Metric met = new Metric()
            {
                name = "host_list",
                type = "inventory",
                ts = MonitorPlugin.Helper.default_timestamp(),
                value = host_list,
                tags = new Dictionary<string, string>()
                {
                    { "mo", Get(moref, "name") },
                    { "mo_type", moref.type },
                    { "ref", moref.Value },
                }
            };
            VCenter.publish(met);

            met.name = "vm_list";
            met.value = vm_list;
            VCenter.publish(met);
        }

        // update methods.
        // --------------------------
        // update perf data for given moref
        public static void UpdatePerfInfo(ManagedObjectReference moref)
        {
            // exclude unsupported types
            if (!(new List<string>() { "HostSystem", "VirtualMachine", "ResourcePool" }.Contains(moref.type))) return;
            if (!VCenter.entity_cache.ContainsKey(moref) || !VCenter.entity_cache[moref].ContainsKey("pspec"))
            {
                RetrievePerfInfo(moref);
                // init perf metric cache
                VCenter.entity_cache[moref]["perf"] = new Dictionary<string, Metric>();
            }
            if (!VCenter.entity_cache[moref].ContainsKey("perf"))
                VCenter.entity_cache[moref]["perf"] = new Dictionary<string, Metric>();
            Dictionary<string, Metric> perf_cache = (Dictionary<string, Metric>)VCenter.entity_cache[moref]["perf"];

            //invoke qp
            PerfQuerySpec spec = VCenter.entity_cache[moref]["pspec"];
            if (null == spec) return;

            Dictionary<int, PerfCounterInfo> counters = VCenter.entity_cache[moref]["pcs"];
            PerfEntityMetricBase[] values = VCenter.service.QueryPerf(VCenter.perfMgr, new PerfQuerySpec[] { spec });

            if (values != null)
            {
                foreach (PerfEntityMetricBase v in values)
                {
                    PerfMetricSeries[] vs = ((PerfEntityMetric)v).value;
                    PerfSampleInfo[] info = ((PerfEntityMetric)v).sampleInfo;
                    Console.WriteLine("虚拟机: {0} 性能计数时间: {1}", Get(moref, "name"), info[0].timestamp.ToLocalTime());
                    for (int i=0; i<vs.Length; ++i)
                    {
                        if (vs[i].GetType().Name == "PerfMetricIntSeries")
                        {
                            PerfMetricIntSeries series = (PerfMetricIntSeries)vs[i];
                            PerfCounterInfo pci = counters[series.id.counterId];
                            if (pci != null)
                            {
                                Metric met = BuildPerfMetric(moref, pci, ((PerfMetricIntSeries)series).value[0], info[0].timestamp.ToLocalTime(), spec.metricId[i].instance);
                                string cache_name = PerfMetricFullName(spec.metricId[i].instance.Replace('/', '_'), pci.groupInfo.key, pci.nameInfo.key);
                                perf_cache[cache_name] = met;
                                VCenter.publish(met);
//                                Console.WriteLine("{0}\t{1}\t{2}\t{3} = \t{4}",
  //                                                  met.tags["mo_type"], met.tags["mo"], met.tags["inst"], met.name, met.value);
                            }
                                
                        }
                    }
               //     Console.WriteLine("----------------------------");
                }
            }
        }

        // aggregated perf statistics
        public static int CountPerfStat(IEnumerable<ManagedObjectReference> mo_list, string fullname, string method = "sum")
        {
            var items = from x in mo_list
                        where VCenter.entity_cache[x]["perf"].ContainsKey(fullname)
                        select VCenter.entity_cache[x]["perf"][fullname].value;

            int ret = 0;
            switch (method)
            {
                case "sum": ret = (int)items.Sum(x => (decimal)x); break;
                case "average": ret = (int)items.Average(x => (decimal)x); break;
                case "max": ret = items.Max(); break;
            }

            return ret;
        }

        public static void UpdatePerfStat()
        {
            var summary = MonitorPlugin.Helper.info.platform_data["summary_metric"];
            foreach (var item in summary)
            {
                foreach (var kv in VCenter.entity_cache) if (kv.Key.type == item.Value["entity"].ToString())
                {
                    decimal value = CountPerfStat(kv.Value[item.Value["key"].ToString()], item.Value["metric_fullname"].ToString(), item.Value["method"].ToString());
                    Metric met = new Metric()
                    {
                        name = item.Name,
                        type = "metric",
                        ts = MonitorPlugin.Helper.default_timestamp(),
                        value = value,
                        tags = new Dictionary<string, string>()
                        {
                            { "mo", Get(kv.Key, "name") },
                            { "mo_type", kv.Key.type },
                            { "ref", kv.Key.Value },
                        }
                    };
                    VCenter.publish(met);
                }
                    
            }
        }
        // query methods
        
        // find moref by name
        public static ManagedObjectReference get_moref_by_name(string name)
        {
            var ret = from k in VCenter.entity_props
                      where Get(k.Key, "name") == name
                      select k.Key;
            return ret.First();
        }

        // find host of a vm
        public static ManagedObjectReference get_vm_host(ManagedObjectReference vm)
        {
            var ret = from k in VCenter.entity_cache
                      where k.Key.type == "HostSystem" && ((ManagedObjectReference[])k.Value["vm"]).ToList().Contains(vm, new MorefCmp())
                      select k.Key;
            return ret.First();
        }
    }
}
