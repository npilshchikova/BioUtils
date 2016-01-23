# Copyright (C) 2012 Allis Tauri <allista@gmail.com>
# 
# degen_primer is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# degen_primer is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
Created on Mar 6, 2014

@author: Allis Tauri <allista@gmail.com>
'''
from datetime import timedelta
import errno
from threading import Thread
from time import time, sleep

import traceback as tb

class WaitingThread(Thread):
    '''Thread that specially handle EOFError and IOError 4, interpreting them 
    as a signal that the target activity (which is supposed to run in another 
    process, e.g. in a Manager) has been terminated.'''
    def __init__(self, lock, t_id, target=None, name=None, args=None, kwargs=None):
        Thread.__init__(self, name=name)
        self._lock   = lock
        self._id     = t_id
        self._target = self._timeit(target)
        self._assembler_args   = args if args else ()
        self._kwargs = kwargs if kwargs else dict()
        self.daemon  = True
    #end def
    
    @staticmethod
    def _timeit(func):
        def worker(*args, **kwargs):
            time0 = time()
            func(*args, **kwargs)
            return (time()-time0)
        return worker
    #end def
        
    def _print_exception(self, e):
        with self._lock:
            print '\nError in thread: %s' % self.name
            print e
            tb.print_exc()
    #end def
        
    def run(self):
        elapsed_time = 0
        try: elapsed_time = self._target(*self._assembler_args, **self._kwargs)
        #Ctrl-C
        #EOF means that target activity was terminated in the Manager process
        except (KeyboardInterrupt, EOFError): return
        #IO code=4 means the same
        except IOError, e:
            if e.errno == errno.EINTR: return
            elif e.errno == errno.EBADMSG:
                with self._lock:
                    print '\nError in thread: %s' % self.name
                    print e
                    print '\n*** It seems that an old degen_primer ' \
                    'subprocess is running in the system. Kill it and try again. ***\n'
            else: self._print_exception(e)
        except Exception, e: self._print_exception(e)
        finally:
            #send back a message with elapsed time
            sleep(0.1)
            with self._lock:
                print('\nTask #%d has finished:\n   %s\nElapsed time: %s' % \
                      (self._id, self.name, timedelta(seconds=elapsed_time)))
    #end def
#end class