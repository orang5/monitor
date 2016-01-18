# -*- coding: utf-8 -*-
from common.agent_utils import *
from common.models import *
import datetime, time, collections

class _query(object):
	def __init__(self, model):
		self.model = model
	def query(self, **kargs):
		rest = dict()
		for key in kargs:
			if kargs[key]: rest[key] = kargs[key]
		if self.model:
			return self.model.objects(**rest)
		return None
	def byId(self, uuid):
		if self.model and uuid:
			return self.query(uuid=uuid)
		return None
	def byName(self, name):
		if self.model and name:
			return self.query(name=name)
		return None
	def first(self, **kargs):
		try:
			ret = self.query(**kargs).first().value
		except:
			ret = None
		return ret
			
class _queryMetric(_query):
    def __init__(self, last=None, span=None):
        super(_queryMetric, self).__init__(MetricModel)
        self.last = last
        self.span = span
    
    def set(self, last=None, span=None, **kargs):
        if kargs: self.kargs = kargs
        if last: self.last = last
        if span: self.span = span

    def query(self, **kargs):
        conds = dict()
        conds.update(self.kargs, **kargs)
        if self.last and self.span:
            conds["timestamp__gte"] = self.last-self.span
        return super(_queryMetric, self).query(**conds)


    def byMinutes(self, delta=1):
        self.set(last=datetime.datetime.now(),span=datetime.timedelta(minutes=delta))
        return self.query(**self.kargs)

    def byHours(self, delta=1):
        self.set(last=datetime.datetime.now(),span=datetime.timedelta(hours=delta))
        return self.query(**self.kargs)

    def byDays(self, delta=1):
        self.set(last=datetime.datetime.now(),span=datetime.timedelta(days=delta))
        return self.query(**self.kargs)

    def clean(self):
        self.kargs = None
        self.last = None
        self.span = None

def metric_filter(qsets, unit, format):
    label = []
    value = []
    for q in qsets:
        ticks = sorted(q.value.keys())
        mark = 0
        offset = int(ticks[0][1:])
        while(offset<=int(ticks[-1][1:])):
            delta = datetime.timedelta(seconds = offset)
            label.append((q.timestamp + delta).strftime(format))
            pre = ticks[mark]
            if mark < len(ticks)-1:
                next = ticks[mark+1]
            else:
                next = 'a3601'
            if offset < int(next[1:]):
                value.append(int(q.value[pre]))
            else:
                total = 0
                num = 0
                low = offset - unit
                high = int(next[1:])
                while(int(next[1:])<=offset):
                    n = high - low
                    total += q.value[pre]*n
                    num += n
                    mark += 1
                    pre = ticks[mark]
                    if mark < len(ticks)-1:
                        next = ticks[mark+1]
                    else:
                        next = 'a3601'
                    low = int(pre[1:])
                    high = int(next[1:])
                n = offset - int(pre[1:])
                total += q.value[pre]*n
                num += n
                value.append(int(total/num))
            offset += unit
    return (label,value)

formate = {
    'day': "%b-%d-%y",
    'hour': "%b-%d %H",
    'minute': "%H:%M",
    'seconds': "%H:%M:%S"
}

queryCur = _query(CurrentModel)
queryCurInfo = _query(CurrentInfoModel)
queryMetric = _queryMetric()


def query_did(uuid=None):
	qc = queryCur.byId(uuid)
	devid = []
	for q in qc:
		kargs = dict(tag=False)
		try:
			if not q.inst: kargs["tag"] = True
			kargs["deviceId"] = q.DeviceID
		except:
			if kargs.has_key("deviceId"):
				kargs["tag"] = True
		if kargs["tag"]:
			devid.append(kargs["deviceId"])
	devid = list(set(devid))
	return devid
    
def query_vminfo(uuid=None):
    conds = dict(uuid=uuid, name="mem_Capacity")
    qc = queryCurInfo.byId(uuid)
    cap = queryCur.query(**conds)
    capacity = 0

    for c in cap:
        capacity += int(c.value)
    vmInfo = {}
    for q in qc:
        key = q.display_name
        if(key=="host_info"):
            temp = from_json(q.value)
            for mem in temp["mem"]:
                mem["Capacity"] = capacity
            niclist = []
            for nic in temp["nic"]:
                if nic["has_ip"]:
                    niclist.append(nic)
            temp["nic"] = niclist
            vmInfo[key] = temp
        elif(key == "installed_programs"):
            if len(q.value) > 8:
                temp = q.value[1:9]
            else:
                temp = q.value
            vmInfo[key] = temp
        else:
            vmInfo[key] = vmInfo.get(key,q.value)
    return vmInfo
    
def query_log(uuid=None):
    collection = None
    '''
    if uuid:
		collection = MetricModel.objects(name__startwith="Vim25Api", uuid=uuid)
    else:
        collection = MetricModel.objects(name__startswith="Vim25Api")
    ''' 
    collection = queryMetric.query(name__startswith="Vim25Api", uuid=uuid)
    ret = {}
    
    #entity_list = CurrentInfoModel.objects(name="entity_list").first().value
    entity_list = queryCurInfo.first(name="entity_list")
    for evt in collection:
        ret[evt.key] = json.loads(evt.to_json())
        evt_time = datetime.datetime.fromtimestamp(ret[evt.key]["timestamp"]["$date"]/1000)
        ret[evt.key]["timestamp"] = evt_time.strftime("%b %d %I:%M:%S %p")
        for item in entity_list:
            if item["uuid"] == ret[evt.key]["uuid"]:
                ret[evt.key]["name"] = item["mo"]
       
    return ret.values()
    
def query_vmlist(uuid=None):
    if not uuid:
    # all
    # query entity_list in CurrentInfoModel
    # only one entry.
        host = {}
        for q in queryCurInfo.byName("entity_list"):
            for item in q.value:
                if item["mo_type"] == "HostSystem":
                    host[item["uuid"]] = item
        # query vm_list in CurrentModel
        # one entry for each host.
        vmlist = {}
        for q in queryCur.byName("vm_list"):
            if q.uuid:
                vmlist[q.uuid] = q.value

        # return values
        for uuid in host.keys():
            host[uuid]["vm"] = vmlist[uuid]
            
        return host.values()
    
    else:
      # query vm_list in CurrentModel
      # one entry for each host.
      for q in queryCur.query(name="vm_list", uuid=uuid):
          return q.value        
    
def query_points(uuid, DeviceID, tag, vc):
    datasets = queryCur.query(uuid = uuid,DeviceID = DeviceID)
    points = []
    for ch in vc["charts"]:
        if tag == ch["tag"]:
            points = ch["points"]
    ret = []
    for i,p in enumerate(points):
        ret.append(-1)
        for data in datasets:
            if data.name in p["value"]:
                ret[i]=data.value
                continue
    return ret

def test_query():
    uuid = u"0050568b044b"
    print query_did(uuid)
    print query_vminfo(uuid)   
    print query_log()
    print query_vmlist()

def test_qm():
    q = _queryMetric()
    q.set(name = 's_host_cpu_usage_avg', mo='dev')
    sets = q.byDays()
    (label, value) = metric_filter(sets, 10, "%b-%d-%y %H:%M:%S")

    for i in range(len(label)):
        print "%s: %s" % (label[i], value[i])


if "__main__" == __name__:test_qm()
    



