import os, sys
global project_root
project_root = os.environ.get("MONITOR_HOME")
agent_root = project_root + r"\agent"
if not project_root in sys.path: sys.path.append(project_root)
if not agent_root in sys.path: sys.path.append(agent_root)

if __name__ == "__main__": print project_root