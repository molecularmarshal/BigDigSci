from abc import ABCMeta, abstractmethod
import os
import time
import random
import math
import cStringIO
import itertools
import subprocess
import shutil
import time
import generator
from multiprocessing import Process

# Generic Pipeline Class extended from generator bass class to execute a sequence 
# of shell commands and function calls for protein simulator

class Pipeline_generator(generator.Generator):
  __metaclass__ = ABCMeta

  # Application dependent and has to be implemented for each pipeline
  @abstractmethod
  def preprocess(self, input_params):
    raise NotImplementedError( "Should have implemented this" )

  # Application dependent and has to be implemented for each pipeline
  @abstractmethod
  def run_substage(self, output_prefix, param_dict):
    raise NotImplementedError( "Should have implemented this" )

  # Application dependent and has to be implemented for each pipeline
  # since for different user pipelines there may be different number of 
  # parameters, we need to init the params for each object after we call 
  # run method
  @abstractmethod
  def set_params(self, run_dict):
    raise NotImplementedError( "Should have implemented this" )

  # A run wrapper with timeout
  def run(self, output_prefix, run_dict, cmd_dict):
    self.set_params(run_dict)
    self.cmd_dict = cmd_dict

    timeout = None
    try:
      timeout = self.timeout
    except:
      pass

    sleeptime = 5
    p = Process(target=self.run_)
    p.start()
    if not timeout:
      p.join()
      status = 'normal'
    else:
      total_sleep = 0

      while total_sleep < timeout:
        time.sleep(sleeptime)
        total_sleep = total_sleep + sleeptime
        if not p.is_alive():
          p.join()
          status = 'normal'
          break

      if p.is_alive():
        p.terminate()
        status = 'timeout'
      else:
        p.join()
        status = 'normal'

    return status

    

  # Actual Run method:
  #  (1) process template/input files by performing dict substitution using self.param_dict
  #  (2) rsync additional data (copying without substitutions)
  #  (3) run stages where each stage is a list of substages: [(command/operation, input, output)]
  #  (4) upon a substage failure, the execution restarts as the first substage of the stage
  def run_(self):
    # template_prefix = os.path.join(resource_prefix, app_dir, "template")
    self.param_dict['template_prefix'] = os.path.join(self.param_dict['resource_prefix'],
                                                      self.param_dict['app_dir'],
                                                      self.param_dict['template_dir'])

    output_prefix = os.path.join(self.param_dict['resource_prefix'], 
                                 self.param_dict['io_dir'], 
                                 self.param_dict['session_dir'],
                                 self.param_dict['deployment_dir'],
                                 self.param_dict['run_dir'])

    self.param_dict['output_prefix'] = output_prefix

    if not os.path.exists(output_prefix):
      os.makedirs(output_prefix)
    
    # TODO we assume that the templates dir is in the same level of apps/*/scripts
    #for aux_dir in self.param_dict.get('aux_dirs') or []:
    #  cmd = 'rsync -av {0}/{1}/{2} {3}'.format(self.param_dict['template_prefix'], 
    #                                           self.param_dict['template_dir'], 
    #                                           aux_dir, output_prefix)
    #  print cmd
    #  subprocess.Popen(cmd, shell=True, 
    #                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.read()

    # two types of files need to be copied to run_dir
    # 1) aux_fn : keep these unchanged
    # 2) template_fn : applied to dict subsitution 
    # 3) template_fn_list : user defined list contain all template_fn 

    if hasattr(self, 'input_fn_list'):
      for fn in self.input_fn_list:
        s = os.path.join(self.param_dict['template_prefix'], fn)
        t = os.path.join(output_prefix, fn)

        work_dir = os.path.split(t)[0]
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)


        print s, '->', t
        shutil.copy2(s,t)

    if hasattr(self, 'template_fn_list'):
      for fn in self.template_fn_list:
        if fn != None:
          with open(os.path.join(self.param_dict['template_prefix'],
                                 fn), 'r') as ifp:
            template = ifp.read()

            fn = os.path.join(output_prefix, fn)
            work_dir = os.path.split(fn)[0]
            print 'work_dir:', work_dir
            if not os.path.exists(work_dir):
              os.makedirs(work_dir)


            with open(fn, 'w') as ofp:
              ofp.write(template.format(**self.param_dict))

    for stage in self.stage_list:
      move_on = False
      while not move_on:
        for substage in stage:
#
#  Cleaning up old output files
#  this should go inside run_substage because it's app dependent
#
#          out_fns = substage.get('o')
#          in_fn   = substage.get('i') or substage.get('si')
#          if out_fns == None:
#            try:
#              out_fns = [os.path.splitext(in_fn)[0] + self.default_out_ext]
#              substage['o'] = out_fns
#              cmd = 'rm ' + ' '.join(out_fns)
#              print cmd
#              subprocess.Popen(cmd, shell=True, cwd = output_prefix,
#                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.read()
#            except:
#              substage['o'] = None
#         
          success = self.run_substage(output_prefix, substage)
          #success = True
          if success:
            move_on = True
          else:
            move_on = False
            break
    print 'pipleline finished'

    @abstractmethod
    def load(self, conn, d):
      raise NotImplementedError ("Should have implemented this")

    @abstractmethod
    def get_output_fns(self, d):
      raise NotImplementedError ("Should have implemented this")
  
