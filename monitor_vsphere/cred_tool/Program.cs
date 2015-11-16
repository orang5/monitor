using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Web.Services.Protocols;
using VMware.Security.CredentialStore;

namespace cred_tool
{
    public class cred_tool
    {
        private static AppUtil.AppUtil cb = null;

        public void CreateNewUser()
        {
                ICredentialStore csObj = CredentialStoreFactory.CreateCredentialStore();
             //   var createUserResult = csObj.AddPassword(GetServerName(), userName, password.ToCharArray());
        }

        public static void Main(String[] args)
        {
            try
            {
                if (args.Length != 3)
                    Console.WriteLine("usage: cred_tool [servername] [username] [password]");
                else
                {
                    string servername = args[0];
                    string username = args[1];
                    string password = args[2];

                    Console.WriteLine("服务器 {0} 用户名 {1} 口令 {2}", servername, username, password);
                    ICredentialStore cs = CredentialStoreFactory.CreateCredentialStore();
                    cs.AddPassword(servername, username, password.ToCharArray());
                    Console.WriteLine("成功保存口令");
                    Console.WriteLine(cs.GetPassword(servername, username));
                }
            }
            catch (Exception e)
            {
                Console.WriteLine(e);
            }

            Console.WriteLine("Press <Enter> to exit...");
            Console.Read();
        }
    }
}
