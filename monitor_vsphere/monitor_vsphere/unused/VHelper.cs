using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Vim25Api;
using AppUtil;
using VMware.Security.CredentialStore;
using System.Web.Services.Protocols;

namespace monitor_vsphere
{
    class VHelper
    {
        public static string center;
        public static string username;
        public static AppUtil.AppUtil cb;
        public static List<string> hostSystemAttributesArr = new List<string>();

        static VimService service;
        static ServiceContent sic;
        static ManagedObjectReference perfMgr;

        public static void displayBasics(string host)
        {
            service = cb.getConnection()._service;
            sic = cb.getConnection()._sic;
            perfMgr = sic.perfManager;

            getIntervals(perfMgr, service);
            getCounters(perfMgr, service);
            ManagedObjectReference hostmor
               = cb.getServiceUtil().GetDecendentMoRef(null,
                                                      "HostSystem",
                                                       host);
            if (hostmor == null)
            {
                Console.WriteLine("Host " + host + " not found");
                return;
            }
            getQuerySummary(perfMgr, hostmor, service);
            getQueryAvailable(perfMgr, hostmor, service);
        }

        private static void getIntervals(ManagedObjectReference perfMgr, VimService service)
        {
            Object property = getProperty(service, perfMgr, "historicalInterval");
            PerfInterval[] intervals = (PerfInterval[])property;
            // PerfInterval [] intervals = arrayInterval.perfInterval;
            Console.WriteLine("Performance intervals (" + intervals.Length + "):");
            Console.WriteLine("---------------------");
            for (int i = 0; i != intervals.Length; ++i)
            {
                PerfInterval interval = intervals[i];
                Console.WriteLine(i + ": " + interval.name);
                Console.WriteLine(" -- period = " + interval.samplingPeriod);
                Console.WriteLine(", length = " + interval.length);
            }
            Console.WriteLine();
        }
        private static void getCounters(ManagedObjectReference perfMgr, VimService service)
        {
            Object property = getProperty(service, perfMgr, "perfCounter");
            PerfCounterInfo[] counters = (PerfCounterInfo[])property;
            //  PerfCounterInfo[] counters = arrayCounter.getPerfCounterInfo();
            Console.WriteLine("Performance counters (averages only):");
            Console.WriteLine("-------------------------------------");
            foreach (PerfCounterInfo counter in counters)
            {
                if (counter.rollupType == PerfSummaryType.average)
                {
                    ElementDescription desc = counter.nameInfo;
                    Console.WriteLine(desc.label + ": " + desc.summary);
                }
            }
            Console.WriteLine();
        }

        private static void getQuerySummary(ManagedObjectReference perfMgr,
                                     ManagedObjectReference hostmor,
                                     VimService service)
        {
            PerfProviderSummary summary = service.QueryPerfProviderSummary(perfMgr, hostmor);
            Console.WriteLine("Host perf capabilities:");
            Console.WriteLine("----------------------");
            Console.WriteLine("  Summary supported: " + summary.summarySupported);
            Console.WriteLine("  Current supported: " + summary.currentSupported);
            if (summary.currentSupported)
            {
                Console.WriteLine("  Current refresh rate: " + summary.refreshRate);
            }
            Console.WriteLine();
        }

        private static void getQueryAvailable(ManagedObjectReference perfMgr,
                                       ManagedObjectReference hostmor,
                                       VimService service)
        {
            DateTime end = DateTime.Now;
            DateTime start = end.AddHours(-12);

            PerfMetricId[] metricIds
               = service.QueryAvailablePerfMetric(perfMgr, hostmor, start, true, end, true, 20, true);
            int[] ids = new int[metricIds.Length];
            for (int i = 0; i != metricIds.Length; ++i)
            {
                ids[i] = metricIds[i].counterId;
            }
            PerfCounterInfo[] counters = service.QueryPerfCounter(perfMgr, ids);
            Console.WriteLine("Available metrics for host (" + metricIds.Length + "):");
            Console.WriteLine("--------------------------");
            for (int i = 0; i != metricIds.Length; ++i)
            {
                String label = counters[i].nameInfo.label;
                String instance = metricIds[i].instance;
                Console.WriteLine("   " + label);
                if (instance.Length != 0)
                {
                    Console.WriteLine(" [" + instance + "]");
                }
                Console.WriteLine();
            }
            Console.WriteLine();
        }

        private static Object[] getProperties(VimService service,
                                  ManagedObjectReference moRef,
                                  String[] properties)
        {
            PropertySpec pSpec = new PropertySpec();
            pSpec.type = moRef.type;
            pSpec.pathSet = properties;
            ObjectSpec oSpec = new ObjectSpec();
            oSpec.obj = moRef;
            PropertyFilterSpec pfSpec = new PropertyFilterSpec();
            pfSpec.propSet = (new PropertySpec[] { pSpec });
            pfSpec.objectSet = (new ObjectSpec[] { oSpec });
            ObjectContent[] ocs
               = service.RetrieveProperties(sic.propertyCollector,
                                            new PropertyFilterSpec[] { pfSpec });
            Object[] ret = new Object[properties.Length];
            if (ocs != null)
            {
                for (int i = 0; i < ocs.Length; ++i)
                {
                    ObjectContent oc = ocs[i];
                    DynamicProperty[] dps = oc.propSet;
                    if (dps != null)
                    {
                        for (int j = 0; j < dps.Length; ++j)
                        {
                            DynamicProperty dp = dps[j];
                            for (int p = 0; p < ret.Length; ++p)
                            {
                                if (properties[p].Equals(dp.name))
                                {
                                    ret[p] = dp.val;
                                }
                            }
                        }
                    }
                }
            }
            return ret;
        }

        private static Object getProperty(VimService service,
                              ManagedObjectReference moRef,
                              String prop)
        {
            Object[] props = getProperties(service, moRef, new String[] { prop });
            if (props.Length > 0)
            {
                return props[0];
            }
            else
            {
                return null;
            }
        }

        public static void SetHostSystemAttributesList()
        {
            hostSystemAttributesArr.Add("name");
            hostSystemAttributesArr.Add("config.product.productLineId");
            hostSystemAttributesArr.Add("summary.hardware.cpuMhz");
            hostSystemAttributesArr.Add("summary.hardware.numCpuCores");
            hostSystemAttributesArr.Add("summary.hardware.cpuModel");
            hostSystemAttributesArr.Add("summary.hardware.uuid");
            hostSystemAttributesArr.Add("summary.hardware.vendor");
            hostSystemAttributesArr.Add("summary.hardware.model");
            hostSystemAttributesArr.Add("summary.hardware.memorySize");
            hostSystemAttributesArr.Add("summary.hardware.numNics");
            hostSystemAttributesArr.Add("summary.config.name");
            hostSystemAttributesArr.Add("summary.config.product.osType");
            hostSystemAttributesArr.Add("summary.config.vmotionEnabled");
            hostSystemAttributesArr.Add("summary.quickStats.overallCpuUsage");
            hostSystemAttributesArr.Add("summary.quickStats.overallMemoryUsage");
        }

        public static void PrintHostProductDetails()
        {
            SetHostSystemAttributesList();
            string prop = null;
            Dictionary<ManagedObjectReference, Dictionary<string, object>> hosts =
                cb._svcUtil.getEntitiesByType("HostSystem", hostSystemAttributesArr.ToArray());
            foreach (KeyValuePair<ManagedObjectReference, Dictionary<string, object>> host in hosts)
            {
                foreach (KeyValuePair<string, object> hostProps in host.Value)
                {
                    prop = hostProps.Key;
                    Console.WriteLine(prop + " : " + hostProps.Value);
                }
                Console.WriteLine("***************************************************************");
            }
        }
        /// <summary>
        /// Retrieve inventory from the given root 
        /// </summary>
        public static void PrintInventory(string type, string property)
        {
            try
            {
                Console.WriteLine("Fetching Inventory");
                // folder, name, childentity
                string[][] typeInfo = new string[][] { new string[] { type, property }, };
                // Retrieve Contents recursively starting at the root folder 
                // and using the default property collector.            
                ObjectContent[] ocary =
                   cb.getServiceUtil().GetContentsRecursively(null, null, typeInfo, true);
                ObjectContent oc = null;
                ManagedObjectReference mor = null;
                DynamicProperty[] pcary = null;
                DynamicProperty pc = null;
                for (int oci = 0; oci < ocary.Length; oci++)
                {
                    oc = ocary[oci];
                    mor = oc.obj;
                    pcary = oc.propSet;
                    cb.log.LogLine("Object Type : " + mor.type);
                    cb.log.LogLine("Reference Value : " + mor.Value);
                    if (pcary != null)
                    {
                        for (int pci = 0; pci < pcary.Length; pci++)
                        {
                            pc = pcary[pci];
                            cb.log.LogLine("   Property Name : " + pc.name);
                            if (pc != null)
                            {
                                if (!pc.val.GetType().IsArray)
                                {
                                    cb.log.LogLine("   Property Value : " + pc.val);
                                }
                                else
                                {
                                    Array ipcary = (Array)pc.val;
                                    cb.log.LogLine("Val : " + pc.val);
                                    for (int ii = 0; ii < ipcary.Length; ii++)
                                    {
                                        object oval = ipcary.GetValue(ii);
                                        if (oval.GetType().Name.IndexOf("ManagedObjectReference") >= 0)
                                        {
                                            ManagedObjectReference imor = (ManagedObjectReference)oval;
                                            cb.log.LogLine("Inner Object Type : " + imor.type);
                                            cb.log.LogLine("Inner Reference Value : " + imor.Value);
                                        }
                                        else
                                        {
                                            cb.log.LogLine("Inner Property Value : " + oval);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                cb.log.LogLine("Done Printing Inventory");
                cb.log.LogLine("Browser : Successful Getting Contents");
            }

            catch (SoapException e)
            {
                Console.WriteLine("Browser : Failed Getting Contents");
                Console.WriteLine("Encountered SoapException");
                throw e;
            }
            catch (Exception e)
            {
                cb.log.LogLine("Browser : Failed Getting Contents");
                throw e;
            }

        }

        public static void PrintAboutInfo()
        {
            AboutInfo ai = cb.getConnection()._sic.about;
            Console.WriteLine("{0} {1}", ai.apiType, ai.version);
            Console.WriteLine(ai.fullName);
        }

        public static void connect()
        {
            try
            {
                center = VCenter.ipaddr; username = VCenter.username;
                ICredentialStore cs = CredentialStoreFactory.CreateCredentialStore();
                string pass = new string(cs.GetPassword(center, username));
                string url = "https://" + center + "/sdk/vimService";
                string[] args = {"--url", url,
                                 "--username", username,
                                 "--password", pass, 
                                 "--disablesso", "--ignorecert" };

                cb = AppUtil.AppUtil.initialize("monitor_vsphere", args);
                cb.connect();
                VCenter.cb = cb;
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
    }
}
