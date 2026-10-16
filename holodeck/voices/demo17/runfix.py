import sys, runpy; sys.path.insert(0, '/workspace/grok-tools/holodeck/voices/demo17'); import npfix
p = sys.argv[1]; sys.argv = sys.argv[1:]; runpy.run_path(p, run_name='__main__')
