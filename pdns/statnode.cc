#include "statnode.hh"

StatNode::Stat StatNode::print(int depth, Stat newstat, bool silent) const
{
  if(!silent) {
    cout<<string(depth, ' ');
    cout<<name<<": "<<endl;
  }
  Stat childstat;
  childstat.queries += s.queries;
  childstat.noerrors += s.noerrors;
  childstat.nxdomains += s.nxdomains;
  childstat.servfails += s.servfails;
  childstat.drops += s.drops;
  if(children.size()>1024 && !silent) {
    cout<<string(depth, ' ')<<name<<": too many to print"<<endl;
  }
  for(const children_t::value_type& child :  children) {
    childstat=child.second.print(depth+8, childstat, silent || children.size()>1024);
  }
  if(!silent || children.size()>1)
    cout<<string(depth, ' ')<<childstat.queries<<" queries, " << 
      childstat.noerrors<<" noerrors, "<< 
      childstat.nxdomains<<" nxdomains, "<< 
      childstat.servfails<<" servfails, "<< 
      childstat.drops<<" drops"<<endl;

  newstat+=childstat;

  return newstat;
}


void  StatNode::visit(visitor_t visitor, Stat &newstat, int depth) const
{
  Stat childstat;
  childstat.queries += s.queries;
  childstat.noerrors += s.noerrors;
  childstat.nxdomains += s.nxdomains;
  childstat.servfails += s.servfails;
  childstat.drops += s.drops;
  childstat.remotes = s.remotes;
  
  Stat selfstat(childstat);


  for(const children_t::value_type& child :  children) {
    child.second.visit(visitor, childstat, depth+8);
  }

  visitor(this, selfstat, childstat);

  newstat+=childstat;
}


void StatNode::submit(const DNSName& domain, int rcode, const ComboAddress& remote)
{
  //  cerr<<"FIRST submit called on '"<<domain<<"'"<<endl;
  vector<string> tmp = domain.getRawLabels();
  if(tmp.empty())
    return;

  deque<string> parts;
  for(auto const i : tmp) {
    parts.push_back(i);
  }
  children[parts.back()].submit(parts, "", rcode, remote);
}

/* www.powerdns.com. -> 
   .                 <- fullnames
   com.
   powerdns.com
   www.powerdns.com. 
*/

void StatNode::submit(deque<string>& labels, const std::string& domain, int rcode, const ComboAddress& remote)
{
  if(labels.empty())
    return;
  //  cerr<<"Submit called for domain='"<<domain<<"': ";
  //  for(const std::string& n :  labels) 
  //    cerr<<n<<".";
  //  cerr<<endl;
  if(name.empty()) {

    name=labels.back();
    //    cerr<<"Set short name to '"<<name<<"'"<<endl;
  }
  else 
    ; //    cerr<<"Short name was already set to '"<<name<<"'"<<endl;

  if(labels.size()==1) {
    fullname=name+"."+domain;
    //    cerr<<"Hit the end, set our fullname to '"<<fullname<<"'"<<endl<<endl;
    s.queries++;
    if(rcode<0)
      s.drops++;
    else if(rcode==0)
      s.noerrors++;
    else if(rcode==2)
      s.servfails++;
    else if(rcode==3)
      s.nxdomains++;
    s.remotes[remote]++;
  }
  else {
    fullname=name+"."+domain;
    //    cerr<<"Not yet end, set our fullname to '"<<fullname<<"', recursing"<<endl;
    labels.pop_back();
    children[labels.back()].submit(labels, fullname, rcode, remote);
  }
}

