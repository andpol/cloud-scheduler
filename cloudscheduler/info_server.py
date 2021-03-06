#!/usr/bin/env python
# vim: set expandtab ts=4 sw=4:

# Copyright (C) 2009 University of Victoria
# You may distribute under the terms of either the GNU General Public
# License or the Apache v2 License, as specified in the README file.

## Auth: Patrick Armstrong. 8/28/2009.
##
## Cloud Scheduler Information Server
## This class implements an XMLRPC Server that serves information about the state
## of the cloud sceduler to information utilities (web interface, command line, whatever)
##
## Based on http://docs.python.org/library/simplexmlrpcserver.html

##
## IMPORTS
##
import logging
import threading
import time
import socket
import sys
import platform
import re
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

import cloudscheduler.config as config
from cluster_tools import ICluster
from cluster_tools import VM
from cloud_management import ResourcePool
from job_management import Job
from job_management import JobPool
# JSON lib included in 2.6+
if sys.version_info < (2, 6):
    try:
        import simplejson as json
    except:
        raise "Please install the simplejson lib for python 2.4 or 2.5"
else:
    import json

log = None

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

class InfoServer(threading.Thread,):

    cloud_resources = None
    job_pool = None
    job_poller = None
    machine_poller = None
    vm_poller = None
    scheduler = None
    cleaner = None
    def __init__(self, c_resources, c_job_pool, c_job_poller, c_machine_poller, c_vm_poller, c_scheduler, c_cleaner):

        global log
        log = logging.getLogger("cloudscheduler")

        #set up class
        threading.Thread.__init__(self, name=self.__class__.__name__)
        self.done = False
        cloud_resources = c_resources
        job_pool = c_job_pool
        job_poller = c_job_poller
        machine_poller = c_machine_poller
        vm_poller = c_vm_poller
        scheduler = c_scheduler
        cleaner = c_cleaner
        host_name = "0.0.0.0"
        #set up server
        try:
            self.server = SimpleXMLRPCServer((host_name,
                                              config.info_server_port),
                                              requestHandler=RequestHandler,
                                              logRequests=False)
            self.server.socket.settimeout(1)
            self.server.register_introspection_functions()
        except:
            log.error("Couldn't start info server: %s" % sys.exc_info()[0])
            sys.exit(1)

        # Register an instance; all the methods of the instance are
        # published as XML-RPC methods
        class externalFunctions:
            def get_cloud_resources(self):
                return cloud_resources.get_pool_info()
            def get_cluster_resources(self):
                output = "Clusters in resource pool:\n"
                for cluster in cloud_resources.resources:
                    output += cluster.get_cluster_info_short()+"\n"
                return output
            def get_cluster_vm_resources(self):
                output = VM.get_vm_info_header()
                clusters = 0
                vm_count = 0
                for cluster in cloud_resources.resources:
                    clusters += 1
                    vm_count += len(cluster.vms)
                    output += cluster.get_cluster_vms_info()
                output += '\nTotal VMs: %i. Total Clouds: %i' % (vm_count, clusters)
                return output
            def get_cluster_info(self, cluster_name):
                output = "Cluster Info: %s\n" % cluster_name
                cluster = cloud_resources.get_cluster(cluster_name)
                if cluster:
                    output += cluster.get_cluster_info_short()
                else:
                    output += "Cluster named %s not found." % cluster_name
                return output
            def get_vm_info(self, cluster_name, vm_id):
                output = "VM Info for VM id: %s\n" % vm_id
                cluster = cloud_resources.get_cluster(cluster_name)
                vm = None
                if cluster:
                    vm = cluster.get_vm(vm_id)
                else:
                    output += "Cluster %s not found.\n" % cluster_name
                if vm:
                    output += vm.get_vm_info()
                else:
                    output += "VM with id: %s not found.\n" % vm_id
                return output
            def get_json_vm(self, cluster_name, vm_id):
                output = "{}"
                cluster = cloud_resources.get_cluster(cluster_name)
                vm = None
                if cluster:
                    vm = cluster.get_vm(vm_id)
                    if vm:
                        output = VMJSONEncoder().encode(vm)
                return output
            def get_json_cluster(self, cluster_name):
                output = "{}"
                cluster = cloud_resources.get_cluster(cluster_name)
                if cluster:
                    output = ClusterJSONEncoder().encode(cluster)
                return output
            def get_json_resource(self):
                return ResourcePoolJSONEncoder().encode(cloud_resources)
            def get_developer_information(self):
                try:
                    from guppy import hpy
                    h = hpy()
                    heap = h.heap()
                    return str(heap)
                except:
                    return "You need to have Guppy installed to get developer " \
                           "information" 
            def get_newjobs(self):
                jobs = job_pool.job_container.get_unscheduled_jobs()
                output = Job.get_job_info_header()
                for job in jobs:
                    output += job.get_job_info()
                return output
            def get_schedjobs(self):
                jobs = job_pool.job_container.get_scheduled_jobs()
                output = Job.get_job_info_header()
                for job in jobs:
                    output += job.get_job_info()
                return output
            def get_highjobs(self):
                jobs = job_pool.job_container.get_high_priority_jobs()
                output = Job.get_job_info_header()
                for job in jobs:
                    output += job.get_job_info()
                return output
            def get_idlejobs(self):
                jobs = job_pool.job_container.get_idle_jobs()
                output = Job.get_job_info_header()
                for job in jobs:
                    output += job.get_job_info()
                return output
            def get_runningjobs(self):
                jobs = job_pool.job_container.get_running_jobs()
                output = Job.get_job_info_header()
                for job in jobs:
                    output += job.get_job_info()
                return output
            def get_completejobs(self):
                jobs = job_pool.job_container.get_complete_jobs()
                output = Job.get_job_info_header()
                for job in jobs:
                    output += job.get_job_info()
                return output
            def get_heldjobs(self):
                jobs = job_pool.job_container.get_held_jobs()
                output = Job.get_job_info_header()
                for job in jobs:
                    output += job.get_job_info()
                return output
            def get_job(self, jobid):
                output = "Job not found."
                job = job_pool.job_container.get_job_by_id(jobid)
                if job != null:
                    output = job_match.get_job_info_pretty()
                return output
            def get_json_job(self, jobid):
                output = '{}'
                job_match = job_pool.job_container.get_job_by_id(jobid)
                return JobJSONEncoder().encode(job)
            def get_json_jobpool(self):
                return JobPoolJSONEncoder().encode(job_pool)
            def get_ips_munin(self):
                output = ""
                for cluster in cloud_resources.resources:
                    for vm in cluster.vms:
                        if re.search("(10|192\.168|172\.(1[6-9]|2[0-9]|3[01]))\.", vm.ipaddress):
                            continue
                        else:
                            output += "[%s]\n\taddress %s\n" % (vm.hostname, vm.ipaddress)
                return output
            def get_vm_startup_time(self):
                output = ""
                for cluster in cloud_resources.resources:
                    output += "Cluster: %s " % cluster.name
                    total_time = 0
                    for vm in cluster.vms:
                        pass
                        output += "%d, " % (vm.startup_time if vm.startup_time != None else 0)
                        total_time += (vm.startup_time if vm.startup_time != None else 0)
                    if len(cluster.vms) > 0:
                        output += " Avg: %d " % (int(total_time) / len(cluster.vms))
                return output
            def get_diff_types(self):
                current_types = cloud_resources.vmtype_distribution()
                desired_types = job_pool.job_type_distribution()
                # Negative difference means will need to create that type
                diff_types = {}
                for type in current_types.keys():
                    if type in desired_types.keys():
                        diff_types[type] = current_types[type] - desired_types[type]
                    else:
                        diff_types[type] = 1 # changed from 0 to handle users with multiple job types
                for type in desired_types.keys():
                    if type not in current_types.keys():
                        diff_types[type] = -desired_types[type]
                output = "Diff Types dictionary\n"
                for key, value in diff_types.iteritems():
                    output += "type: %s, dist: %f\n" % (key, value)
                output += "Current Types (vms)\n"
                for key, value in current_types.iteritems():
                    output += "type: %s, dist: %f\n" % (key, value)
                output += "Desired Types (jobs)\n"
                for key, value in desired_types.iteritems():
                    output += "type: %s, dist: %f\n" % (key, value)
                return output
            def get_vm_job_run_times(self):
                output = "Run Times of Jobs on VMs\n"
                for cluster in cloud_resources.resources:
                    for vm in cluster.vms:
                        output += "%s : avg %f\n" % (vm.hostname, vm.job_run_times.average())
                return output
            def get_cloud_config_values(self):
                return cloud_resources.get_cloud_config_output()
            def check_shared_objs(self):
                output = ""
                output += "Scheduler Thread:\n" + scheduler.check_shared_objs() + "\n"
                output += "Cleanup Thread:\n" + cleaner.check_shared_objs() + "\n"
                output += "VMPoller Thread:\n" + vm_poller.check_shared_objs() + "\n"
                output += "JobPoller Thread:\n" + job_poller.check_shared_objs() + "\n"
                output += "MachinePoller Thread:\n" + machine_poller.check_shared_objs() + "\n"
                return output

        self.server.register_instance(externalFunctions())

    def run(self):

        # Run the server's main loop
        log.info("Started info server on port %s" % config.info_server_port)
        while self.server:
            try:
                self.server.handle_request()
                if self.done:
                    log.debug("Killing info server...")
                    self.server.socket.close()
                    break
            except socket.timeout:
                log.warning("info server's socket timed out. Don't panic!")

    def stop(self):
        self.done = True

class VMJSONEncoder(json.JSONEncoder):
    def default(self, vm):
        if not isinstance (vm, VM):
            log.error("Cannot use VMJSONEncoder on non VM object")
            return
        return {'name': vm.name, 'id': vm.id, 'vmtype': vm.vmtype,
                'hostname': vm.hostname, 'clusteraddr': vm.clusteraddr,
                'cloudtype': vm.cloudtype, 'network': vm.network, 
                'cpuarch': vm.cpuarch, 'image': vm.image,
                'memory': vm.memory, 'mementry': vm.mementry, 
                'cpucores': vm.cpucores, 'storage': vm.storage, 
                'status': vm.status}

class ClusterJSONEncoder(json.JSONEncoder):
    def default(self, cluster):
        if not isinstance (cluster, ICluster):
            log.error("Cannot use ClusterJSONEncoder on non Cluster object")
            return
        vmEncodes = []
        for vm in cluster.vms:
            vmEncodes.append(VMJSONEncoder().encode(vm))
        vmDecodes = []
        for vm in vmEncodes:
            vmDecodes.append(json.loads(vm))
        return {'name': cluster.name, 'network_address': cluster.network_address,
                'cloud_type': cluster.cloud_type, 'memory': cluster.memory, 
                'cpu_archs': cluster.cpu_archs, 
                'network_pools': cluster.network_pools, 
                'vm_slots': cluster.vm_slots, 'cpu_cores': cluster.cpu_cores, 
                'storageGB': cluster.storageGB, 'vms': vmDecodes}

class ResourcePoolJSONEncoder(json.JSONEncoder):
    def default(self, res_pool):
        if not isinstance (res_pool, ResourcePool):
            log.error("Cannot use ResourcePoolJSONEncoder on non ResourcePool Object")
            return
        pool = []
        for cluster in res_pool.resources:
            pool.append(ClusterJSONEncoder().encode(cluster))
        poolDecodes = []
        for cluster in pool:
            poolDecodes.append(json.loads(cluster))
        return {'resources': poolDecodes}

class JobJSONEncoder(json.JSONEncoder):
    def default(self, job):
        if not isinstance(job, Job):
            log.error("Cannot use JobJSONEncoder on non Job Object")
            return
        return {'id': job.id, 'user': job.user, 'priority': job.priority,
                'job_status': job.job_status, 'cluster_id': job.cluster_id,
                'proc_id': job.proc_id, 'req_vmtype': job.req_vmtype,
                'req_network': job.req_network, 'req_cpuarch': job.req_cpuarch,
                'req_image': job.req_image, 'req_imageloc': job.req_imageloc,
                'req_ami': job.req_ami, 'req_memory': job.req_memory,
                'req_cpucores': job.req_cpucores, 'req_storage': job.req_storage,
                'keep_alive': job.keep_alive, 'status': job.status,
                'remote_host': job.remote_host, 'running_cloud': job.running_cloud}

class JobPoolJSONEncoder(json.JSONEncoder):
    def default(self, job_pool):
        if not isinstance(job_pool, JobPool):
            log.error("Cannot use JobPoolJSONEncoder on non JobPool Object")
            return
        new_queue = []
        for job in job_pool.job_container.get_unscheduled_jobs():
            new_queue.append(JobJSONEncoder().encode(job))
        sched_queue = []
        for job in job_pool.job_container.get_scheduled_jobs():
            sched_queue.append(JobJSONEncoder().encode(job))
        new_decodes = []
        for job in new_queue:
            print job
            new_decodes.append(job)
        sched_decodes = []
        for job in sched_queue:
            sched_decodes.append(job)
        return {'new_jobs': new_decodes, 'sched_jobs': sched_decodes}
