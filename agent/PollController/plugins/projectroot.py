import os, sys
# root definition in pollcontroller/plugins
project_root = os.path.abspath(os.path.join(sys.path[0], os.pardir, os.pardir))
if not project_root in sys.path: sys.path.append(project_root)

if __name__ == "__main__": print project_root