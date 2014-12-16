#include "addrquench.hh"
#include "cachecleaner.hh"
#include <boost/foreach.hpp>

AddressQuencher::AddressQuencher()
{
  pthread_rwlock_init(&d_lock, 0);
}

// this should be rare
void AddressQuencher::insert(const ComboAddress& addr, int ttl)
{
  Entry e(addr, time(0)+ttl);
  WriteLock wl(&d_lock);
  d_store.insert(e);
}

// this will be frequent;
bool AddressQuencher::present(const ComboAddress& addr, time_t now)
{
  ReadLock rl(&d_lock);
  store_t::const_iterator iter = d_store.find(addr);
  if(iter == d_store.end() || iter->ttd < now)
    return false;
  return true;
}

vector<ComboAddress> AddressQuencher::dump()
{
  vector<ComboAddress> ret;
  ret.reserve(d_store.size());
  time_t now=time(0);

  ReadLock rl(&d_lock);

  
  BOOST_FOREACH(const Entry& e, d_store) {
    if(e.ttd > now)
      ret.push_back(e.addr);
  }
  return ret;
}

uint64_t AddressQuencher::size()
{
  ReadLock rl(&d_lock);
  return d_store.size();
}

void AddressQuencher::clean()
{
  WriteLock wl(&d_lock);
  pruneCollection(d_store, 100000);
}
