using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using Vim25Api;
using AppUtil;
using System.Web.Services.Protocols;
using MonitorPlugin;

namespace monitor_vsphere
{
    class TaskHelper
    {
        public static string message;

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

        public static void TaskCompleted(IAsyncResult result)
        {
            if (result == null) return;
            Dictionary<string, dynamic> ret = (Dictionary<string, dynamic>)result.AsyncState;
            bool success = ((VMTask)ret["delegate"]).EndInvoke(result);
            Console.WriteLine("*** Task Completed *** ");
            Console.WriteLine("VM: {0} op: {1} result: {2}",
                                ((ManagedObjectReference)ret["vm"]).Value, (string)ret["op"], success);
        }

        public static void BeginPowerOn(ManagedObjectReference vm, ManagedObjectReference host)
        {
            ManagedObjectReference task = VCenter.service.PowerOnVM_Task(vm, host);
            if (task != null)
            {
                Console.WriteLine("*** Power-On VM {0} on host {1} ***", vm.Value, host.Value);
                VMTask worker = WaitForTask;
                Dictionary<string, dynamic> taskinfo = new Dictionary<string, dynamic>();
                taskinfo["vm"] = vm;
                taskinfo["host"] = host;
                taskinfo["task"] = task;
                taskinfo["op"] = "poweron";
                taskinfo["delegate"] = worker;

                worker.BeginInvoke(task, TaskCompleted, taskinfo);
            }
        }

    }
}
