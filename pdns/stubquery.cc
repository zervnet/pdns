#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
#include "arguments.hh"
#include "dnsrecords.hh"
#include "dns_random.hh"
#include "stubresolver.hh"
#include "statbag.hh"

StatBag S;

ArgvMap &arg()
{
  static ArgvMap theArg;
  return theArg;
}

void usage() {
  cerr<<"stubquery"<<endl;
  cerr<<"Syntax: stubquery QUESTION [QUESTION-TYPE]"<<endl;
}

int main(int argc, char** argv)
try
{
  DNSName qname;
  QType qtype;

  for(int i=1; i<argc; i++) {
    if ((string) argv[i] == "--help") {
      usage();
      exit(EXIT_SUCCESS);
    }

    if ((string) argv[i] == "--version") {
      cerr<<"stubquery "<<VERSION<<endl;
      exit(EXIT_SUCCESS);
    }
  }

  if(argc < 2) {
    usage();
    exit(EXIT_FAILURE);
  }

  ::arg().set("recursor","If recursion is desired, IP address of a recursing nameserver")="no"; 

  reportAllTypes();
  dns_random_init("0123456789abcdef");
  stubParseResolveConf();

  vector<DNSResourceRecord> ret;

  int res=stubDoResolve(argv[1], DNSRecordContent::TypeToNumber(argv[2]), ret);

  cout<<"res: "<<res<<endl;
  for(const auto& r : ret) {
    cout<<r.getZoneRepresentation()<<endl;
  }
}
catch(std::exception &e)
{
  cerr<<"Fatal: "<<e.what()<<endl;
}
catch(PDNSException &e)
{
  cerr<<"Fatal: "<<e.reason<<endl;
}
