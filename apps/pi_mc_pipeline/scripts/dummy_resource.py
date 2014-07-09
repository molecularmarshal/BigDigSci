import resources
import os
import uuid
import subprocess

class DummyResource(resources.RemoteResource):
  
  def get_paths(self):
    path_dict = \
      {
       'io_dir':          self.io_dir, 
       'resource_prefix': self.resource_prefix,
      }
    return path_dict

  def get_environ(self):
    d = { "PYTHONPATH": [os.path.join(self.resource_prefix,
                                      'core/scripts')]}
    return d
