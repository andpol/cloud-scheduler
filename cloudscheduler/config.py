#!/usr/bin/env python
# vim: set expandtab ts=4 sw=4:

# Copyright (C) 2009 University of Victoria
# You may distribute under the terms of either the GNU General Public
# License or the Apache v2 License, as specified in the README file.

## Auth.: Patrick Armstrong

import os
import sys
from urlparse import urlparse
import ConfigParser

import utilities

# Cloud Scheduler Options Module.

# Set default values
condor_webservice_url = "http://localhost:8080"
condor_collector_url = "http://localhost:9618"
condor_retrieval_method = "soap"
condor_q_command = "condor_q -l"
condor_status_command = "condor_status -l"
condor_off_command = "/usr/sbin/condor_off"
condor_on_command = "/usr/sbin/condor_on"
ssh_path = "/usr/bin/ssh"
openssl_path = "/usr/bin/openssl"
condor_host = "localhost"
condor_host_on_vm = ""
condor_context_file = ""
vm_lifetime = 10080
cert_file = ""
key_file = ""
cert_file_on_vm = ""
key_file_on_vm = ""
ca_root_certs = []
ca_signing_policies = []
cloudscheduler_ssh_key = ""
cloud_resource_config = None
image_attach_device = "sda"
scratch_attach_device = "sdb"
info_server_port = 8111
workspace_path = "workspace"
persistence_file = "/var/run/cloudscheduler.persistence"
job_ban_timeout = 60*60 # 1 hour default
ban_tracking = False
ban_file = "/var/run/cloudscheduler.banned"
ban_min_track = 5
ban_failrate_threshold = 1.0
polling_error_threshold = 10
condor_register_time_limit = 900
graceful_shutdown = False
graceful_shutdown_method = "hold"
retire_before_lifetime = False
retire_before_lifetime_factor = 1.5
getclouds = False
scheduling_metric = "slot"
scheduling_algorithm = "fairshare"
job_distribution_type = "normal"
high_priority_job_support = False
high_priority_job_weight = 1
cpu_distribution_weight = 1.0
memory_distribution_weight = 1.0
storage_distribution_weight = 1.0
cleanup_interval = 5
vm_poller_interval = 5
job_poller_interval = 5
machine_poller_interval = 5
scheduler_interval = 5
job_proxy_refresher_interval = -1 # The current default is not to refresh the job proxies. (until code is thouroughly tested -- Andre C.)
job_proxy_renewal_threshold = 15 * 60 # 15 minutes default
vm_proxy_refresher_interval = -1 # The current default is not to refresh the VM proxies. (until code is thouroughly tested -- Andre C.)
vm_proxy_renewal_threshold = 60 * 60 # 60 minutes default
vm_proxy_shutdown_threshold = 30 * 60 # 30 minutes default
vm_connection_fail_threshold = 30 * 60 # 30 minutes default
vm_idle_threshold = 5 * 60 # 5 minute default
myproxy_logon_command = 'myproxy-logon'
proxy_cache_dir = None
override_vmtype = False

default_VMType= "default"
default_VMNetwork= ""
default_VMCPUArch= "x86"
default_VMName= "Default-Image"
default_VMLoc= ""
default_VMAMI= ""
default_VMMem= 512
default_VMCPUCores= 1
default_VMStorage= 1
default_VMInstanceType= ""
default_VMMaximumPrice= 0

log_level = "INFO"
log_location = None
log_stdout = False
log_max_size = None
log_format = "%(asctime)s - %(levelname)s - %(threadName)s - %(message)s"

use_pyopenssl = False



def setup(path=None):
    """Setup cloudscheduler using config file.
       setup will look for a configuration file specified on the command line,
       or in ~/.cloudscheduler.conf or /etc/cloudscheduler.conf
    """

    global condor_webservice_url
    global condor_collector_url
    global condor_retrieval_method
    global condor_q_command
    global condor_status_command
    global condor_off_command
    global condor_on_command
    global ssh_path
    global openssl_path
    global condor_context_file
    global condor_host
    global condor_host_on_vm
    global vm_lifetime
    global cert_file
    global key_file
    global cert_file_on_vm
    global key_file_on_vm
    global ca_root_certs
    global ca_signing_policies
    global cloudscheduler_ssh_key
    global cloud_resource_config
    global image_attach_device
    global scratch_attach_device
    global info_server_port
    global workspace_path
    global persistence_file
    global job_ban_timeout
    global ban_tracking
    global ban_file
    global ban_min_track
    global ban_failrate_threshold
    global polling_error_threshold
    global condor_register_time_limit
    global graceful_shutdown
    global graceful_shutdown_method
    global retire_before_lifetime
    global retire_before_lifetime_factor
    global getclouds
    global scheduling_metric
    global scheduling_algorithm
    global job_distribution_type
    global high_priority_job_support
    global high_priority_job_weight
    global cpu_distribution_weight
    global memory_distribution_weight
    global storage_distribution_weight
    global cleanup_interval
    global vm_poller_interval
    global job_poller_interval
    global machine_poller_interval
    global scheduler_interval
    global job_proxy_refresher_interval
    global job_proxy_renewal_threshold
    global vm_proxy_refresher_interval
    global vm_proxy_renewal_threshold
    global vm_proxy_shutdown_threshold
    global vm_connection_fail_threshold
    global vm_idle_threshold
    global proxy_cache_dir
    global myproxy_logon_command
    global override_vmtype
    global default_VMType
    global default_VMNetwork
    global default_VMCPUArch
    global default_VMName
    global default_VMLoc
    global default_VMAMI
    global default_VMMem
    global default_VMCPUCores
    global default_VMStorage
    global default_VMInstanceType
    global default_VMMaximumPrice

    global log_level
    global log_location
    global log_stdout
    global log_max_size
    global log_format

    global use_pyopenssl

    homedir = os.path.expanduser('~')

    # Find config file
    if not path:
        if os.path.exists(homedir + "/.cloudscheduler/cloud_scheduler.conf"):
            path = homedir + "/.cloudscheduler/cloud_scheduler.conf"
        elif os.path.exists("/etc/cloudscheduler/cloud_scheduler.conf"):
            path = "/etc/cloudscheduler/cloud_scheduler.conf"
        else:
            print >> sys.stderr, "Configuration file problem: There doesn't " \
                  "seem to be a configuration file. " \
                  "You can specify one with the --config-file parameter, " \
                  "or put one in ~/.cloudscheduler/cloud_scheduler.conf or "\
                  "/etc/cloudscheduler/cloud_scheduler.conf"
            sys.exit(1)

    # Read config file
    config_file = ConfigParser.ConfigParser()
    try:
        config_file.read(path)
    except IOError:
        print >> sys.stderr, "Configuration file problem: There was a " \
              "problem reading %s. Check that it is readable," \
              "and that it exists. " % path
        raise
    except ConfigParser.ParsingError:
        print >> sys.stderr, "Configuration file problem: Couldn't " \
              "parse your file. Check for spaces before or after variables."
        raise
    except:
        print "Configuration file problem: There is something wrong with " \
              "your config file."
        raise

    if config_file.has_option("global", "condor_retrieval_method"):
        condor_retrieval_method = config_file.get("global",
                                                "condor_retrieval_method")

    if config_file.has_option("global", "condor_q_command"):
        condor_q_command = config_file.get("global",
                                                "condor_q_command")

    if config_file.has_option("global", "condor_off_command"):
        condor_off_command = config_file.get("global",
                                                "condor_off_command")

    if config_file.has_option("global", "condor_on_command"):
        condor_on_command = config_file.get("global",
                                                "condor_on_command")

    if config_file.has_option("global", "ssh_path"):
        ssh_path = config_file.get("global", "ssh_path")

    if config_file.has_option("global", "openssl_path"):
        openssl_path = config_file.get("global", "openssl_path")

    if config_file.has_option("global", "condor_status_command"):
        condor_status_command = config_file.get("global",
                                                "condor_status_command")

    if config_file.has_option("global", "condor_webservice_url"):
        condor_webservice_url = config_file.get("global",
                                                "condor_webservice_url")

    if config_file.has_option("global", "condor_collector_url"):
        condor_collector_url = config_file.get("global",
                                                "condor_collector_url")

    if config_file.has_option("global", "condor_host_on_vm"):
        condor_host_on_vm = config_file.get("global",
                                                "condor_host_on_vm")

    if config_file.has_option("global", "condor_context_file"):
        condor_context_file = config_file.get("global",
                                                "condor_context_file")

    if config_file.has_option("global", "vm_lifetime"):
        try:
            vm_lifetime = config_file.getint("global", "vm_lifetime")
        except ValueError:
            print "Configuration file problem: vm_lifetime must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "cert_file"):
        cert_file = config_file.get("global", "cert_file")

    if config_file.has_option("global", "key_file"):
        key_file = config_file.get("global", "key_file")

    if config_file.has_option("global", "cert_file_on_vm"):
        cert_file_on_vm = config_file.get("global", "cert_file_on_vm")

    if config_file.has_option("global", "key_file_on_vm"):
        key_file_on_vm = config_file.get("global", "key_file_on_vm")

    if config_file.has_option("global", "ca_root_certs"):
        ca_root_certs = config_file.get("global", "ca_root_certs").split(',')

    if config_file.has_option("global", "ca_signing_policies"):
        ca_signing_policies = config_file.get("global", "ca_signing_policies").split(',')

    if config_file.has_option("global", "cloudscheduler_ssh_key"):
        cloudscheduler_ssh_key = config_file.get("global", "cloudscheduler_ssh_key")

    if config_file.has_option("global", "cloud_resource_config"):
        cloud_resource_config = config_file.get("global",
                                                "cloud_resource_config")

    if config_file.has_option("global", "image_attach_device"):
        image_attach_device = config_file.get("global",
                                                "image_attach_device")

    if config_file.has_option("global", "scratch_attach_device"):
        scratch_attach_device = config_file.get("global",
                                                "scratch_attach_device")

    if config_file.has_option("global", "info_server_port"):
        try:
            info_server_port = config_file.getint("global", "info_server_port")
        except ValueError:
            print "Configuration file problem: info_server_port must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "workspace_path"):
        workspace_path = config_file.get("global", "workspace_path")

    if config_file.has_option("global", "persistence_file"):
        persistence_file = config_file.get("global", "persistence_file")

    if config_file.has_option("global", "job_ban_timeout"):
        try:
            job_ban_timeout = 60 * config_file.getint("global", "job_ban_timeout")
        except ValueError:
            print "Configuration file problem: job_ban_timeout must be an " \
                  "integer value in minutes."
            sys.exit(1)

    if config_file.has_option("global", "ban_file"):
        ban_file = config_file.get("global", "ban_file")

    if config_file.has_option("global", "polling_error_threshold"):
        try:
            polling_error_threshold = config_file.getint("global", "polling_error_threshold")
        except ValueError:
            print "Configuration file problem: polling_error_threshold must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "ban_failrate_threshold"):
        try:
            ban_failrate_threshold = config_file.getfloat("global", "ban_failrate_threshold")
            if ban_failrate_threshold == 0:
                print "Please use a float value (0, 1.0]"
                sys.exit(1)
        except ValueError:
            print "Configuration file problem: ban_failrate_threshold must be an " \
                  "float value."
            sys.exit(1)

    if config_file.has_option("global", "ban_min_track"):
        try:
            ban_min_track = config_file.getint("global", "ban_min_track")
        except ValueError:
            print "Configuration file problem: ban_min_track must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "condor_register_time_limit"):
        try:
            condor_register_time_limit = 60*config_file.getint("global", "condor_register_time_limit")
        except ValueError:
            print "Configuration file problem: condor_register_time_limit must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "ban_tracking"):
        ban_tracking = config_file.getboolean("global", "ban_tracking")

    if config_file.has_option("global", "graceful_shutdown"):
        graceful_shutdown = config_file.getboolean("global", "graceful_shutdown")

    if config_file.has_option("global", "graceful_shutdown_method"):
        graceful_shutdown_method = config_file.get("global", "graceful_shutdown_method")

    if config_file.has_option("global", "retire_before_lifetime"):
        retire_before_lifetime = config_file.getboolean("global", "retire_before_lifetime")

    if config_file.has_option("global", "retire_before_lifetime_factor"):
        try:
            retire_before_lifetime_factor = config_file.getfloat("global", "retire_before_lifetime_factor")
            if retire_before_lifetime_factor < 1.0:
                print "Please use a float value (1.0, X] for the retire_before_lifetime_factor"
                sys.exit(1)
        except ValueError:
            print "Configuration file problem: retire_before_lifetime_factor must be a " \
                  "float value."
            sys.exit(1)

    if config_file.has_option("global", "getclouds"):
        getclouds = config_file.getboolean("global", "getclouds")
        
    if config_file.has_option("global", "scheduling_metric"):
        scheduling_metric = config_file.get("global", "scheduling_metric")

    if config_file.has_option("global", "job_distribution_type"):
        job_distribution_type = config_file.get("global", "job_distribution_type")

    if config_file.has_option("global", "memory_distribution_weight"):
        try:
            memory_distribution_weight = config_file.getfloat("global", "memory_distribution_weight")
            if ban_failrate_threshold <= 0:
                print "Please use a float value (0, x]"
                sys.exit(1)
        except ValueError:
            print "Configuration file problem: memory_distribution_weight must be an " \
                  "float value."
            sys.exit(1)

    if config_file.has_option("global", "cpu_distribution_weight"):
        try:
            cpu_distribution_weight = config_file.getfloat("global", "cpu_distribution_weight")
            if ban_failrate_threshold <= 0:
                print "Please use a float value (0, x]"
                sys.exit(1)
        except ValueError:
            print "Configuration file problem: cpu_distribution_weight must be an " \
                  "float value."
            sys.exit(1)

    if config_file.has_option("global", "storage_distribution_weight"):
        try:
            storage_distribution_weight = config_file.getfloat("global", "storage_distribution_weight")
            if ban_failrate_threshold <= 0:
                print "Please use a float value (0, x]"
                sys.exit(1)
        except ValueError:
            print "Configuration file problem: storage_distribution_weight must be an " \
                  "float value."
            sys.exit(1)

    if config_file.has_option("global", "scheduling_algorithm"):
        scheduling_algorithm = config_file.get("global", "scheduling_algorithm")

    if config_file.has_option("global", "high_priority_job_support"):
        high_priority_job_support = config_file.getboolean("global", "high_priority_job_support")

    if config_file.has_option("global", "high_priority_job_weight"):
        try:
            high_priority_job_weight = config_file.getint("global", "high_priority_job_weight")
        except ValueError:
            print "Configuration file problem: high_priority_job_weight must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "scheduler_interval"):
        try:
            scheduler_interval = config_file.getint("global", "scheduler_interval")
        except ValueError:
            print "Configuration file problem: scheduler_interval must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "vm_poller_interval"):
        try:
            vm_poller_interval = config_file.getint("global", "vm_poller_interval")
        except ValueError:
            print "Configuration file problem: vm_poller_interval must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "job_poller_interval"):
        try:
            job_poller_interval = config_file.getint("global", "job_poller_interval")
        except ValueError:
            print "Configuration file problem: job_poller_interval must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "machine_poller_interval"):
        try:
            machine_poller_interval = config_file.getint("global", "machine_poller_interval")
        except ValueError:
            print "Configuration file problem: machine_poller_interval must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "cleanup_interval"):
        try:
            cleanup_interval = config_file.getint("global", "cleanup_interval")
        except ValueError:
            print "Configuration file problem: cleanup_interval must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "job_proxy_refresher_interval"):
        try:
            job_proxy_refresher_interval = config_file.getint("global", "job_proxy_refresher_interval")
        except ValueError:
            print "Configuration file problem: job_proxy_refresher_interval must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "job_proxy_renewal_threshold"):
        try:
            job_proxy_renewal_threshold = config_file.getint("global", "job_proxy_renewal_threshold")
        except ValueError:
            print "Configuration file problem: job_proxy_renewal_threshold must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "vm_proxy_refresher_interval"):
        try:
            vm_proxy_refresher_interval = config_file.getint("global", "vm_proxy_refresher_interval")
        except ValueError:
            print "Configuration file problem: vm_proxy_refresher_interval must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "vm_proxy_renewal_threshold"):
        try:
            vm_proxy_renewal_threshold = config_file.getint("global", "vm_proxy_renewal_threshold")
        except ValueError:
            print "Configuration file problem: vm_proxy_renewal_threshold must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "vm_proxy_shutdown_threshold"):
        try:
            vm_proxy_shutdown_threshold = config_file.getint("global", "vm_proxy_shutdown_threshold")
        except ValueError:
            print "Configuration file problem: vm_proxy_shutdown_threshold must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "vm_connection_fail_threshold"):
        try:
            vm_connection_fail_threshold = config_file.getint("global", "vm_connection_fail_threshold")
        except ValueError:
            print "Configuration file problem: vm_connection_fail_threshold must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "vm_idle_threshold"):
        try:
            vm_idle_threshold = config_file.getint("global", "vm_idle_threshold")
        except ValueError:
            print "Configuration file problem: vm_idle_threshold must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("global", "proxy_cache_dir"):
        proxy_cache_dir = config_file.get("global", "proxy_cache_dir")

    if config_file.has_option("global", "myproxy_logon_command"):
        myproxy_logon_command = config_file.get("global", "myproxy_logon_command")

    if config_file.has_option("global", "override_vmtype"):
        override_vmtype = config_file.getboolean("global", "override_vmtype")

    if config_file.has_option("logging", "log_level"):
        log_level = config_file.get("logging", "log_level")

    if config_file.has_option("logging", "log_location"):
        log_location = os.path.expanduser(config_file.get("logging", "log_location"))

    if config_file.has_option("logging", "log_stdout"):
        log_stdout = config_file.getboolean("logging", "log_stdout")

    if config_file.has_option("logging", "log_max_size"):
        try:
            log_max_size = config_file.getint("logging", "log_max_size")
        except ValueError:
            print "Configuration file problem: log_max_size must be an " \
                  "integer value in bytes."
            sys.exit(1)

    if config_file.has_option("logging", "log_format"):
        log_format = config_file.get("logging", "log_format")

    # Default Job options
    if config_file.has_option("job", "default_VMType"):
        default_VMType = config_file.get("job", "default_VMType")

    if config_file.has_option("job", "default_VMNetwork"):
        default_VMNetwork = config_file.get("job", "default_VMNetwork")

    if config_file.has_option("job", "default_VMCPUArch"):
        default_VMCPUArch = config_file.get("job", "default_VMCPUArch")

    if config_file.has_option("job", "default_VMName"):
        default_VMName = config_file.get("job", "default_VMName")

    if config_file.has_option("job", "default_VMLoc"):
        default_VMLoc = config_file.get("job", "default_VMLoc")

    if config_file.has_option("job", "default_VMAMI"):
        default_VMAMI = config_file.get("job", "default_VMAMI")

    if config_file.has_option("job", "default_VMMem"):
        try:
            default_VMMem = config_file.getint("job", "default_VMMem")
        except ValueError:
            print "Configuration file problem: default_VMMem must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("job", "default_VMCPUCores"):
        try:
            default_VMCPUCores = config_file.getint("job", "default_VMCPUCores")
        except ValueError:
            print "Configuration file problem: default_VMCPUCores must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("job", "default_VMStorage"):
        try:
            default_VMStorage = config_file.getint("job", "default_VMStorage")
        except ValueError:
            print "Configuration file problem: default_VMStorage must be an " \
                  "integer value."
            sys.exit(1)

    if config_file.has_option("job", "default_VMInstanceType"):
        default_VMInstanceType = config_file.get("job", "default_VMInstanceType")

    if config_file.has_option("job", "default_VMMaximumPrice"):
        try:
            default_VMMaximumPrice = config_file.getint("job", "default_VMMaximumPrice")
        except ValueError:
            print "Configuration file problem: default_VMMaximumPrice must be an " \
                  "integer value."
            sys.exit(1)

    # Derived options
    if condor_host_on_vm:
        condor_host = condor_host_on_vm
    else:
        condor_host = utilities.get_hostname_from_url(condor_webservice_url)

    if config_file.has_option("global", "use_pyopenssl"):
        use_pyopenssl = config_file.getboolean("global", "use_pyopenssl")
