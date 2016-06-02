#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
#include "statbag.hh"
#include "logger.hh"
#include "iputils.hh"
#include "sstuff.hh"
#include "arguments.hh"
#include "common_startup.hh"

#include "namespaces.hh"

void* carbonDumpThread(void*)
try
{
  extern StatBag S;

  string hostname=arg()["carbon-ourname"];
  if(hostname.empty()) {
    char tmp[80];
    memset(tmp, 0, sizeof(tmp));
    gethostname(tmp, sizeof(tmp));
    char *p = strchr(tmp, '.');
    if(p) *p=0;
    hostname=tmp;
    boost::replace_all(hostname, ".", "_");
  }

  vector<string> carbonServers;
  stringtok(carbonServers, arg()["carbon-server"], ", ");

  for(;;) {
    if(carbonServers.empty()) {
      sleep(1);
      continue;
    }

    string msg;
    vector<string> entries = S.getEntries();
    ostringstream str;
    time_t now=time(0);
    for(const string& entry : entries) {
      str<<"pdns."<<hostname<<".auth."<<entry<<' '<<S.read(entry)<<' '<<now<<"\r\n";
    }
    msg = str.str();

    for (const auto& carbonServer : carbonServers) {
      ComboAddress remote(carbonServer, 2003);
      Socket s(remote.sin4.sin_family, SOCK_STREAM);
      s.setNonBlocking();
      s.connect(remote);  // we do the connect so the attempt happens while we gather stats

      try {
        writen2WithTimeout(s.getHandle(), msg.c_str(), msg.length(), 2);
      } catch (runtime_error &e){
        L<<Logger::Warning<<"Unable to write data to carbon server at "<<remote.toStringWithPort()<<": "<<e.what()<<endl;
        continue;
      }
    }
    sleep(arg().asNum("carbon-interval"));
  }
  return 0;
}
catch(std::exception& e)
{
  L<<Logger::Error<<"Carbon thread died: "<<e.what()<<endl;
  return 0;
}
catch(PDNSException& e)
{
  L<<Logger::Error<<"Carbon thread died, PDNSException: "<<e.reason<<endl;
  return 0;
}
catch(...)
{
  L<<Logger::Error<<"Carbon thread died"<<endl;
  return 0;
}
