#!/usr/bin/env python
# vim: set expandtab ts=4 sw=4:

# Copyright 2009 University of Victoria
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.


## Auth: Duncan Penfold-Brown. 6/15/2009

## CLOUD SCHEDULER
##
## The main body for the cloud scheduler, that encapsulates and organizes
## all cloud scheduler functionality.
##
## Using optparse for command line options (http://docs.python.org/library/optparse.html)
##


## Imports

import sys
import logging
import getopt
import threading
import time   # for testing purposes only (sleeps)
import string # for debugging purposes
from optparse import OptionParser
import cloud_management
import job_management
import info_server

## GLOBAL VARIABLES

usage_str = "cloud_scheduler [-c FILE | --cluster-config FILE] [-m SERVER | --MDS SERVER]"
version_str = "Cloud Scheduler v 0.1"


## LOGGING SETUP

log = logging.getLogger("CloudLogger")
log.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler()
log_handler.setLevel(logging.DEBUG)
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)



## Thread Bodies

# Polling:
# The resource & running vm polling thread. Inherits from Thread class.
# Polling thread will iterate through the resource pool, updating resource
#   status based on vm_poll calls to each vm in a cluster's 'vms' list (of 
#   running vms)
# Constructed with argument 'resource_pool'
class PollingTh(threading.Thread):
    
    def __init__(self, resource_pool):
        threading.Thread.__init__(self)
        self.resource_pool = resource_pool

    def run(self):
        # TODO: Implement polling thread functionality here.
        log.debug("Poll - Starting polling thread...")

# Scheduling:
# Scheduling thread will match jobs to available resources and start vms
# (for now, will contain test create/destroy functions)
class SchedulingTh(threading.Thread):
    
    def __init__(self, resource_pool, job_pool):
        threading.Thread.__init__(self)
        self.resource_pool = resource_pool
        self.job_pool      = job_pool
        self.quit          = False

    def stop(self):
        log.debug("Wating for scheduling loop to end")
        self.quit = True

    def run(self):
        log.debug("Sched - Starting scheduling thread...")
        
#       ##############################################################################
#       ## Initial tests:
#       ##############################################################################
#
#       # Simulate job requirements for VMs (simple parameters only)
#       # Scan through resource pool to find fitting cluster
#       # Start a VM with simulated parameters on fitting cluster
#
#       # VM create parameters (name, networktype, cpuarch, imageloc, mem)
#       # Note: These are the only currently used fields that would be retrieved
#       #       from the job scheduler + job description files
#       req_name = "test-vm-nimbus-01"
#       req_network = "public"
#       req_cpuarch = "x86"
#       req_imageloc = "file://sl53base_i386.img"
#       req_mem = 128
#
#       ## Create
#       
#       # Create a VM (DRYRUN) on first cluster in resource pool's 'resources' list
#       print "dbg - Sched - Selecting a first-fit resource for test run."
#       print "dbg - Sched - Simulated job VM parameters: "
#       print "\tname: %s\n\tnetwork assoc.: %s\n\tcpu arch.: %s\n\timage: %s\n\tmemory: %d" \
#         % (req_name, req_network, req_cpuarch, req_imageloc, req_mem)
#       #target_rsrc = self.resource_pool.get_resource()
#       target_rsrc = self.resource_pool.get_resourceFF(req_network, req_cpuarch, req_mem)
#       print "dbg - Sched - open resource selected:"
#       target_rsrc.print_short()
#       target_rsrc.vm_create(req_name, req_network, req_cpuarch, req_imageloc, req_mem)
#
#       # Check that create is reflected internally
#       print "dbg - Sched - Print updated cluster information (after create):"
#       target_rsrc.print_short()
#       target_rsrc.print_vms()
#       
#       ## Poll...
#       # Poll every 5 seconds for 30 seconds (as a test)
#       for i in range(5):
#           time.sleep(5)
#           ret_state = target_rsrc.vm_poll(target_rsrc.vms[0])
#           print "dbg - Sched - Polled VM, state:\t%s" % ret_state
#           if ret_state == "Error":
#               print "dbg - Sched - VM is in Error state. Polling stopped. Moving to destroy."
#               break
#           elif ret_state == None:
#               print "dbg - Sched - VM has been destroyed. Polling stopped"
#               break
#        
#       ## Destroy...
#
#       # Call vm_destroy on the first entry in the target resource's 'vms' list
#       print "dbg - Sched - Attempting to destroy created VM..."
#       target_rsrc.vm_destroy(target_rsrc.vms[0])
#       
#       print "dbg - Sched - Print updated cluster information (after destroy):"
#       target_rsrc.print_short()
#       target_rsrc.print_vms()
#
#       ##############################################################################
#       ##############################################################################

        ##############################################################################
        ## Full scheduler test
        ##############################################################################

        
        # The main scheduling loop (currently runs for a fixed number of iterations
        # for demo purposes)
        #for i in range (200):
	
	while (not self.quit):
            log_with_line("Scheduler Loop")

            ## Query the job pool to get new unscheduled jobs
            #self.job_pool.job_queryCMD()
            self.job_pool.job_querySOAP()

            ## For each job in the unscheduled jobs list
            log.info("Schedule all queued jobs")
            for job in self.job_pool.jobs:
              
                log.debug("(Scheduler) - Attempting to schedule job %s" % job.get_id())

                # Find a resource that matches the job's requirements
                target_cluster = self.resource_pool.get_resourceFF(job.req_network, \
                  job.req_cpuarch, job.req_memory)

                # If no job fits, leave job in list and continue to next job
                if (target_cluster == None):
                    log.info("Scheduler - No resource to match job: %s" % job.get_id())
                    log.info("Scheduler - Leaving job unscheduled, moving to next job")
                    continue

                # Print details of the resource selected
                log.info("Scheduler - Open resource selected:")
                target_cluster.print_short()

                # Start VM with job requirements on the selected resource
                create_ret = target_cluster.vm_create(job.req_image, job.req_network, \
                  job.req_cpuarch, job.req_imageloc, job.req_memory)
                
                # If the VM create fails, continue to the next job
                if (create_ret != 0):
                    log.info("Scheduler - Creating VM for job %s failed" % job.get_id())
                    log.info("Scheduler - VM Create failed on cluster: ")
                    target_cluster.print_short()
                    log.info("Scheduler - Leaving job unscheduled, moving to next job")
                    continue

                # Mark job as scheduled
                self.job_pool.schedule(job)
           
            #ENDFOR - Attempt to schedule each job in the job pool
            
            ## Wait for a number of seconds
            log_with_line("Waiting")
            log.info("Scheduler - Waiting...")
            time.sleep(3)

            ## Poll all started VMs
            log.info("Scheduler - Polling all running VMs...")
            for cluster in self.resource_pool.resources:
                for vm in cluster.vms:
                    ret_state = cluster.vm_poll(vm)
                    
                    # Print polled VM's state and details
                    log.info("Scheduler - Polled VM: ")
                    vm.print_short("\t")
                    log.debug("(Scheduler) - VM in '%s' state" % ret_state)

                    # If the VM is in an error state, manually recreate it
                    if ret_state == "Error":
                        log.debug("(Scheduler) - VM in error state. Recreating...")

                        # Store all VM fields
                        vm_name = vm.name
                        vm_network = vm.network
                        vm_cpuarch = vm.cpuarch
                        vm_imageloc = vm.imagelocation
                        vm_mem = vm.memory

                        # Destroy the VM
                        destroy_ret = cluster.vm_destroy(vm)
                        if (destroy_ret != 0):
                            log.error("(Scheduler) - Destroying VM failed. Leaving VM in error state.")
                            continue
                        # Find an available resource to recreate on 
                        target_rsrc = self.resource_pool.get_resourceFF(vm_network, vm_cpuarch, vm_mem)
                        if (target_rsrc == None):
                            log.error("(Scheduler) - No resource found for recreation. Aborting recreate.")
                            continue
                        # Recreate the VM on the new resource
                        log.debug("(Scheduler) - Open resource selected:")
                        target_rsrc.print_short()
                        create_ret = target_rsrc.vm_create(vm_name, vm_network, vm_cpuarch, vm_imageloc, vm_mem)
                        if (create_ret != 0):
                            log.error("(Scheduler) - Recreating VM failed. Leaving VM in error state.")
                            continue
                    # ENDIF - if VM in error state

                    ## CANNOT USE recreate or reboot because of poll loop bug.
                    ## If the VM is in an error state, recreate it!
                    #if ret_state == "Error":
                    #    print "(Scheduler) - VM in error state. Recreating..."
                    #   recreate_ret = cluster.vm_recreate(vm)
  
                        # If recreate fails, leave VM in error state (tbdestroyed)
                    #   if (recreate_ret != 0):
                    #       print "(Scheduler) - Recreating VM failed. Leaving" +\
                    #         "VM in error state"
                    #       continue

                    ## If the VM is in an error state, destroy it
                    #if ret_state == "Error":
                    #   print "(Scheduler) - VM in error state. Destroying..."
                    #   destroy_ret = cluster.vm_destroy(vm)
 
                        # If destroy fails, leave VM in error state to be destroyed later
                    #   if (destroy_ret != 0):
                    #       print "(Scheduler) - Destroying VM failed"
                    #       print "(Scheduler) - Leaving VM in error state"
                    #       continue
                    
            #ENDFOR - Poll each running VM in the resource pool
        
        #ENDFOR - End of the main scheduler loop

        # Exit the scheduling thread - clean up VMs and exit
	log.debug("Exiting scheduler thread")

        # Destroy all VMs and finish
        log.debug("Destroying all remaining VMs :-(")
        for cluster in self.resource_pool.resources:
            for vm in cluster.vms:
                log.debug("(Scheduler) - Destroying VM:")
                vm.print_short("\t")

                destroy_ret = cluster.vm_destroy(vm)
                if destroy_ret != 0:
                    log.debug("(Scheduler) - Destroying VM failed. Continuing " +\
                      "anyway... check VM logs")
        
        #ENDFOR - Attempt to destroy each remaining VM in the system


##
## Functions
##

def main():

    # Create a parser and process commandline arguments
    parser = OptionParser(usage=usage_str, version=version_str)
    set_options(parser)
    (options, args) = parser.parse_args()

    # If the neither the cloud conffile or the MDS server are passed to obtain
    # initial cluster information, print usage and exit the system.
    if (not options.cloud_conffile) and (not options.mds_server):
        print "ERROR - main - No cloud or cluster information sources provided"
        parser.print_help()
        sys.exit(1)
    
    # Create a resource pool
    cloud_resources = cloud_management.ResourcePool("TestRsrcPool")

    # Create a job pool
    job_pool = job_management.JobPool("TestJobPool")
    
    # If the cluster config option was passed, read in the config file
    if options.cloud_conffile:
        if read_cloud_config(options.cloud_conffile, cloud_resources):
            print "ERROR - main - Reading cloud configuration file failed. Exiting..."
            sys.exit(1)

    # TODO: Add code to query an MDS to get initial cluster/cloud information
    
    # Print the resource pool
    cloud_resources.print_pool()

    # TODO: Resolve issue of atomicity / reliability when 2 threads are working
    #       on the same resource pool data. Does it matter (best effort!)?
    
    # Start the cloud scheduler info server for RPCs
    log.debug("Starting Cloud Scheduler info server...")
    info_serv = info_server.CloudSchedulerInfoServer(cloud_resources)
    info_serv.daemon = True
    info_serv.start()
    log.debug("Started Cloud Scheduler info server...")

    # Create the Polling thread (pass resource pool)
    poller = PollingTh(cloud_resources)
    poller.start()

    # Create the Scheduling thread (pass resource pool)
    scheduler = SchedulingTh(cloud_resources, job_pool)
    scheduler.start()

    log.debug("Scheduling and Polling threads started.")

    # Wait on the scheduler to finish before exiting main
    # (Unnecessary? The scheduler and the poller are the only things that need
    # to remain running)
    log.debug("Waiting for the scheduler to finish...")

    # Wait for keyboard input to exit the cloud scheduler
    try: 
        while scheduler.isAlive():
            time.sleep(2)
    except (SystemExit, KeyboardInterrupt):
        log.info("Exiting normally due to KeyboardInterrupt or SystemExit")

    # Clean up out threads (shuts down all running VMs)
    scheduler.stop()
    info_serv.stop()
    sys.exit()


# Sets the command-line options for a passed in OptionParser object (via optparse)
def set_options(parser):

    # Option attributes: action, type, dest, help. See optparse documentation.
    # Defaults: action=store, type=string, dest=[name of the option] help=none
    parser.add_option("-c", "--cloud-config", dest="cloud_conffile", metavar="FILE", \
      help="Designate a config file from which cloud cluster information is obtained")

    parser.add_option("-m", "--MDS", dest="mds_server", metavar="SERVER", \
      help="Designate an MDS server from which cloud cluster information is obtained")

# Reads in a cmdline passed configuration file containing cloud cluster information
# Stores cluster information in the ResourcePool parameter rsrc_pool
# (see the sample_cloud example configuration file for more information)
def read_cloud_config(config_file, rsrc_pool):

    log.debug("Attempting to read cloud configuration file: " + config_file)

    # Open config file for reading
    cloud_conf = open(config_file, 'r')

    # Read in config file, parse into Cluster objects
    for line in cloud_conf:
        
        # Check for commented or blank lines
        if line[0] == "#" or line == "\n" :
            continue

        cluster_attr = line.split('/') 
        log.debug("%s" % (cluster_attr))

        # Create a new cluster according to cloud_type
        # TODO: A more dynamic format would be helpful here - current solution is hardcoded
        if "Nimbus" in cluster_attr:
            log.debug("found new Nimbus cluster")
            new_cluster = cloud_management.NimbusCluster()
        elif "OpenNebula" in cluster_attr:
            log.debug("found new OpenNebula cluster")
            new_cluster = cloud_management.Cluster()   # TODO: Use superclass for now
        elif "Eucalyptus" in cluster_attr:
            log.debug("found new Eucalyptus cluster")
            new_cluster = cloud_management.Cluster()   # TODO: Use superclass for now
        
        # Use superclass methods for population and print
        new_cluster.populate(cluster_attr)
        new_cluster.print_cluster()
        
        # Add the new cluster to a resource pool
        rsrc_pool.add_resource(new_cluster)

    log.debug("Cloud configuration read succesfully from " + config_file )
    return (0)
    

# Prints readable lined lines across the screen with message
def print_line(msg):
    log.warning("print_line is DEPRECATED, use log_with_line instead")
    log_with_line(msg)

# logs readable lined lines across the screen with message
def log_with_line(msg):
    msg_len = len(msg)
    fill = "-" * (75-msg_len)
    log.debug("-----"+msg+fill)


##
## Main Functionality
##

main()
