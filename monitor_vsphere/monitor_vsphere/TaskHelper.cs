using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using Vim25Api;
using AppUtil;
using System.Web.Services.Protocols;
using MonitorPlugin;
using Newtonsoft.Json;

namespace monitor_vsphere
{
    class TaskHelper
    {
        public static string message = "";

        public delegate bool VMTask(ManagedObjectReference moref);

        // use BeginInvoke to call.
        public static bool WaitForTask(ManagedObjectReference task_ref)
        {
            try
            {
                object[] result = VCenter.su.WaitForValues(
                    task_ref, new string[] { "info.state", "info.error" }, new string[] { "state" },
                    new object[][] { new object[] { TaskInfoState.success, TaskInfoState.error } });
                message = (string)result[1];
                if (message != null) Console.WriteLine(message);
                return (result[0].Equals(TaskInfoState.success));
            }
            catch (Exception e)
            {
                message = e.Message;
                return false;
            }
        }

        public static Dictionary<string, string> ConvertResult(Dictionary<string, dynamic> d)
        {
            Dictionary<string, string> ret = new Dictionary<string, string>();
            foreach (var kv in d)
                try
                {
                    ret[kv.Key] = kv.Value.ToString();
                }
                catch { }
            return ret;
        }

        public static void SendResult(object d)
        {
            MonitorPlugin.MQ.publish_con(JsonConvert.SerializeObject(d));
        }

        public static void TaskCompleted(IAsyncResult result)
        {
            if (result == null) return;
            Dictionary<string, dynamic> ret = (Dictionary<string, dynamic>)result.AsyncState;
            bool success = ((VMTask)ret["delegate"]).EndInvoke(result);
            Console.WriteLine("*** 操作完成 *** ");
            Console.WriteLine("VM: {0} 操作: {1} 结果: {2} {3}",
                                ((ManagedObjectReference)ret["vm"]).Value, (string)ret["op"], success, message);
            Console.WriteLine("报告结果...");
            ret["result"] = success.ToString();
            ret["error"] = message;
            SendResult(ConvertResult(ret));
            Console.WriteLine("更新Inventory...");
            // retrieve host/vm list
            PropHelper.RetrieveAllEntities();
            PropHelper.RetrieveArrays();
            // print/send entity info
            PropHelper.BuildPropMetric();
        }

        public static VMTask BeginTask(ManagedObjectReference task, Dictionary<string, dynamic> tags = null, bool callback=true)
        {
            if (task != null)
            {
                VMTask worker = WaitForTask;
                if (tags == null) tags = new Dictionary<string, dynamic>();
                tags["task"] = task;
                tags["delegate"] = worker;
                if (callback)
                    worker.BeginInvoke(task, TaskCompleted, tags);
                else
                    worker.BeginInvoke(task, null, tags);
                return worker;
            }
            return null;
        }

        public static void ProcessTask(Dictionary<string, string> args)
        {
            ManagedObjectReference task;

            if (!args.ContainsKey("op") || !args.ContainsKey("job_id")) return;
            string op = args["op"];
            if (op == "test")
            {
                Metric met = PropHelper.BuildBasicInfo();
                Dictionary<string, dynamic> d = met.message_dict;
                d["job_id"] = args["job_id"];
                SendResult(d);
                return;
            }
            string vm_name = args["name"];
            string job_id = args["job_id"];
            
            // find vm moref & host moref from vm name
            var vmref = PropHelper.get_moref_by_name(vm_name);
            var hostref = PropHelper.get_vm_host(vmref);
            Dictionary<string, dynamic> info = new Dictionary<string, dynamic>();
            foreach (var kv in args) info[kv.Key] = kv.Value;
            info["vm"] = vmref;
            info["host"] = hostref;
            Console.WriteLine("JID: {0} 操作: {1} VM: {2} 主机: {3}", job_id, op, vm_name, hostref.Value);

            // migrate args
            string pool_name, target_name, ds_name;
            ManagedObjectReference poolref, targetref, dsref;
            VirtualMachinePowerState st = VirtualMachinePowerState.poweredOn;
            VirtualMachineMovePriority pr = VirtualMachineMovePriority.defaultPriority;
            VirtualMachineConfigSpec conf_spec;
            try
            {
                switch (op)
                {
                    case "poweron":
                        task = VCenter.service.PowerOnVM_Task(vmref, hostref);
                        BeginTask(task, info);
                        break;
                    case "poweroff":
                        task = VCenter.service.PowerOffVM_Task(vmref);
                        BeginTask(task, info);
                        break;
                    case "suspend":
                        task = VCenter.service.SuspendVM_Task(vmref);
                        BeginTask(task, info);
                        break;
                    case "reset":
                        task = VCenter.service.ResetVM_Task(vmref);
                        BeginTask(task, info);
                        break;
                    case "reboot":
                        VCenter.service.RebootGuest(vmref);
                        info["result"] = true;
                        Console.WriteLine("*** 操作完成 *** ");
                        SendResult(ConvertResult(info));
                        break;
                    case "shutdown":
                        VCenter.service.ShutdownGuest(vmref);
                        info["result"] = true;
                        Console.WriteLine("*** 操作完成 *** ");
                        SendResult(ConvertResult(info));
                        break;
                    case "standby":
                        VCenter.service.StandbyGuest(vmref);
                        info["result"] = true;
                        Console.WriteLine("*** 操作完成 *** ");
                        SendResult(ConvertResult(info));
                        break;

                    case "migrate":
                        pool_name = args["pool"];
                        target_name = args["target"];
                        poolref = PropHelper.get_moref_by_name(pool_name);
                        targetref = PropHelper.get_moref_by_name(target_name);
                        info["pool"] = poolref;
                        info["target"] = targetref;

                        task = VCenter.service.MigrateVM_Task(vmref, poolref, targetref, pr, st, true);
                        BeginTask(task, info);
                        break;
                    case "relocate":
                        pool_name = args["pool"];
                        target_name = args["target"];
                        ds_name = args["datastore"];
                        poolref = PropHelper.get_moref_by_name(pool_name);
                        targetref = PropHelper.get_moref_by_name(target_name);
                        dsref = PropHelper.get_moref_by_name(ds_name);
                        info["pool"] = poolref;
                        info["target"] = targetref;
                        info["ds"] = dsref;
                        task = VCenter.service.RelocateVM_Task(vmref,
                            new VirtualMachineRelocateSpec() { datastore = dsref, host = targetref, pool = poolref }, pr, true
                            );
                        BeginTask(task, info);
                        break;
                    case "check_migrate":
                        pool_name = args["pool"];
                        target_name = args["target"];
                        poolref = PropHelper.get_moref_by_name(pool_name);
                        targetref = PropHelper.get_moref_by_name(target_name);
                        info["pool"] = poolref;
                        info["target"] = targetref;
                        info["result"] = (QueryVMotion(vmref, hostref, targetref) && CheckMigrate(vmref, targetref, poolref));
                        Console.WriteLine("*** 操作完成 *** ");
                        SendResult(ConvertResult(info));
                        break;
                    case "check_relocate":
                        pool_name = args["pool"];
                        target_name = args["target"];
                        ds_name = args["datastore"];
                        poolref = PropHelper.get_moref_by_name(pool_name);
                        targetref = PropHelper.get_moref_by_name(target_name);
                        dsref = PropHelper.get_moref_by_name(ds_name);
                        info["pool"] = poolref;
                        info["target"] = targetref;
                        info["ds"] = dsref;
                        info["result"] = (QueryVMotion(vmref, hostref, targetref) && CheckRelocation(vmref, targetref, poolref, dsref));
                        Console.WriteLine("*** 操作完成 *** ");
                        SendResult(ConvertResult(info));
                        break;
                    case "reconf_mem":
                        conf_spec = new VirtualMachineConfigSpec() {
                            memoryAllocation = GetShares("custom", int.Parse(args["value"]))
                        };
                        info["result"] = WaitForTask(VCenter.service.ReconfigVM_Task(vmref, conf_spec));
                        Console.WriteLine("*** 操作完成 *** ");
                        SendResult(ConvertResult(info));
                        break;

                    case "reconf_numcpu":
                        conf_spec = new VirtualMachineConfigSpec()
                        {
                            numCPUs = int.Parse(args["value"])
                        };
                        info["result"] = WaitForTask(VCenter.service.ReconfigVM_Task(vmref, conf_spec));
                        Console.WriteLine("*** 操作完成 *** ");
                        SendResult(ConvertResult(info));
                        break;
                    case "reconf_disk":
                        var vd_spec = GetVDiskSpec(vmref);
                        //info["result"] = WaitForTask(VCenter.service.);
                        Console.WriteLine("*** 操作完成 *** ");
                        SendResult(ConvertResult(info));
                        break;
                }
            }
            catch (Exception e)
            {
                info["result"] = false;
                info["error"] = e.Message;
                SendResult(ConvertResult(info));
            }
        }

        public static bool QueryVMotion(ManagedObjectReference vmref, ManagedObjectReference host, ManagedObjectReference target)
        {
            return WaitForTask(VCenter.service.QueryVMotionCompatibilityEx_Task(
                VCenter.sic.vmProvisioningChecker,
                new ManagedObjectReference[] { vmref },
                new ManagedObjectReference[] { host, target }
                ));
        }

        public static bool CheckMigrate(ManagedObjectReference vmref, ManagedObjectReference target, ManagedObjectReference poolref)
        {
            return WaitForTask(VCenter.service.CheckMigrate_Task(
                VCenter.sic.vmProvisioningChecker, vmref, target, poolref, VirtualMachinePowerState.poweredOff, false, null));
        }

        public static bool CheckRelocation(ManagedObjectReference vmref, ManagedObjectReference host,
                                           ManagedObjectReference poolref, ManagedObjectReference dsref)
        {
            return WaitForTask(VCenter.service.CheckRelocate_Task(
                VCenter.sic.vmProvisioningChecker, vmref, 
                new VirtualMachineRelocateSpec() { datastore = dsref, host = host, pool = poolref },
                null));
        }

        public static ResourceAllocationInfo GetShares(string level="custom", int value=0)
        {
            List<string> levels = new List<string>() { "low", "normal", "high", "custom" };
            return new ResourceAllocationInfo() {
                shares = new SharesInfo() { level = (SharesLevel)levels.IndexOf(level), shares = value }
            };
        }

        public static VirtualDiskConfigSpec GetVDiskSpec(ManagedObjectReference vmref)
        {
            VirtualDiskConfigSpec ret = new VirtualDiskConfigSpec();
            VirtualMachineConfigInfo conf = (VirtualMachineConfigInfo)VCenter.su.GetDynamicProperty(vmref, "config");
            return ret;
        }

    }
}
