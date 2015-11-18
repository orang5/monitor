# -*- coding: utf-8 -*-
# display_name: alias for metric.name
names = dict(
    dev_cpu="cpu", 
    dev_mem="mem",
    dev_disk="logical_disk",
    dev_nic="network",
    program_list="installed_programs"
)

names["host_info"] = "host_info"

# metric type routes: describes how to deal with certain metric type
# to which model this metric is saved
type_models = dict(
    config = ["ConfigModel", "CurrentModel"],         # config 
    metric = ["MetricModel", "CurrentModel"],         # metric/perf
    inventory = ["InventoryInfoModel", "CurrentInfoModel"],   # inventory
    current = ["CurrentModel"],   # current/runtime only save in currentmodel
    runtime = ["CurrentModel"],
    # todo
    log = ["LogModel"],
    flow = ["FlowModel"]
)

# model settings. currently only [latest]
# describes how to save into this model
model_conf = dict(
  ConfigModel = {"latest" : False},
  MetricModel = {"latest" : False},
  InventoryInfoModel = {"latest" : False},
  CurrentModel = {"latest" : True},
  CurrentInfoModel = {"latest" : True}
)