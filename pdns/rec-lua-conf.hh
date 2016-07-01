#pragma once
#include "sholder.hh"
#include "sortlist.hh"
#include "filterpo.hh"
#include "remote_logger.hh"

class LuaConfigItems 
{
public:
  LuaConfigItems();
  SortList sortlist;
  DNSFilterEngine dfe;
  map<DNSName,DSRecordContent> dsAnchors;
  map<DNSName,std::string> negAnchors;
  std::shared_ptr<RemoteLogger> protobufServer{nullptr};
};

extern GlobalStateHolder<LuaConfigItems> g_luaconfs;
void loadRecursorLuaConfig(const std::string& fname);

