mongo MoniterDB --eval "db.getCollectionNames().forEach(function(n){db[n].remove({})})
pause