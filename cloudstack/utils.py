# -*- coding: utf-8 -*-
import parsedatetime.parsedatetime as pdt
import datetime
import time

def safe_option(config, section, option):
    retval = config.get(section, option)
    if retval:
        return retval
    else:
        raise Exception, "[%s] に [%s] を設定してください。" % (section,option)

class res(object):
    def __repr__(self):
        reprkeys = sorted(k for k in self.__dict__.keys())
        info = []
        for k in reprkeys:
            val = getattr(self,k)
            if isinstance(val,unicode):
                val = val.encode("utf-8")
            elif isinstance(val,int):
                val = str(val)
            info.append("%s=%s" % (k,val))
        return "<%s %s>" % (self.__class__.__name__, ", ".join(info))


def dict2obj(d,use_key=False):
    if not d:
        return None
    top = res()

    if isinstance(d,dict):
        for k, v in d.iteritems():
            if isinstance(v, dict):
                setattr(top, k, dict2obj(v))
            elif isinstance(v, list):
                tmp_list = []
                for vv in v:
                    if isinstance(vv, dict):
                        tmp_list.append(dict2obj(vv,True))
                    else:
                        tmp_list.append(vv)
                if use_key:
                    list_name = k
                else:
                    list_name = 'list'
                setattr(top, list_name,
                        type(v)(tmp_list))
                        #type(v)(dict2obj(vv) if isinstance(vv, dict) else vv for vv in v))
            else:
                setattr(top,k,v)

    elif isinstance(d,list):
        tmp_list = []
        for vv in d:
            if isinstance(vv, dict):
                tmp_list.append(dict2obj(vv,True))
            else:
                tmp_list.append(vv)
        if use_key:
            list_name = k
        else:
            list_name = 'list'
        setattr(top, list_name,type(d)(tmp_list))
        if not hasattr(top,"count"):
            setattr(top,"count",len(getattr(top,"list")))

    return top

def datetimeFromString(s):
    c = pdt.Constants()
    p = pdt.Calendar(c)
    result, what = p.parse(s)
    dt = 0
    if what in (1,2,3):
        dt = datetime.datetime( *result[:6] )
    if what == 0:
        return ""
    return dt

def time_format(epoch):
    return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(epoch))
