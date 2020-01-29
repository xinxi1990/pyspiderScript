from pyspider.result import ResultWorker
from pyspider.libs.base_handler import *

class MyResultWorker(ResultWorker):




    def on_result(self, task, result):
        print("#################")
        print(task)
        print(result)
        assert task['taskid']
        assert task['project']
        assert task['url']
        assert result
        # your processing code goes here