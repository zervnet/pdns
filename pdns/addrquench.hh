#ifndef PDNS_ADDRQUENCH_HH
#define PDNS_ADDRQUENCH_HH
#include "lock.hh"
#include "iputils.hh"
#include <set>
#include <boost/multi_index_container.hpp>
using namespace boost::multi_index;

class AddressQuencher
{
public:
  AddressQuencher();
  void insert(const ComboAddress&addr, int ttl);
  bool present(const ComboAddress&addr, time_t now);
  void clean();
  vector<ComboAddress> dump();

  struct Entry
  {
    Entry(const ComboAddress& addr_, time_t ttd_) : addr(addr_), ttd(ttd_){}
    ComboAddress addr;
    time_t ttd;
    time_t getTTD() const
    {
      return ttd;
    }
  };
  uint64_t size();
private:
  
  struct TimeTag {};

  typedef multi_index_container<
    Entry,
    indexed_by<
      ordered_unique<
        member<Entry, ComboAddress, &Entry::addr>, ComboAddress::addressOnlyLessThan
      >,
      ordered_non_unique<
        tag<TimeTag>,
        member<Entry, time_t, &Entry::ttd>
      >
    >
  > store_t; 

  store_t d_store;
  pthread_rwlock_t d_lock;
};

#endif
