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
        }

        public static void BeginTask(ManagedObjectReference task, Dictionary<string, dynamic> tags = null)
        {
            if (task != null)
            {
                VMTask worker = WaitForTask;
                tags["task"] = task;
                tags["delegate"] = worker;
                worker.BeginInvoke(task, TaskCompleted, tags);
            }
        }

        public static void ProcessTask(Dictionary<string, string> args)
        {
            ManagedObjectReference task;

            if (!args.ContainsKey("op") || !args.ContainsKey("job_id")) return;
            string op = args["op"];
            if (op == "test")
            {
                Metric met = PropHelper.BuildPlatformInfo();
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
                        //task = VCenter.service.MigrateVM_Task(
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

    }
}
