#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri May  5 16:12:51 2017

@author: yuxin
"""

import boto

from boto.ec2.connection import EC2Connection
from boto.ec2.regioninfo import *
# In[]
region = RegionInfo(name="NeCTAR", endpoint="nova.rc.nectar.org.au")
# In[]
# Team ec2 credentials
ec2_access_key = '88a4f0645d47437fab220333415be1e1'
ec2_secret_key = '3c412674f56446679138a7e73045e1ab'
# In[]
connection = boto.connect_ec2(aws_access_key_id=ec2_access_key,
                    aws_secret_access_key=ec2_secret_key,
                    is_secure=True,
                    region=region,
                    validate_certs=False,
                    port=8773,
                    path="/services/Cloud")
# In[]
reservations = connection.get_all_instances()
print reservations
# In[]
images = connection.get_all_images()
# In[]
for i in range(1,len(images)):
        if images[i].name=="NeCTAR Ubuntu 16.04 LTS (Xenial) amd64":
            ubuntuImage = images[i]
            break
# In[]
instance_size = 'm2.medium'
n = 0
while n < 4:
    instance = connection.run_instances(ubuntuImage.id,key_name='cloud',instance_type=instance_size,security_groups=['ssh','http','default'])
    n += 1
