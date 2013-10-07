from util_nova import returnNodes, statsCount, totalVMType
from util_nova import returnServers, getResources
from util_nova import getAvailFlav, filterAz
from util_report import printPretty2, printPretty3, processConfig
from multiprocessing import Process, Queue
import time


def computeStats(node_name, _az2, dic, zone, i, client, r_outs=None, opt=None):

    startTime = time.time()

    print "Getting data from zone %s" % node_name

    node_info = returnNodes(client, zone, i)
    nodes_count = len(node_info)

    nodes_rc = statsCount(getResources(node_info, client))
    type_ = totalVMType(dic, returnServers(client, _az2))
    if 'others' in list(type_.elements()):
        others = type_['others']
    else:
        others = 0

    print "%s done , took %0.2f secs" % (node_name, (time.time() - startTime))

    stats = {'node_name': node_name,
             'node_count': nodes_count,
             'total_cores': nodes_rc.get('total_cores'),
             'total_memory': nodes_rc.get('total_memory'),
             'used_cores': nodes_rc.get('used_cores'),
             'used_memory': nodes_rc.get('used_memory'),
             'free_cores': nodes_rc.get('free_cores'),
             'free_memory': nodes_rc.get('free_memory'),
             'total_s': type_['m1.small'],
             'total_m': type_['m1.medium'],
             'total_l': type_['m1.large'],
             'total_xl': type_['m1.xlarge'],
             'total_xxl': type_['m1.xxlarge'],
             'oth': others}

    if opt is True:
        r_outs.put(stats)
    else:
        return stats


def combineResource(data_array):
    total_nodes = total_cores = total_mem = 0
    used_cores = used_mem = free_cores = free_mem = 0
    total_s = total_m = total_l = total_xl = total_xxl = oth = 0

    for i in data_array:
        total_nodes += i.get('node_count')
        total_cores += i.get('total_cores')
        total_mem += i.get('total_memory')
        used_cores += i.get('used_cores')
        used_mem += i.get('used_memory')
        free_cores += i.get('free_cores')
        free_mem += i.get('free_memory')
        total_s += i.get('total_s')
        total_m += i.get('total_m')
        total_l += i.get('total_l')
        total_xl += i.get('total_xl')
        total_xxl += i.get('total_xxl')
        oth += i.get('oth')

    data_dict = {'total_nodes': total_nodes,
                 'total_cores': total_cores,
                 'total_mem': total_mem,
                 'used_cores': used_cores,
                 'used_mem': used_mem,
                 'free_cores': free_cores,
                 'free_mem': free_mem,
                 'total_small': total_s,
                 'total_medium': total_m,
                 'total_large': total_l,
                 'total_xl': total_xl,
                 'total_xxl': total_xxl,
                 'oth': oth}

    return data_dict


def runCollect(client, zone, opt=None):
    flav = getAvailFlav(client)
    cell = filterAz(client, zone)
    timeout = processConfig('config', 'timeout')
    if opt == True:
        jobs = []
        r_outs = [Queue() for q in range(len(cell) + 1)]

        for z, i in enumerate(cell[0]):
            p = Process(name=z, target=computeStats,
                    args=(cell[1][z], cell[2][z], flav,
                          zone, i, client, r_outs[z],
                          True)
                        )
            jobs.append(p)
            p.start()

        for p in jobs:
            p.join(int(timeout))
            if p.is_alive():
                p.terminate()
                return False

        html_array = []
        for q in r_outs:
            html_array.append(q.get())

        return html_array
    else:
        if opt in cell[1]:
            index_id = cell[1].index(opt)
        a_name = cell[0][index_id]
        c_name = cell[2][index_id]

        return computeStats(opt, c_name, flav, zone, a_name, client,
                                        r_outs=None, opt=None)


def printOptions(data1, data_2=None, options=None):

    if options == None:
        printPretty2(data1, wrap=60)
    elif options == 'all':
        for i in data1:
            printPretty2(i, wrap=60)
        printPretty3(data_2, wrap=60)
