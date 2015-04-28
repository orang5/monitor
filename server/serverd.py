from web.models import MoniterModel
import logging, threading
def cleaner():
    def func():
        MoniterModel.objects.delete()    
    while True:
        t = threading.Timer(5*60,func)
        t.start()
        t.join()
        
if __name__ == '__main__':
    cleaner()