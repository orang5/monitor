using System;
using System.Collections.Generic;
using System.Text;
using System.Diagnostics;
using System.IO;

using VixCOM;
using MonitorPlugin;

namespace VixPlugin
{
    public enum POWERSTATE { off_ing = 1, off = 2, on_ing = 4, on = 8, tools_running = 64 };
    public enum VMSTATE { init = 1, run = 2, login = 8, down = 64 };

    class VM
    {
        public string path;
        public IVixHandle handle;

        public VMSTATE state = VMSTATE.init;

        private Dictionary<string, dynamic> _props;
        public Dictionary<string, dynamic> props
        {
            get
            {
                if (_props == null) UpdateProps();
                return _props;
            }
        }
        public void UpdateProps()
        {
            _props = new Dictionary<string, dynamic>();
            int[] propids = new int[] { Constants.VIX_PROPERTY_VM_NUM_VCPUS, Constants.VIX_PROPERTY_VM_VMX_PATHNAME,
                                        Constants.VIX_PROPERTY_VM_MEMORY_SIZE, Constants.VIX_PROPERTY_VM_POWER_STATE,
                                        Constants.VIX_PROPERTY_VM_TOOLS_STATE, Constants.VIX_PROPERTY_VM_SUPPORTED_FEATURES};
            object p = null;
            ulong err = handle.GetProperties(propids, ref p);
            object[] result = (object [])p;
            Debug.Assert(err == 0);

            _props["vcpu"] = (int)result[0];
            _props["path"] = (string)result[1];
            _props["mem"] = (int)result[2];
            _props["power"] = Enum.Parse(typeof(POWERSTATE), ((int)result[3]).ToString());
            _props["tool"] = (int)result[4];
            _props["features"] = result[5];
            _props["name"] = name;

            state = VMSTATE.run;
        }

        public string name { get { return Path.GetFileNameWithoutExtension(props["path"]); } }

        public void Login(string username, string password)
        {
            IVM hvm = (IVM)handle;
            Debug.WriteLine("wait for vmware-tools...", name);
            // Program.WaitJob(hvm.PowerOn(Constants.VIX_VMPOWEROP_LAUNCH_GUI, null, null), false);
            if (!((POWERSTATE)props["power"]).HasFlag(POWERSTATE.on))
            {
                Debug.Assert(false, "PowerState must be ON", "{0} power_state = {1}", name, (POWERSTATE)props["power"]);
            }
            Program.WaitJob(hvm.WaitForToolsInGuest(3, null), false);
            Debug.WriteLine("login...", name);
            Program.WaitJob(hvm.LoginInGuest(username, password, Constants.VIX_LOGIN_IN_GUEST_REQUIRE_INTERACTIVE_ENVIRONMENT, null), false);

            state |= VMSTATE.login;
        }

        public void Logout()
        {
            Debug.Assert((state & VMSTATE.login) !=0);
            Program.WaitJob(((IVM)handle).LogoutFromGuest(null), false);
            Debug.WriteLine("logged out");

            state &= ~VMSTATE.login;
        }

        public List<Dictionary<string, dynamic>> UpdateProcessList()
        {
            List<Dictionary<string, dynamic>> ret = new List<Dictionary<string, dynamic>>();
            IVM hvm = (IVM)handle;

            Debug.Assert(state.HasFlag(VMSTATE.login));
            IJob job = hvm.ListProcessesInGuest(0, null);
            ulong err = job.WaitWithoutResults();
            Debug.Assert(err == 0);

            Debug.WriteLine("update process list...", name);
            int n = job.GetNumProperties(Constants.VIX_PROPERTY_JOB_RESULT_ITEM_NAME);
            int[] propids = new int[] { Constants.VIX_PROPERTY_JOB_RESULT_ITEM_NAME,
                                        Constants.VIX_PROPERTY_JOB_RESULT_PROCESS_ID,
                                        Constants.VIX_PROPERTY_JOB_RESULT_PROCESS_COMMAND};
            for (int i = 0; i < n; i++)
            {
                Dictionary<string, dynamic> r = new Dictionary<string, dynamic>();
                object robj = null;
                err = job.GetNthProperties(i, propids, ref robj);
                Debug.Assert(err == 0);
                object[] rarray = (object[])robj;
                r["name"] = (string)rarray[0];
                r["pid"] = rarray[1];
                r["cmd"] = (string)rarray[2];
                ret.Add(r);

            }
            Program.CloseVixObject(job);
            return ret;
        }
    }

    class Program
    {
        static VixLibClass vix;
        static IHost host;
        static List<VM> vm = new List<VM>();

        public static void CloseVixObject(Object v)
        {
            try { ((IVixHandle2)v).Close(); }
            catch (Exception) { }
        }

        public static object WaitJob(IJob job, bool has_result=true)
        {
            object ret = null;
            ulong err;
            if (has_result)
                err = job.Wait(new int[] { Constants.VIX_PROPERTY_JOB_RESULT_HANDLE }, ref ret);
            else
                err = job.WaitWithoutResults();
            if (err != 0)
            {
                string msg = Encoding.UTF8.GetString(Encoding.Default.GetBytes(vix.GetErrorText(err, null)));
                Debug.WriteLine("job failed!, error {0} {1}", err, msg);
                Debug.Assert(err == 0, msg);
            }

            CloseVixObject(job);
            if (has_result)
                return ((object[])ret)[0];
            else return null;
        }

        class SearchCallback : ICallback
        {
            public void OnVixEvent(IJob job, int type, IVixHandle more)
            {
                ulong err;
                if (type == Constants.VIX_EVENTTYPE_FIND_ITEM)
                {
                    object ret = null;
                    err = more.GetProperties(new int[] { Constants.VIX_PROPERTY_FOUND_ITEM_LOCATION }, ref ret);
                    Debug.Assert(err == 0);
                    string pathname = (string)((object[])ret)[0];
                  //  Console.WriteLine(pathname);
                    VM vv = new VM();
                    vv.path = pathname;
                    if (!vm.Exists(x => x.path == pathname))
                        vm.Add(vv);
                    VM t = vm.Find(x => x.path == pathname);
                    t.state &= ~VMSTATE.down;
                }
                CloseVixObject(job);
            }
        }

        static void MetricWorker(Metric met)
        {
            string item = met.name.Split('.')[1];

            foreach (VM v in vm)
                if (!v.state.HasFlag(VMSTATE.down))
                {
                    if (item == "process_list")
                    {
                        if (!v.state.HasFlag(VMSTATE.login))
                            v.Login("dongyf", "whu");
                        met.value = v.UpdateProcessList();
                    }
                    else
                    {
                        met.value = v.props[item];
                    }

                    met.tags.Clear();
                    met.tags["vm_path"] = v.path;
                    met.ts["latest"] = Helper.to_timestamp(DateTime.Now);
                    MQ.publish(met.json_message);
                }
        }

        static void Main(string[] args)
        {
            vix = new VixLibClass();

            Helper.plugin_info("VixPlugin.json");
            MQ.setup_local_queue();
            
            // connect to host
            host = (IHost)WaitJob(vix.Connect(Constants.VIX_API_VERSION, Constants.VIX_SERVICEPROVIDER_VMWARE_WORKSTATION,
                                   null, 0, null, null, 0, null, null));

            bool flag = true;

            while (flag)
            {
                foreach (VM vv in vm)
                    vv.state |= VMSTATE.down;
                // update vm list
                WaitJob(host.FindItems(Constants.VIX_FIND_RUNNING_VMS, null, -1, new SearchCallback()), false);

                foreach (VM vv in vm) if (vv.state == VMSTATE.init)
                {
                    Debug.Print("new vm {0}", vv.path);
                    vv.handle = (IVixHandle)WaitJob(host.OpenVM(vv.path, null));
                    vv.state = VMSTATE.run;
                }

                Helper.update_metrics(MetricWorker, false);
                System.Threading.Thread.Sleep(2000);
            }
                // disconn
            host.Disconnect();

            Debug.WriteLine("Done.");
            Console.ReadKey();
        }
    }
}
