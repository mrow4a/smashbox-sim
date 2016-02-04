
import smashbox.compatibility.argparse as argparse

def keyval_tuple(x):
   a,b = x.split('=',1)
   return (a.strip(),b)

def arg_parser(**kwds):
    """ Create an ArgumentParser with common options for smash scripts and tools.
    """
    
    parser = argparse.ArgumentParser(**kwds)
    
    parser.add_argument('--option', '-o', metavar="key=val", dest="options", type=keyval_tuple, action='append', help='set config option')
    parser.add_argument('--dry-run', '-n', action='store_true', help='show config options and print what tests would be run')
    parser.add_argument('--quiet', '-q', action="store_true", help='do not produce output (other than errors)')
    parser.add_argument('--verbose', '-v', action="store_true", help='produce more output')
    parser.add_argument('--debug', action="store_true", help='produce very verbose output')
    parser.add_argument('--config','-c',dest="configs",default=[],action="append",help='config files (one or more), added on to of default config file')
    return parser


import os.path
main_config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'etc','smashbox.conf')

class Configuration:
    # you may use config object for string interpolation "..."%config
    def __getitem__(self,x):
        return getattr(self,x)

    def _dict(self,**args):
        return dict(self.__dict__.items() + args.items()) 

    def get(self,x,default):
        logger = getLogger()
        logger.debug('config.get(%s,default=%s)',repr(x),repr(default))
        try:
            return getattr(self,x)
        except AttributeError:
            return default


config = Configuration()

def configure_from_blob(config_blob):
    import pickle
    global config
    config = pickle.loads(config_blob)
    config_log(level=logging.DEBUG)
    return config

def dump_config_to_blob():
    import pickle
    return pickle.dumps(config)
        
def configure(cmdline_opts,config_files=None):
   """ Initialize config object and return it.

   First exec the sequence of config_files (including the
   main_config_file). All symbols defined by these files will be set
   as attributes of the config object.

   Then process cmdline_opts (which is a list of tuples generated by
   arg_parser). If attribute matching the option already exists (was
   defined in a configuration file) then eval to the same type (if not
   None). Otherwise leave string values. The string "None" is special
   and it is always converted to None and may always be assigned.
 
   """

   if config_files is None:
      config_files = []

   logger = getLogger()

   config_files = [main_config_file] + config_files

   for cf in config_files:
      execfile(cf,{},config.__dict__)

   if cmdline_opts:
      for key,val in cmdline_opts:
         try:
            if val == "None":
               val = None
            else:
               attr = getattr(config,key)
               # coerce val type to attr's type unless attr is set to None (then leave as-is <string>)
               try:
                  if attr is not None:
                     val = type(attr)(val)
               except ValueError,x:
                  # allow setting to None
                  logger.warning("cannot set option (type mismatch) %s=%s --> %s",key,repr(val),x)
                  continue
         except AttributeError:
            # if attr unknown then leave the val as-is (string)
            pass

         setattr(config,key,val)

   config_log(level=logging.DEBUG) 
   
   return config

def config_log(level):
   logger = getLogger()
   for d in dir(config):
      if not d.startswith("_") and d != "get":
          logger.log(level,"CONFIG: %s = %s",d,repr(getattr(config,d)))


import logging

logger = None
def getLogger(name="",level=None):
   global logger
   if not logger:
      if level is None:
          level = logging.INFO  # change here to DEBUG if you want to debug config stuff
      logging.basicConfig(level=level)

   return logging.getLogger('.'.join(['smash',name]))