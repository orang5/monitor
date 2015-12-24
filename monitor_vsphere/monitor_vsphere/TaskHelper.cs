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
                    ret[kv.Key] = kv.Value;
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

        public static void BeginPowerOn(ManagedObjectReference vm, ManagedObjectReference host, 
            Dictionary<string, string> tags = null)
        {
            ManagedObjectReference task = VCenter.service.PowerOnVM_Task(vm, host);
            if (task != null)
            {
                Console.WriteLine("***  打开 {0} 的电源 ***", vm.Value);
                VMTask worker = WaitForTask;
                Dictionary<string, dynamic> taskinfo = new Dictionary<string, dynamic>();
                if (tags != null)
                    foreach (var kv in tags) taskinfo[kv.Key] = kv.Value;

                taskinfo["vm"] = vm;
                taskinfo["host"] = host;
                taskinfo["task"] = task;
                taskinfo["op"] = "poweron";
                taskinfo["delegate"] = worker;

                worker.BeginInvoke(task, TaskCompleted, taskinfo);
            }
        }

        public static void ProcessTask(Dictionary<string, string> args)
        {
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
            Console.WriteLine("JID: {0} 操作: {1} VM: {2} 主机: {3}", job_id, op, vm_name, hostref.Value);
            
            switch (op)
            {
                case "poweron": BeginPowerOn(vmref, hostref, args); break;
            }

        }

    }
}
